"""Settlement layer for official results: quarter-score integrity and feed timing.

The brief's first gap: the pipeline had completed-game *lines* (``TeamGame``) but
no notion of when a day's results are safe to settle a model against. A final
score alone does not prove the game ended — a truncated box score prints a final
line too. The official game page prints quarter-by-quarter linescores, so this
module treats "the four quarter scores add to the printed final, for both teams" as
the settlement condition.

Inputs come from ``data/snapshots/results-<date>.json`` (an official extraction;
see that file's provenance block). Nothing here estimates a quarter score: a row
without four printed quarters is reported as unchecked and blocks settlement.

Feed delay: the results document prints a tip time and a ``fetched_at_utc`` but no
game-end clock, so this module reports ``feed_delay_hours`` as ``None`` (rendered
``[NO INPUT]``) and instead prints the retrieval lag measured tip-to-fetch, clearly
labelled as lag *after the printed tip*, never as the end of the game.

2026-11-14 reference: five games, ten team lines, ten agreements
(``data/snapshots/results-2026-11-14.json``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from .inputs import NO_INPUT, MissingInput, official_link, require

__all__ = [
    "ResultLine",
    "LineCheck",
    "check_line",
    "check_day",
    "DayStatus",
    "load_results_snapshot",
    "feed_delay_hours",
    "settlement_gate",
]

QUARTERS = 4


@dataclass(frozen=True)
class ResultLine:
    """One team's printed line for one game, as the official page shows it."""

    game_id: str
    team: str
    quarters: Sequence[int | None]
    printed_final: int | None
    source_url: str = ""
    source_time: str = ""  # the timestamp the document itself carries
    observed_at: str = ""  # when we retrieved the document
    source_time_precision: str = "datetime"  # "date" when the page prints a date but no clock

    def _stamp(self, name: str, *, require_offset: bool) -> str:
        value = require(getattr(self, name), name, needed_for=f"{self.team} {self.game_id} timing")
        parsed = datetime.fromisoformat(str(value))
        if require_offset and parsed.tzinfo is None:
            raise MissingInput(
                f"{self.game_id} {self.team}: {name} must carry a UTC offset; the document prints no clock, "
                "so no time of day is invented"
            )
        return str(value)

    def validated(self) -> "ResultLine":
        require(self.game_id, "game_id", needed_for=f"the {self.team} result line")
        require(self.team, "team", needed_for="a result line")
        official_link(self.source_url, where=f"{self.team} {self.game_id} result line")
        # A dated page (scoreboard, game summary) prints its own date but no clock, so
        # source_time may be date-only; the retrieval time always carries an offset.
        self._stamp("source_time", require_offset=self.source_time_precision != "date")
        self._stamp("observed_at", require_offset=True)
        return self


@dataclass(frozen=True)
class LineCheck:
    game_id: str
    team: str
    quarter_sum: int | None
    printed_final: int | None
    agrees: bool | None
    note: str = ""

    @property
    def settlement_eligible(self) -> bool:
        return self.agrees is True


def check_line(line: ResultLine) -> LineCheck:
    """Add the quarters and compare with the printed final; never repair a mismatch."""
    line.validated()
    quarters = list(line.quarters or [])
    if len(quarters) != QUARTERS:
        return LineCheck(
            line.game_id,
            line.team,
            None,
            line.printed_final,
            None,
            f"only {len(quarters)} of {QUARTERS} quarter scores printed; not checked, not repaired",
        )
    if any(q is None for q in quarters):
        missing = [i + 1 for i, q in enumerate(quarters) if q is None]
        return LineCheck(
            line.game_id,
            line.team,
            None,
            line.printed_final,
            None,
            f"quarter(s) {missing} not printed; no quarter score invented",
        )
    if line.printed_final is None:
        return LineCheck(
            line.game_id, line.team, sum(quarters), None, None, "final not printed; nothing to compare"
        )
    total = sum(quarters)
    agrees = total == line.printed_final
    return LineCheck(
        line.game_id,
        line.team,
        total,
        line.printed_final,
        agrees,
        "quarter scores add to the printed final"
        if agrees
        else f"quarter sum {total} disagrees with printed final {line.printed_final}",
    )


