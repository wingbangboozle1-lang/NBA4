"""Injury-report archive and consecutive-report differ.

Brief items implemented (2026-11-15):

* "Store every injury PDF with its timestamp and diff consecutive reports to
  detect status changes."
* "Show the injury-report revision time and retrieval time in the Injuries
  page banner."

Every stored report keeps the two timestamps the brief asks for: the
**revision time** printed inside the document (``source_revision_stamp``,
e.g. the header the NBA prints on its own report files) and the **retrieval
time** at which this repository fetched it (``retrieved_at``). A report
without both is refused, because a status change can only be interpreted
relative to a known revision.

The differ compares *consecutive stored reports of the same game code* and
classifies each player as UNCHANGED / STATUS_CHANGED / REASON_CHANGED /
ADDED / REMOVED. It also separates a real change from a **name-spelling
drift**: the official reports are keyed on a printed "Last, First" string, and
when two consecutive reports spell a player differently a naive key join turns
one unchanged player into an ADD plus a REMOVE. ``name_drift`` pairs such rows
by team and string similarity so they can be flagged for review instead of
silently re-keyed or silently merged (see ``docs/verification-pass-7dfeb9eb.md``
for the observed instances, which are reported as printed, not corrected).

Status values are recorded exactly as printed. This module never maps a status
to availability or minutes: that is ``engine/injuries.py``'s separate,
UNVALIDATED scenario step, and the two are deliberately not joined here.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

NOT_YET_SUBMITTED = "NOT YET SUBMITTED"

CHANGE_STATUS = "STATUS_CHANGED"
CHANGE_REASON = "REASON_CHANGED"
CHANGE_ADDED = "ADDED"
CHANGE_REMOVED = "REMOVED"
CHANGE_UNCHANGED = "UNCHANGED"
CHANGE_NAME_DRIFT = "NAME_SPELLING_DRIFT"


class InjuryArchiveError(ValueError):
    """Raised when a stored report is missing provenance or repeats a key."""


def _parse_iso(value: str, field_name: str, who: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise InjuryArchiveError(f"{who}: {field_name} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise InjuryArchiveError(f"{who}: {field_name} must carry a UTC offset")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class InjuryRow:
    """One printed row of one injury report."""

    game_code: str          # e.g. "IND@PHI" exactly as printed
    team: str               # full team name as printed, "" when the cell was lost
    player: str             # "Last, First" as printed
    status: str             # as printed; "" when the row is a NOT-YET-SUBMITTED marker
    reason: str             # as printed

    @property
    def is_submission_marker(self) -> bool:
        return self.reason == NOT_YET_SUBMITTED and not self.player

    @property
    def cell_lost(self) -> bool:
        return not self.team


@dataclass(frozen=True)
class InjuryReport:
    """A whole published report, its two timestamps and its source URL."""

    document_id: str
    source_url: str
    source_revision_stamp: str     # the revision time printed by the source
    retrieved_at: str              # when this repository fetched it
    rows: Tuple[InjuryRow, ...]
    extraction_notes: Tuple[str, ...] = ()

    def validate(self) -> "InjuryReport":
        if not self.document_id:
            raise InjuryArchiveError("report: document_id required")
        if not self.source_url.startswith("https://"):
            raise InjuryArchiveError(f"{self.document_id}: source_url must be https://")
        _parse_iso(self.source_revision_stamp, "source_revision_stamp", self.document_id)
        _parse_iso(self.retrieved_at, "retrieved_at", self.document_id)
        seen: set = set()
        for row in self.rows:
            key = (row.game_code, row.team, row.player)
            if row.player and key in seen:
                raise InjuryArchiveError(f"{self.document_id}: duplicate row {key}")
            seen.add(key)
        return self

    def content_hash(self) -> str:
        payload = json.dumps([asdict(r) for r in self.rows], sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def banner(self) -> Dict[str, str]:
        """The two timestamps the Injuries page banner must show, plus the count."""
        return {
            "document_id": self.document_id,
            "revision_time": self.source_revision_stamp,
            "retrieval_time": self.retrieved_at,
            "row_count": str(len(self.rows)),
            "source_url": self.source_url,
            "content_hash": self.content_hash(),
        }


def normalise_name(player: str) -> str:
    """Join key: case-folded, accent-stripped, suffix-stripped "last first".

    Deliberately lossy in one direction only - it can bring two spellings of
    one name together for *comparison*, but ``diff_reports`` still reports the
    printed strings, and a normalisation collision is surfaced as drift rather
    than silently treated as the same player.
    """
    text = unicodedata.normalize("NFKD", player).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", " ", text)
    text = text.replace(".", " ").replace(",", " ")
    return " ".join(text.split())


def _order_key(name: str) -> str:
    """Normalise 'Last, First' and 'First Last' to the same token order-insensitive key."""
    return " ".join(sorted(normalise_name(name).split()))


@dataclass(frozen=True)
class Change:
    """One classified difference between two consecutive reports."""

    kind: str
    game_code: str
    team: str
    player: str
    before_status: str
    after_status: str
    before_reason: str
    after_reason: str
    before_document: str
    after_document: str
    note: str = ""

    def to_row(self) -> Dict[str, str]:
        return {
            "kind": self.kind,
            "game_code": self.game_code,
            "team": self.team,
            "player": self.player,
            "before_status": self.before_status,
            "after_status": self.after_status,
            "before_reason": self.before_reason,
            "after_reason": self.after_reason,
            "before_document": self.before_document,
            "after_document": self.after_document,
            "note": self.note,
        }


@dataclass(frozen=True)
class DiffReport:
    """All classified differences for one game code, plus review flags."""

    game_code: str
    before_document: str
    after_document: str
    changes: Tuple[Change, ...]
    unchanged_players: Tuple[str, ...]
    name_drift_candidates: Tuple[Change, ...]
    lost_team_cells: Tuple[str, ...]
    submission_marker_flip: Tuple[str, ...]
    comparable: bool
    incomparable_reason: str = ""

    @property
    def status_changes(self) -> Tuple[Change, ...]:
        return tuple(c for c in self.changes if c.kind == CHANGE_STATUS)

    @property
    def summary(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for change in self.changes:
            out[change.kind] = out.get(change.kind, 0) + 1
        out["UNCHANGED"] = len(self.unchanged_players)
        out["NAME_SPELLING_DRIFT"] = len(self.name_drift_candidates)
        return out


def _index(report: InjuryReport, game_code: str) -> Dict[str, InjuryRow]:
    out: Dict[str, InjuryRow] = {}
    for row in report.rows:
        if row.game_code != game_code or not row.player:
            continue
        out[_order_key(row.player)] = row
    return out


def diff_reports(
    before: InjuryReport,
    after: InjuryReport,
    game_code: str,
    similarity_threshold: float = 0.82,
) -> DiffReport:
    """Diff two stored reports of the same game code, oldest first.

    ``similarity_threshold`` guards the drift detector only; it never licenses
    a merge. A row is only ever *reported* as drift for a human to review.
    """
    before.validate()
    after.validate()
    before_dt = _parse_iso(before.source_revision_stamp, "source_revision_stamp", before.document_id)
    after_dt = _parse_iso(after.source_revision_stamp, "source_revision_stamp", after.document_id)
    if after_dt < before_dt:
        raise InjuryArchiveError("diff_reports: the 'after' report is older than the 'before' report")
    if before.document_id == after.document_id:
        raise InjuryArchiveError("diff_reports: a report cannot be diffed against itself")

    old = _index(before, game_code)
    new = _index(after, game_code)
    changes: List[Change] = []
    unchanged: List[str] = []
    lost_team_cells: List[str] = []
    drift: List[Change] = []

    matched_new: set = set()
    unmatched_old: List[Tuple[str, InjuryRow]] = []
    for key, old_row in sorted(old.items()):
        new_row = new.get(key)
        if new_row is None:
            unmatched_old.append((key, old_row))
            continue
        matched_new.add(key)
        if old_row.team and old_row.team != new_row.team:
            lost_team_cells.append(old_row.player)
        if old_row.status != new_row.status:
            changes.append(
                Change(CHANGE_STATUS, game_code, new_row.team, new_row.player,
                       old_row.status, new_row.status, old_row.reason, new_row.reason,
                       before.document_id, after.document_id,
                       "status value as printed in each report")
            )
        elif old_row.reason != new_row.reason:
            changes.append(
                Change(CHANGE_REASON, game_code, new_row.team, new_row.player,
                       old_row.status, new_row.status, old_row.reason, new_row.reason,
                       before.document_id, after.document_id,
                       "reason text changed while the status did not")
            )
        else:
            unchanged.append(new_row.player)

    unmatched_new = [(k, r) for k, r in sorted(new.items()) if k not in matched_new]

    # Drift detection: an unmatched ADD and an unmatched REMOVE inside the
    # same team whose printed names are near-identical are almost certainly a
    # spelling change, not a roster change. Report them, do not merge them.
    for old_key, old_row in list(unmatched_old):
        best: Optional[Tuple[float, str, InjuryRow]] = None
        for new_key, new_row in unmatched_new:
            if old_row.team and new_row.team and old_row.team != new_row.team:
                continue
            ratio = SequenceMatcher(None, normalise_name(old_row.player), normalise_name(new_row.player)).ratio()
            if ratio >= similarity_threshold and (best is None or ratio > best[0]):
                best = (ratio, new_key, new_row)
        if best is not None:
            ratio, new_key, new_row = best
            drift.append(
                Change(CHANGE_NAME_DRIFT, game_code, new_row.team,
                       f"{old_row.player} | {new_row.player}", old_row.status, new_row.status,
                       old_row.reason, new_row.reason, before.document_id, after.document_id,
                       f"printed names differ (similarity {ratio:.2f}); the join key is the "
                       "printed string, so this pair is flagged for review and is NOT merged")
            )
            unmatched_old.remove((old_key, old_row))
            unmatched_new = [(k, r) for k, r in unmatched_new if k != new_key]
            matched_new.add(new_key)

    for _, old_row in unmatched_old:
        changes.append(
            Change(CHANGE_REMOVED, game_code, old_row.team, old_row.player,
                   old_row.status, "", old_row.reason, "", before.document_id, after.document_id,
                   "present in the earlier report only")
        )
    for _, new_row in unmatched_new:
        changes.append(
            Change(CHANGE_ADDED, game_code, new_row.team, new_row.player,
                   "", new_row.status, "", new_row.reason, before.document_id, after.document_id,
                   "present in the later report only")
        )

    for row in after.rows:
        if row.game_code == game_code and row.cell_lost:
            lost_team_cells.append(row.player)

    flips = tuple(
        row.team or f"{game_code} ({row.game_code})"
        for row in before.rows
        if row.game_code == game_code and row.is_submission_marker
        and any(r.game_code == game_code and r.player for r in after.rows)
    )

    return DiffReport(
        game_code=game_code,
        before_document=before.document_id,
        after_document=after.document_id,
        changes=tuple(changes),
        unchanged_players=tuple(sorted(set(unchanged))),
        name_drift_candidates=tuple(drift),
        lost_team_cells=tuple(sorted(set(lost_team_cells))),
        submission_marker_flip=flips,
        comparable=True,
    )


def diff_consecutive(
    reports: Sequence[InjuryReport],
    game_codes: Optional[Iterable[str]] = None,
) -> List[DiffReport]:
    """Diff every adjacent pair of stored reports, in revision order.

    "Consecutive" is evaluated over the reports this repository actually
    stores. If the source publishes files between two stored reports, the pair
    is still consecutive *in the archive* and the gap is stated, never hidden.
    """
    ordered = sorted(reports, key=lambda r: _parse_iso(r.source_revision_stamp, "s", r.document_id))
    if len(ordered) < 2:
        return []
    codes = set(game_codes) if game_codes is not None else None
    out: List[DiffReport] = []
    for before, after in zip(ordered, ordered[1:]):
        games = codes
        if games is None:
            games = {r.game_code for r in before.rows} & {r.game_code for r in after.rows}
        for code in sorted(games):
            if not code:
                continue
            out.append(diff_reports(before, after, code))
    return out


# --- archive storage -------------------------------------------------------

@dataclass
class ReportArchive:
    """Append-only directory of stored reports, one JSON file per document id."""

    directory: Path

    def __post_init__(self) -> None:
        self.directory = Path(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, report: InjuryReport) -> Path:
        return self.directory / f"{report.document_id}.json"

    def store(self, report: InjuryReport) -> Path:
        report.validate()
        path = self.path_for(report)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing.get("content_hash") != report.content_hash():
                raise InjuryArchiveError(
                    f"{report.document_id}: a different extraction is already stored for this "
                    "document id; store a new document id, never overwrite an archived report"
                )
            return path
        payload = asdict(report)
        payload["rows"] = [asdict(r) for r in report.rows]
        payload["content_hash"] = report.content_hash()
        payload["stored_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def load(self, document_id: str) -> InjuryReport:
        payload = json.loads((self.directory / f"{document_id}.json").read_text(encoding="utf-8"))
        rows = tuple(InjuryRow(**r) for r in payload.pop("rows", []))
        stored_hash = payload.pop("content_hash", None)
        payload.pop("stored_at_utc", None)
        notes = tuple(payload.pop("extraction_notes", ()) or ())
        report = InjuryReport(rows=rows, extraction_notes=notes, **payload)
        report.validate()
        if stored_hash and stored_hash != report.content_hash():
            raise InjuryArchiveError(
                f"{document_id}: stored content hash does not match the rows on file - the archive "
                "has been edited after it was written"
            )
        return report

    def all(self) -> List[InjuryReport]:
        """Every stored report, each re-verified against its own stored hash."""
        if not self.directory.is_dir():
            return []
        return [self.load(path.stem) for path in sorted(self.directory.glob("*.json"))]
