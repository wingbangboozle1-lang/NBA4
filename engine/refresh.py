"""The scheduled-job refresh gate for one rolling slate.

Brief item implemented (2026-11-16): "Extend the scheduled job to refresh the
official schedule, standings, team statistics and injury report for each rolling
slate, then rebuild only after freshness and provenance gates pass."

The job this module governs is the daily cycle described in
``docs/automation.md``. The order matters and is the whole point of the item:
**refresh first, rebuild second, and only if the refresh cleared its gates.**
A rebuild run on a stale injury report is worse than no rebuild, because it
produces a number that looks current.

What a "gate" means here, mechanically:

* **Provenance.** Each feed must name the official document it came from, the
  timestamp that document prints for itself (when it prints one) and the time
  it was retrieved. A feed with no URL is not a feed.
* **Freshness.** Age is measured from the **document's own timestamp** when the
  document prints one, because that is when the information became true;
  retrieval time is the weaker fallback and is labelled as such. The fallback
  never silently upgrades to "fresh".
* **Completeness.** A feed that reports how many rows it carries must carry all
  of them. This is the same rule :mod:`engine.teamstats` enforces on the three
  team-stat pages, applied to every feed.
* **Rights.** ``allowed_use`` is the operator's declared permission flag. The
  gate refuses a feed that is not cleared rather than letting an uncleared feed
  quietly become a model input.

This module **never fetches**. It is the decision layer that a fetcher reports
into, so a scheduled run can be replayed and audited from its observation
record alone.

Nothing here holds NBA data, and nothing here defaults a value that should come
from a document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "RefreshError",
    "FeedState",
    "FeedSpec",
    "FeedObservation",
    "FeedVerdict",
    "SlateWindow",
    "RefreshDecision",
    "DEFAULT_HORIZON_HOURS",
    "rolling_window",
    "evaluate",
    "refresh_decision",
    "default_feed_specs",
]

DEFAULT_HORIZON_HOURS = 72
"""The requested maximum forecast horizon: three days."""

SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
STANDINGS_URL = "https://www.nba.com/standings"
TEAM_STATS_URLS = (
    "https://www.nba.com/stats/teams/traditional",
    "https://www.nba.com/stats/teams/opponent",
    "https://www.nba.com/stats/teams/advanced",
)
INJURY_INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
RESULTS_URL = "https://www.nba.com/games"

#: The official schedule PDF prints its own "as of" line; the NBA.com stats and
#: standings pages print no revision stamp, so for those the retrieval time is
#: the only timestamp available and is recorded as the weaker basis.
NO_REVISION_STAMP = (
    "the document prints no revision stamp; only the retrieval time is available"
)


class RefreshError(ValueError):
    """Raised when a feed declaration or observation is malformed."""


class FeedState(str, Enum):
    """The outcome of one feed's gate."""

    PASS = "PASS"
    NOT_RETRIEVED = "NOT_RETRIEVED"
    STALE_DOCUMENT = "STALE_DOCUMENT"
    STALE_RETRIEVAL = "STALE_RETRIEVAL"
    NO_DOCUMENT_TIMESTAMP = "NO_DOCUMENT_TIMESTAMP"
    INCOMPLETE_ROWS = "INCOMPLETE_ROWS"
    INCOMPLETE_CHUNKS = "INCOMPLETE_CHUNKS"
    RIGHTS_NOT_CLEARED = "RIGHTS_NOT_CLEARED"
    RETRIEVED_BEFORE_PUBLISHED = "RETRIEVED_BEFORE_PUBLISHED"
    URL_MISMATCH = "URL_MISMATCH"


BLOCKING_STATES = frozenset(
    {
        FeedState.NOT_RETRIEVED,
        FeedState.STALE_DOCUMENT,
        FeedState.STALE_RETRIEVAL,
        FeedState.NO_DOCUMENT_TIMESTAMP,
        FeedState.INCOMPLETE_ROWS,
        FeedState.INCOMPLETE_CHUNKS,
        FeedState.RIGHTS_NOT_CLEARED,
        FeedState.RETRIEVED_BEFORE_PUBLISHED,
        FeedState.URL_MISMATCH,
    }
)


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise RefreshError(f"{field_name} must be timezone aware")
    return value.astimezone(timezone.utc)


def _https(url: str, field_name: str) -> str:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RefreshError(f"{field_name} must be an https URL, got {url!r}")
    return url