@dataclass(frozen=True)
class DayStatus:
    """Whether a day of results can settle a forecast, and what we know about timing."""

    day: str
    games: int
    lines_checked: int
    agreed: int
    disagreed: int
    unchecked: int
    settled: bool
    feed_delay_hours: float | None
    retrieval_lag_after_tip_hours: float | None
    per_line: Sequence[LineCheck] = field(default_factory=tuple)
    source_url: str = ""

    @property
    def status(self) -> str:
        if self.unchecked:
            return "INCOMPLETE"
        return "SETTLED" if self.settled else "DISAGREEMENT"

    def reasons(self) -> list[str]:
        out = [f"{c.game_id} {c.team}: {c.note}" for c in self.per_line if c.agrees is not True]
        if self.feed_delay_hours is None:
            out.append(
                f"{NO_INPUT} feed delay: the results document prints no game-end clock, and no end time is "
                "invented; retrieval lag after the printed tip is reported instead"
            )
        return out


def _hours_between(earlier: str | None, later: str | None) -> float | None:
    if not earlier or not later:
        return None
    a = datetime.fromisoformat(str(earlier)).astimezone(timezone.utc)
    b = datetime.fromisoformat(str(later)).astimezone(timezone.utc)
    return round((b - a).total_seconds() / 3600.0, 4)


def feed_delay_hours(game_end_utc: str | None, retrieved_utc: str | None) -> float | None:
    """Hours between the last game's end and our retrieval; ``None`` when no end time is printed."""
    return _hours_between(game_end_utc, retrieved_utc)


def check_day(
    lines: Iterable[ResultLine],
    *,
    day: str,
    game_end_utc: str | None = None,
    last_tip_utc: str | None = None,
    retrieved_utc: str | None = None,
    source_url: str = "",
) -> DayStatus:
    checks = [check_line(line) for line in lines]
    if not checks:
        raise MissingInput(f"{day}: no result lines supplied, so settlement cannot be assessed")
    return DayStatus(
        day=day,
        games=len({c.game_id for c in checks}),
        lines_checked=len(checks),
        agreed=sum(1 for c in checks if c.agrees is True),
        disagreed=sum(1 for c in checks if c.agrees is False),
        unchecked=sum(1 for c in checks if c.agrees is None),
        settled=all(c.agrees is True for c in checks),
        feed_delay_hours=feed_delay_hours(game_end_utc, retrieved_utc),
        retrieval_lag_after_tip_hours=_hours_between(last_tip_utc, retrieved_utc),
        per_line=tuple(checks),
        source_url=official_link(source_url, where=f"{day} results"),
    )


def settlement_gate(status: DayStatus) -> dict[str, Any]:
    """The ledger-facing decision: settle, or refuse and say why.

    ``ledger.py`` stamps a settlement check with the fetch time; this is the
    predicate the ledger and the pages consult. A day with any unchecked line, or
    with a disagreement, settles nothing.
    """
    if status.unchecked == 0 and status.disagreed == 0 and status.settled:
        return {
            "action": "SETTLE",
            "day": status.day,
            "lines": f"{status.agreed}/{status.lines_checked}",
            "lag_after_tip_hours": status.retrieval_lag_after_tip_hours,
            "source_url": status.source_url,
        }
    return {
        "action": "REFUSE",
        "day": status.day,
        "lines": f"{status.agreed}/{status.lines_checked}",
        "reasons": status.reasons()[:8],
        "source_url": status.source_url,
    }


def load_results_snapshot(path: str | Path, *, last_tip_utc: str | None = None) -> DayStatus:
    """Build the day status from an official results snapshot file.

    ``last_tip_utc`` is the tip of the day's latest game in UTC; the snapshot
    prints the tip in ET ("9:00 PM"), and the caller passes the UTC equivalent
    rather than letting this module guess the offset for a dated page.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    lines: list[ResultLine] = []
    for row in payload["rows"]:
        for team, quarters, final, idx in (
            (row[5], row[7], row[8], "away"),
            (row[6], row[9], row[10], "home"),
        ):
            lines.append(
                ResultLine(
                    game_id=str(row[0]),
                    team=team,
                    quarters=list(quarters),
                    printed_final=final,
                    source_url=row[13],
                    source_time=row[1],
                    source_time_precision="date",
                    observed_at=payload["fetched_at_utc"],
                )
            )
    day = payload["rows"][0][1]
    status = check_day(
        lines,
        day=day,
        game_end_utc=None,  # the document prints no end clock; see the module docstring
        last_tip_utc=last_tip_utc,
        retrieved_utc=payload["fetched_at_utc"],
        source_url=payload["source_index_url"],
    )
    if payload["verification"]["independent_source_disagreements"]:
        raise MissingInput(
            f"{day}: the snapshot records {payload['verification']['independent_source_disagreements']} "
            "disagreement(s) between the scoreboard and the recap headlines; not settled here"
        )
    return status
