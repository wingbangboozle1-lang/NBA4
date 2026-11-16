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
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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
    "INJURY_PDF_PREFIX",
    "default_feed_specs",
    "observations_from_run_record",
    "decision_from_run_record",
    "parse_report_label",
]

DEFAULT_HORIZON_HOURS = 72
"""The requested maximum forecast horizon: three days."""

SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
STANDINGS_URL = "https://www.nba.com/standings"
INJURY_PDF_PREFIX = "https://ak-static.cms.nba.com/referee/injury/"
"""Host and path the official index publishes the dated report PDFs under."""
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
    accepted_url_prefixes: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.feed_id or not self.label:
            raise RefreshError("a feed spec requires feed_id and label")
        _https(self.url, f"{self.feed_id}.url")
        if self.max_age_minutes <= 0:
            raise RefreshError(f"{self.feed_id}: max_age_minutes must be positive")
        if self.expected_rows is not None and self.expected_rows <= 0:
            raise RefreshError(f"{self.feed_id}: expected_rows must be positive when set")
        for prefix in self.accepted_url_prefixes:
            _https(prefix, f"{self.feed_id}.accepted_url_prefixes")
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


def _url_accepted(spec: FeedSpec, url: str) -> bool:
    """Is ``url`` the document this feed declares, or an accepted alternative?

    Exact equality is the rule for every feed by default. ``accepted_url_prefixes``
    exists for the one case where an official feed is served from more than one
    host: the injury report is *listed* on an index page but *published* as a
    dated PDF on a different host, and a run that records the PDF it actually
    fetched must not be reported as reading the wrong document.
    """
    if url == spec.url:
        return True
    return any(url.startswith(prefix) for prefix in spec.accepted_url_prefixes)


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
    if not _url_accepted(spec, observation.url):
        return verdict(
            FeedState.URL_MISMATCH,
            f"observed from {observation.url} but the declared official document is {spec.url}"
            + (
                f" or one of {list(spec.accepted_url_prefixes)}"
                if spec.accepted_url_prefixes
                else ""
            )
            + "; a feed is identified by its document",
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
            accepted_url_prefixes=(INJURY_PDF_PREFIX,),
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


# --- bridge to scripts/scheduled_refresh.py -----------------------------------
#
# Session `arena/cbc8e41a-nba4` (task BH) owns `scripts/scheduled_refresh.py`,
# which performs the fetches and records a run record. This module owns the
# per-feed decision. Rather than either session editing the other's file, the
# adapter below converts one artefact into the other's input. It reads a run
# record and never writes one.

_RUN_RECORD_FEEDS: Tuple[Tuple[str, str], ...] = (
    ("schedule", "schedule_pdf"),
    ("standings", "standings"),
    ("team_stats_traditional", "teamstats_traditional"),
    ("team_stats_opponent", "teamstats_opponent"),
    ("team_stats_advanced", "teamstats_advanced"),
    ("injuries", "injury_report_newest"),
)
"""feed_id -> the key `scripts/scheduled_refresh.py` uses for that fetch."""


def observations_from_run_record(
    record: Mapping[str, Any],
    *,
    allowed_use: bool = False,
    report_tz: Optional[timezone] = None,
) -> Dict[str, FeedObservation]:
    """Translate a scheduled-refresh run record into feed observations.

    The run record is the output of ``scripts/scheduled_refresh.py``: a mapping
    with ``now_utc``, ``fetches`` and ``gates``. Its ``fetches`` entries carry a
    ``status``, and for the tabular pages a ``rows`` count, which is exactly the
    completeness evidence this gate needs.

    Two honesty rules govern the translation:

    * A run record carries one clock, ``now_utc``, not a per-feed retrieval
      time. The adapter uses it for every feed and says so in the observation
      note, so a freshness verdict is never presented as more precise than the
      record supports.
    * A feed absent from ``fetches`` produces **no** observation. It therefore
      arrives at the gate as ``NOT_RETRIEVED`` and blocks, rather than being
      smoothed into an empty or successful fetch.

    A fetch whose ``status`` is not 200 also produces no observation, for the
    same reason: a failed fetch is not a feed that was read and happened to be
    empty.

    ``allowed_use`` defaults to ``False``, so observations produced here block
    on rights gate G0 until an operator clears them.

    ``report_tz`` is the offset to attach to the injury report's printed
    revision label. It defaults to ``None``, meaning *do not parse the label*;
    the feed then fails with ``NO_DOCUMENT_TIMESTAMP`` rather than carrying a
    timestamp built on a guessed offset. See :func:`parse_report_label`.
    """
    fetches = record.get("fetches")
    if not isinstance(fetches, Mapping):
        raise RefreshError("run record has no 'fetches' mapping; nothing can be observed")

    now_text = record.get("now_utc")
    if not isinstance(now_text, str) or not now_text:
        raise RefreshError("run record has no 'now_utc'; the retrieval time is unknown")
    retrieved_at = _parse_iso(now_text)

    declared = {spec.feed_id: spec.url for spec in default_feed_specs()}
    observations: Dict[str, FeedObservation] = {}
    for feed_id, key in _RUN_RECORD_FEEDS:
        entry = fetches.get(key)
        if not isinstance(entry, Mapping):
            continue
        if entry.get("status") != 200:
            continue
        notes = [f"translated from scripts/scheduled_refresh.py fetch key {key!r}"]
        notes.append("retrieval time is the run record's now_utc, not a per-feed clock")
        document_timestamp = None
        label = entry.get("label")
        if isinstance(label, str) and label:
            notes.append(f"report label as printed: {label}")
            if report_tz is not None:
                document_timestamp = parse_report_label(label, report_tz)
                if document_timestamp is None:
                    notes.append("label is not in the printed MM/DD/YY HH:MM AM/PM form")
                else:
                    notes.append(
                        f"revision parsed at offset {report_tz} supplied by the caller"
                    )
            else:
                notes.append(
                    "no report_tz supplied, so the printed revision is not converted "
                    "to a timestamp rather than being given a guessed offset"
                )
        entry_url = entry.get("url")
        url = str(entry_url) if isinstance(entry_url, str) and entry_url else declared[feed_id]
        if url != declared[feed_id]:
            notes.append(f"fetched from {url}; the declared document is {declared[feed_id]}")
        observations[feed_id] = FeedObservation(
            feed_id=feed_id,
            url=url,
            retrieved_at=retrieved_at,
            document_timestamp=document_timestamp,
            rows_read=entry.get("rows") if isinstance(entry.get("rows"), int) else None,
            chunks_read=entry.get("chunks") if isinstance(entry.get("chunks"), int) else None,
            allowed_use=allowed_use,
            note="; ".join(notes),
        )
    return observations


def decision_from_run_record(
    record: Mapping[str, Any],
    *,
    allowed_use: bool = False,
    report_tz: Optional[timezone] = None,
    specs: Optional[Sequence[FeedSpec]] = None,
) -> RefreshDecision:
    """Gate a scheduled-refresh run record with the declared feed specs.

    Convenience wrapper: :func:`observations_from_run_record` followed by
    :func:`refresh_decision` at the run record's own ``now_utc``.
    """
    now_text = record.get("now_utc")
    if not isinstance(now_text, str) or not now_text:
        raise RefreshError("run record has no 'now_utc'; the decision time is unknown")
    return refresh_decision(
        tuple(specs) if specs is not None else default_feed_specs(),
        observations_from_run_record(record, allowed_use=allowed_use, report_tz=report_tz),
        _parse_iso(now_text),
    )


_REPORT_LABEL_RE = re.compile(
    r"^\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)\s*$",
    re.IGNORECASE,
)
"""The injury-report revision label: ``11/16/26 09:15 AM``."""


def parse_report_label(label: str, tz: timezone) -> Optional[datetime]:
    """Turn a printed injury-report revision label into an aware timestamp.

    The official report prints its revision as ``11/16/26 09:15 AM``. That is a
    wall-clock time with no offset, so the offset cannot be derived from the
    label and this function does not guess one: the caller supplies ``tz`` and
    thereby owns the assumption. Callers that will not assert an offset should
    pass nothing and let the feed fail with ``NO_DOCUMENT_TIMESTAMP``, which is
    the honest outcome, rather than accept a silently invented one.

    Returns ``None`` when the label is not in the printed form.
    """
    match = _REPORT_LABEL_RE.match(label)
    if match is None:
        return None
    month, day, year, hour, minute, meridiem = match.groups()
    year_int = int(year)
    if year_int < 100:
        year_int += 2000
    hour_int = int(hour) % 12
    if meridiem.upper() == "PM":
        hour_int += 12
    return datetime(
        year_int, int(month), int(day), hour_int, int(minute), tzinfo=tz
    )


def _parse_iso(text: str) -> datetime:
    """Parse an ISO-8601 timestamp, requiring a UTC-aware result."""
    cleaned = text.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise RefreshError(f"not an ISO-8601 timestamp: {text!r}") from exc
    return _utc(parsed, "timestamp")