@dataclass(frozen=True)
class FeedSpec:
    """What the scheduled job is required to refresh. A declaration, not a result."""

    feed_id: str
    label: str
    url: str
    required: bool = True
    max_age_minutes: int = 90
    requires_document_timestamp: bool = False
    expected_rows: Optional[int] = None
    expected_chunks: Optional[int] = None
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.feed_id or not self.label:
            raise RefreshError("a feed spec requires feed_id and label")
        _https(self.url, f"{self.feed_id}.url")
        if self.max_age_minutes <= 0:
            raise RefreshError(f"{self.feed_id}: max_age_minutes must be positive")
        if self.expected_rows is not None and self.expected_rows <= 0:
            raise RefreshError(f"{self.feed_id}: expected_rows must be positive when set")
        if self.expected_chunks is not None and self.expected_chunks <= 0:
            raise RefreshError(f"{self.feed_id}: expected_chunks must be positive when set")


@dataclass(frozen=True)
class FeedObservation:
    """What the fetcher actually retrieved, for one declared feed."""

    feed_id: str
    url: str
    retrieved_at: datetime
    document_timestamp: Optional[datetime] = None
    rows_read: Optional[int] = None
    chunks_read: Optional[int] = None
    allowed_use: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        if not self.feed_id:
            raise RefreshError("an observation requires feed_id")
        _https(self.url, f"{self.feed_id}.url")
        _utc(self.retrieved_at, f"{self.feed_id}.retrieved_at")
        if self.document_timestamp is not None:
            _utc(self.document_timestamp, f"{self.feed_id}.document_timestamp")
        for name in ("rows_read", "chunks_read"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise RefreshError(f"{self.feed_id}: {name} cannot be negative")


@dataclass(frozen=True)
class FeedVerdict:
    """One feed's gate outcome, with the numbers that produced it."""

    feed_id: str
    label: str
    url: str
    state: FeedState
    detail: str
    required: bool
    age_minutes: Optional[float]
    age_basis: str
    blocking: bool

    def as_row(self) -> Dict[str, object]:
        return {
            "feed": self.feed_id,
            "label": self.label,
            "state": self.state.value,
            "required": self.required,
            "blocking": self.blocking,
            "age_minutes": None if self.age_minutes is None else round(self.age_minutes, 1),
            "age_basis": self.age_basis,
            "detail": self.detail,
            "source": self.url,
        }


@dataclass(frozen=True)
class SlateWindow:
    """The rolling window the slate is selected over."""

    start: datetime
    end: datetime
    horizon_hours: int

    def as_dict(self) -> Dict[str, object]:
        return {
            "start_utc": self.start.isoformat(),
            "end_utc": self.end.isoformat(),
            "horizon_hours": self.horizon_hours,
        }


@dataclass(frozen=True)
class RefreshDecision:
    """The gate's answer: may the rebuild run, and why or why not."""

    window: SlateWindow
    verdicts: Tuple[FeedVerdict, ...]
    may_rebuild: bool
    blocking_reasons: Tuple[str, ...]
    warnings: Tuple[str, ...]
    decided_at: datetime

    def as_dict(self) -> Dict[str, object]:
        return {
            "window": self.window.as_dict(),
            "may_rebuild": self.may_rebuild,
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
            "decided_at": self.decided_at.isoformat(),
            "feeds": [verdict.as_row() for verdict in self.verdicts],
        }

    def summary(self) -> Dict[str, object]:
        return {
            "window": f"{self.window.start.isoformat()} .. {self.window.end.isoformat()}",
            "feeds_checked": len(self.verdicts),
            "feeds_passed": sum(1 for v in self.verdicts if v.state is FeedState.PASS),
            "may_rebuild": self.may_rebuild,
            "blocking": list(self.blocking_reasons),
        }


def rolling_window(
    now_utc: datetime,
    horizon_hours: int = DEFAULT_HORIZON_HOURS,
) -> SlateWindow:
    """The rolling window that starts now and ends at the horizon.

    The horizon is capped at three days because that is the requested maximum;
    a longer window is a different product, not a bigger slate.
    """
    if horizon_hours <= 0 or horizon_hours > DEFAULT_HORIZON_HOURS:
        raise RefreshError(
            f"horizon must be within 1..{DEFAULT_HORIZON_HOURS} hours "
            "(the requested maximum is three days)"
        )
    now = _utc(now_utc, "now_utc")
    return SlateWindow(start=now, end=now + timedelta(hours=horizon_hours), horizon_hours=horizon_hours)


def evaluate(spec: FeedSpec, observation: Optional[FeedObservation], now_utc: datetime) -> FeedVerdict:
    """Gate one feed against its declaration.

    A missing observation is ``NOT_RETRIEVED`` — the scheduled job is asked to
    refresh these feeds, so "we have nothing" is a failure of the refresh, not
    a neutral state.
    """
    now = _utc(now_utc, "now_utc")

    def verdict(state: FeedState, detail: str, age=None, basis: str = "none") -> FeedVerdict:
        return FeedVerdict(
            feed_id=spec.feed_id,
            label=spec.label,
            url=spec.url,
            state=state,
            detail=detail,
            required=spec.required,
            age_minutes=age,
            age_basis=basis,
            blocking=(state in BLOCKING_STATES) and spec.required,
        )

    if observation is None:
        return verdict(
            FeedState.NOT_RETRIEVED,
            "no observation was recorded for this feed; the refresh did not run or did not "
            "report, and a missing feed is not treated as an empty feed",
        )
    if observation.url != spec.url:
        return verdict(
            FeedState.URL_MISMATCH,
            f"observed from {observation.url} but the declared official document is {spec.url}; "
            "a feed is identified by its document",
        )
    if observation.document_timestamp is not None and observation.retrieved_at < observation.document_timestamp:
        return verdict(
            FeedState.RETRIEVED_BEFORE_PUBLISHED,
            f"retrieved {observation.retrieved_at.isoformat()} before the document's own "
            f"timestamp {observation.document_timestamp.isoformat()}; the provenance chain is "
            "impossible and is refused rather than repaired",
        )
    if not observation.allowed_use:
        return verdict(
            FeedState.RIGHTS_NOT_CLEARED,
            "the observation's permission flag is not set; rights gate G0 "
            "(NBA Terms of Use sections 1 and 9) blocks the use of this feed",
        )

    # Freshness. The document's own timestamp is the strong basis.
    if observation.document_timestamp is not None:
        age_minutes = (now - observation.document_timestamp).total_seconds() / 60.0
        basis = "document timestamp"
        state = FeedState.STALE_DOCUMENT
    else:
        age_minutes = (now - observation.retrieved_at).total_seconds() / 60.0
        basis = "retrieval time (no document stamp)"
        state = FeedState.STALE_RETRIEVAL

    if spec.requires_document_timestamp and observation.document_timestamp is None:
        return verdict(
            FeedState.NO_DOCUMENT_TIMESTAMP,
            "this feed's document prints its own revision time and the declaration requires "
            "it; the retrieval time is not a substitute for when the document became true",
            age_minutes,
            basis,
        )
    if age_minutes > spec.max_age_minutes:
        return verdict(
            state,
            f"{age_minutes:.1f} min old by {basis}, over the declared tolerance of "
            f"{spec.max_age_minutes} min; the slate is rebuilt from a fresh copy or not at all",
            age_minutes,
            basis,
        )

    if spec.expected_rows is not None:
        if observation.rows_read is None:
            return verdict(
                FeedState.INCOMPLETE_ROWS,
                f"the declaration expects {spec.expected_rows} rows and the observation does not "
                "report how many were read; an unreported count is not a complete read",
                age_minutes,
                basis,
            )
        if observation.rows_read < spec.expected_rows:
            return verdict(
                FeedState.INCOMPLETE_ROWS,
                f"{observation.rows_read} of {spec.expected_rows} rows read; a partial league is "
                "not a league and no row is inferred",
                age_minutes,
                basis,
            )
    if spec.expected_chunks is not None:
        if observation.chunks_read is None:
            return verdict(
                FeedState.INCOMPLETE_CHUNKS,
                f"the declaration expects {spec.expected_chunks} chunks and the observation does "
                "not report how many were read",
                age_minutes,
                basis,
            )
        if observation.chunks_read < spec.expected_chunks:
            return verdict(
                FeedState.INCOMPLETE_CHUNKS,
                f"{observation.chunks_read} of {spec.expected_chunks} chunks read; the document "
                "was read in part",
                age_minutes,
                basis,
            )

    return verdict(
        FeedState.PASS,
        f"{age_minutes:.1f} min old by {basis}, within the {spec.max_age_minutes} min tolerance"
        + (f"; {observation.note}" if observation.note else ""),
        age_minutes,
        basis,
    )


def refresh_decision(
    specs: Sequence[FeedSpec],
    observations: Mapping[str, FeedObservation],
    now_utc: datetime,
    horizon_hours: int = DEFAULT_HORIZON_HOURS,
) -> RefreshDecision:
    """Gate every feed for one rolling window and answer "may we rebuild?".

    Optional feeds that fail are reported as warnings and do not block; every
    required feed must pass. The answer is deliberately binary: a rebuild that
    ran on four of five fresh feeds is a rebuild on a stale slate.
    """
    now = _utc(now_utc, "now_utc")
    window = rolling_window(now, horizon_hours)
    verdicts = tuple(evaluate(spec, observations.get(spec.feed_id), now) for spec in specs)

    blocking = tuple(
        f"{v.feed_id}: {v.state.value} - {v.detail}"
        for v in verdicts
        if v.blocking
    )
    warnings = tuple(
        f"{v.feed_id}: {v.state.value} - {v.detail}"
        for v in verdicts
        if v.state is not FeedState.PASS and not v.blocking
    )
    unknown = sorted(set(observations) - {spec.feed_id for spec in specs})
    if unknown:
        warnings = warnings + (
            "observations recorded for feeds that are not declared: " + ", ".join(unknown),
        )
    return RefreshDecision(
        window=window,
        verdicts=verdicts,
        may_rebuild=not blocking,
        blocking_reasons=blocking,
        warnings=warnings,
        decided_at=now,
    )


def default_feed_specs() -> Tuple[FeedSpec, ...]:
    """The five feeds the brief names, with the freshness rules this project uses.

    These are declarations only. The URLs are the official documents the site
    already cites; nothing here asserts what those documents currently contain.

    Injury-report freshness is the tightest tolerance because the report is
    revised through the day and a stale status is the most expensive kind of
    stale input. Team statistics are the widest because the three pages change
    once per game day, and the row/chunk counts exist because all three pages
    were at one point published from a partial read (flag AN-04).

    ``max_age_minutes`` values are **operating choices, not measured truths**;
    they are stated here so a reviewer can disagree with them in one place.
    """
    return (
        FeedSpec(
            feed_id="schedule",
            label="Official 2026-27 regular-season schedule (PDF)",
            url=SCHEDULE_URL,
            required=True,
            max_age_minutes=24 * 60,
            requires_document_timestamp=False,
            notes=(
                'the PDF header prints "AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE": an '
                '"as of" date, not a revision clock, so freshness is measured from retrieval',
            ),
        ),
        FeedSpec(
            feed_id="standings",
            label="Official NBA standings (page prints no revision stamp)",
            url=STANDINGS_URL,
            required=True,
            max_age_minutes=12 * 60,
            requires_document_timestamp=False,
            expected_rows=30,
            notes=(NO_REVISION_STAMP,),
        ),
        FeedSpec(
            feed_id="team_stats_traditional",
            label="Official team stats, traditional page",
            url=TEAM_STATS_URLS[0],
            required=True,
            max_age_minutes=12 * 60,
            requires_document_timestamp=False,
            expected_rows=30,
            notes=(NO_REVISION_STAMP,),
        ),
        FeedSpec(
            feed_id="team_stats_opponent",
            label="Official team stats, opponent page",
            url=TEAM_STATS_URLS[1],
            required=True,
            max_age_minutes=12 * 60,
            requires_document_timestamp=False,
            expected_rows=30,
            notes=(NO_REVISION_STAMP,),
        ),
        FeedSpec(
            feed_id="team_stats_advanced",
            label="Official team stats, advanced page",
            url=TEAM_STATS_URLS[2],
            required=True,
            max_age_minutes=12 * 60,
            requires_document_timestamp=False,
            expected_rows=30,
            notes=(NO_REVISION_STAMP,),
        ),
        FeedSpec(
            feed_id="injuries",
            label="Official NBA injury report (newest revision)",
            url=INJURY_INDEX_URL,
            required=True,
            max_age_minutes=90,
            requires_document_timestamp=True,
            notes=(
                "the report PDF prints its own revision time "
                '(for example "Injury Report: 11/15/26 06:15 AM"), which is the strong basis',
                "reports are published every 15 minutes and supersede one another; an older "
                "revision is stale by definition, not by age alone",
            ),
        ),
        FeedSpec(
            feed_id="results",
            label="Official per-game results (settlement feed)",
            url=RESULTS_URL,
            required=False,
            max_age_minutes=6 * 60,
            requires_document_timestamp=False,
            notes=(
                "optional for a pre-tip rebuild because the slate has not been played yet; "
                "required for settlement, which engine/officialresults.py gates separately",
            ),
        ),
    )
