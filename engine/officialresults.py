"""Official per-game result feed: one row per game, settled only after finals verify.

Brief item implemented (2026-11-15): "Keep an official per-game result feed
current and settle only after final scores are verified; store one row per
game: date, teams, final score, quarter scores."

Design rules, in order of enforcement:

* **One row per game.** ``ResultStore`` keys on ``game_id``. A second
  observation of the same game either agrees (it is stored as corroboration,
  which is what makes a score *verified*) or conflicts, which raises
  ``ResultConflict`` and is never silently overwritten. A settled (verified
  final) row is immutable.
* **Internal consistency.** Quarter scores must sum to the final score for
  each team. A row whose quarter column does not add up is not publishable
  and can never be settled.
* **Verification is a pair, not a claim.** ``verify_final`` requires two
  independent official observations of the same game whose final scores and
  quarter scores agree. One observation is "reported", two are "verified".
  This mirrors the ledger rule in ``engine/schema.py`` (provenance is
  mandatory) and extends it with corroboration.
* **Freshness gate before rebuild.** ``refresh_gate`` answers "may the model
  be rebuilt from this feed?" It passes only when the feed is fresh (a
  declared maximum age), every game day in the requested window is either
  settled or explicitly marked as having no games, and no row is pending
  verification.

No value in this module has a default. A caller must supply the official
document, its revision timestamp and the retrieval timestamp; the module
refuses to invent any of them, and it never contains NBA data itself.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

QUARTER_LABELS: Tuple[str, ...] = ("Q1", "Q2", "Q3", "Q4")
OVERTIME_LABELS: Tuple[str, ...] = ("OT1", "OT2", "OT3", "OT4", "OT5")

FINALITY_FINAL = "FINAL"
FINALITY_FINAL_OT = "FINAL/OT"
FINALITY_IN_PROGRESS = "IN PROGRESS"
FINALITY_PREVIEW = "PREVIEW"
FINALITY_POSTPONED = "POSTPONED"
VALID_FINALITY = (
    FINALITY_FINAL,
    FINALITY_FINAL_OT,
    FINALITY_POSTPONED,
    FINALITY_IN_PROGRESS,
    FINALITY_PREVIEW,
)


class ResultError(ValueError):
    """Raised when a result row violates the feed's integrity rules."""


def _parse_iso(value: str, field_name: str, record_id: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ResultError(f"{record_id}: {field_name} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ResultError(f"{record_id}: {field_name} must carry a UTC offset: {value!r}")
    return parsed.astimezone(timezone.utc)


def _require_https(url: str, field_name: str, record_id: str) -> str:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ResultError(f"{record_id}: {field_name} must be an https:// official source URL")
    return url


@dataclass(frozen=True)
class QuarterScore:
    """One period's score for both teams, exactly as the official source prints it."""

    label: str
    away: Optional[float]
    home: Optional[float]

    def validated(self, record_id: str) -> "QuarterScore":
        if self.label not in QUARTER_LABELS + OVERTIME_LABELS:
            raise ResultError(f"{record_id}: unknown period label {self.label!r}")
        if self.label.startswith("Q") and (self.away is None or self.home is None):
            raise ResultError(f"{record_id}: {self.label} needs both scores")
        return self


@dataclass(frozen=True)
class ResultObservation:
    """One official document's statement of one game's result."""

    game_id: str
    game_date: str                       # ISO date, as printed by the source
    away_team: str
    home_team: str
    away_score: Optional[float]
    home_score: Optional[float]
    quarter_scores: Tuple[QuarterScore, ...]
    finality: str
    source_url: str                      # official document
    source_revision_stamp: str           # the revision time the document prints
    retrieved_at: str                    # when we fetched it (ISO with offset)

    @property
    def record_id(self) -> str:
        return f"{self.game_id}@{self.source_revision_stamp}"

    def content_hash(self) -> str:
        payload = json.dumps(
            {
                "game_id": self.game_id,
                "game_date": self.game_date,
                "away_team": self.away_team,
                "home_team": self.home_team,
                "away_score": self.away_score,
                "home_score": self.home_score,
                "quarters": [[q.label, q.away, q.home] for q in self.quarter_scores],
                "finality": self.finality,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def validate(self) -> "ResultObservation":
        if not self.game_id:
            raise ResultError("observation: game_id required")
        datetime.strptime(self.game_date, "%Y-%m-%d")  # raises on anything else
        if not self.away_team or not self.home_team:
            raise ResultError(f"{self.record_id}: away_team/home_team required")
        if self.finality not in VALID_FINALITY:
            raise ResultError(f"{self.record_id}: finality {self.finality!r} not in {VALID_FINALITY}")
        for quarter in self.quarter_scores:
            quarter.validated(self.record_id)
        _require_https(self.source_url, "source_url", self.record_id)
        _parse_iso(self.source_revision_stamp, "source_revision_stamp", self.record_id)
        _parse_iso(self.retrieved_at, "retrieved_at", self.record_id)
        return self

    def quarters_sum_to_final(self) -> bool:
        if self.away_score is None or self.home_score is None:
            return False
        away = sum(q.away or 0.0 for q in self.quarter_scores)
        home = sum(q.home or 0.0 for q in self.quarter_scores)
        return away == self.away_score and home == self.home_score


@dataclass(frozen=True)
class VerificationVerdict:
    """Outcome of the two-observation corroboration test."""

    game_id: str
    verified: bool
    code: str
    detail: str

    @property
    def flag(self) -> str:
        return "VERIFIED" if self.verified else f"UNVERIFIED:{self.code}"


def verify_final(observations: Sequence[ResultObservation]) -> VerificationVerdict:
    """Settle-ready only when two independent official documents agree exactly.

    Independent means a different document id (different source URL or a
    different printed revision stamp), so two copies of one file never count.
    """
    if not observations:
        return VerificationVerdict("", False, "NO_OBSERVATION", "no official result observation stored")
    game_ids = {obs.game_id for obs in observations}
    if len(game_ids) != 1:
        raise ResultError("verify_final: observations mix game ids")
    game_id = observations[0].game_id
    for obs in observations:
        obs.validate()
        if obs.finality not in (FINALITY_FINAL, FINALITY_FINAL_OT):
            return VerificationVerdict(
                game_id, False, "NOT_FINAL",
                f"{obs.source_revision_stamp} prints finality {obs.finality!r}",
            )
        if not obs.quarters_sum_to_final():
            return VerificationVerdict(
                game_id, False, "QUARTERS_DO_NOT_SUM",
                "quarter scores do not add to the printed final score",
            )
    distinct = {obs.content_hash(): obs for obs in observations}
    if len(distinct) > 1:
        return VerificationVerdict(
            game_id, False, "SOURCES_DISAGREE",
            "the official observations do not state the same score",
        )
    if len({(obs.source_url, obs.source_revision_stamp) for obs in observations}) < 2:
        return VerificationVerdict(
            game_id, False, "SINGLE_SOURCE",
            "one official document only; a second independent official "
            "observation is required before settlement",
        )
    return VerificationVerdict(
        game_id, True, "MATCH",
        f"{len(distinct)} official observations agree on final and quarter scores",
    )


@dataclass
class FeedRow:
    """The stored row for one game: the single canonical row plus its corroboration."""

    game_id: str
    observations: List[ResultObservation] = field(default_factory=list)
    settled: bool = False
    settlement_stamp: Optional[str] = None

    @property
    def primary(self) -> ResultObservation:
        return self.observations[0]

    def merged(self) -> Dict[str, object]:
        """The one-row-per-game view the site publishes."""
        obs = self.primary
        by_label: Dict[str, QuarterScore] = {}
        for quarter in obs.quarter_scores:
            by_label[quarter.label] = quarter
        return {
            "game_id": obs.game_id,
            "game_date": obs.game_date,
            "away_team": obs.away_team,
            "home_team": obs.home_team,
            "away_score": obs.away_score,
            "home_score": obs.home_score,
            "quarters": [(label, by_label[label].away, by_label[label].home) for label in by_label],
            "finality": obs.finality,
            "source_url": obs.source_url,
            "source_revision_stamp": obs.source_revision_stamp,
            "retrieved_at": obs.retrieved_at,
            "observation_count": len({(o.source_url, o.source_revision_stamp) for o in self.observations}),
            "verified": bool(self.settled),
            "settlement_stamp": self.settlement_stamp,
        }


class ResultStore:
    """One row per game, append-observations semantics, finals immutable."""

    def __init__(self) -> None:
        self.rows: Dict[str, FeedRow] = {}
        self.rejected: List[Tuple[str, str]] = []

    def upsert(self, observation: ResultObservation) -> str:
        try:
            observation.validate()
        except ResultError as exc:
            self.rejected.append((observation.game_id or "?", str(exc)))
            return "REJECTED"
        row = self.rows.get(observation.game_id)
        if row is None:
            self.rows[observation.game_id] = FeedRow(observation.game_id, [observation])
            return "INSERTED"
        if row.settled:
            if row.primary.content_hash() == observation.content_hash():
                return "IGNORED_DUPLICATE_OF_SETTLED"
            raise ResultConflict(
                f"{observation.game_id}: a settled row cannot be revised; a "
                "conflicting final score is an irregularity for review, not an overwrite"
            )
        for existing in row.observations:
            if (existing.source_url, existing.source_revision_stamp) == (
                observation.source_url,
                observation.source_revision_stamp,
            ):
                if existing.content_hash() != observation.content_hash():
                    raise ResultConflict(
                        f"{observation.game_id}: the same document revision states two scores"
                    )
                return "IGNORED_DUPLICATE"
        # A conflicting score for an unsettled game is kept as corroboration
        # evidence; verify_final() is what refuses to settle it.
        row.observations.append(observation)
        return "CORROBORATED" if observation.content_hash() == row.primary.content_hash() else "CONFLICT_RECORDED"

    def verdict(self, game_id: str) -> VerificationVerdict:
        row = self.rows.get(game_id)
        if row is None:
            return VerificationVerdict(game_id, False, "MISSING_ROW", "no row stored for this game")
        return verify_final(row.observations)

    def game_days(self) -> List[str]:
        return sorted({row.primary.game_date for row in self.rows.values()})

    def to_records(self) -> List[dict]:
        return [self.rows[gid].merged() for gid in sorted(self.rows)]


class ResultConflict(ResultError):
    """Raised when a stored, already-settled row would have to be rewritten."""


@dataclass(frozen=True)
class RefreshGate:
    """The freshness + provenance gate that must pass before a model rebuild."""

    passed: bool
    code: str
    detail: str
    stale_rows: Tuple[str, ...] = ()
    unverified_rows: Tuple[str, ...] = ()


def refresh_gate(
    store: ResultStore,
    requested_game_days: Sequence[str],
    now: str,
    max_age_hours: Optional[float],
) -> RefreshGate:
    """Gate the rebuild on freshness and provenance, never on optimism.

    ``max_age_hours`` must be declared by the caller; passing ``None`` means
    "no freshness policy has been registered" and blocks the rebuild, because
    an undeclared window cannot be audited afterwards.
    """
    now_dt = _parse_iso(now, "now", "refresh_gate")
    if max_age_hours is None:
        return RefreshGate(False, "FRESHNESS_POLICY_UNSET",
                           "no maximum feed age is registered; refuse to rebuild")
    stale: List[str] = []
    unverified: List[str] = []
    for game_id, row in store.rows.items():
        age_hours = (now_dt - _parse_iso(row.primary.retrieved_at, "retrieved_at", game_id)).total_seconds() / 3600.0
        if age_hours > max_age_hours:
            stale.append(game_id)
        if not verify_final(row.observations).verified:
            unverified.append(game_id)
    missing = [day for day in requested_game_days if day not in store.game_days()]
    if missing:
        return RefreshGate(
            False, "FEED_INCOMPLETE",
            "no rows for game day(s): " + ", ".join(missing) + " (a missing day is not a no-games day)",
            tuple(sorted(stale)), tuple(sorted(unverified)),
        )
    if stale:
        return RefreshGate(
            False, "FEED_STALE",
            f"{len(stale)} row(s) older than the declared {max_age_hours}h window",
            tuple(sorted(stale)), tuple(sorted(unverified)),
        )
    return RefreshGate(
        True, "FEED_FRESH_PROVENANCE_OK",
        "every requested game day is present, in-window and carries an https official source; "
        f"{len(unverified)} game(s) still await a second official observation and cannot be settled",
        (), tuple(sorted(unverified)),
    )


def settle_row(store: ResultStore, game_id: str, settled_at: str) -> FeedRow:
    """Freeze a row as settled; the only path that may set ``settled=True``."""
    row = store.rows.get(game_id)
    if row is None:
        raise ResultError(f"{game_id}: nothing stored, nothing to settle")
    verdict = verify_final(row.observations)
    if not verdict.verified:
        raise ResultError(f"{game_id}: settlement refused ({verdict.code}: {verdict.detail})")
    _parse_iso(settled_at, "settled_at", game_id)
    row.settled = True
    row.settlement_stamp = settled_at
    return row


def expected_margin_from_result(row: FeedRow) -> Optional[float]:
    """Home minus away, only from a settled row (used by rest/valuation code)."""
    if not row.settled:
        return None
    obs = row.primary
    if obs.home_score is None or obs.away_score is None:
        return None
    return obs.home_score - obs.away_score


def summarise(store: ResultStore) -> dict:
    rows = list(store.rows.values())
    return {
        "games": len(rows),
        "settled": sum(1 for r in rows if r.settled),
        "awaiting_corroboration": sum(1 for r in rows if not r.settled),
        "rejected": len(store.rejected),
        "game_days": store.game_days(),
    }
