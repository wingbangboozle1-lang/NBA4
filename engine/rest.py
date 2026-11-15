"""Rest, back-to-back and 3-in-4 from official schedule rows.

Brief item implemented (2026-11-15): "Compute rest, back-to-back and 3-in-4
from the official schedule (already possible) and add travel distance from a
sourced arena-coordinate table." (Travel lives in ``engine/venues.py``; the two
combine in ``rest_and_travel`` below.)

Definitions used, stated so a reviewer can disagree with them:

* **days rest** = whole days between a team's previous game date and the game
  date in question (date difference, not hours). A same-day game is impossible
  in this data and would be a source error, so it raises.
* **back-to-back** = days rest equal to 1.
* **3-in-4** = three or more games inside the four-date window that ends on the
  game date in question (the game itself counted). 2-in-3 and 4-in-6 are
  reported beside it because coaches and models use all three.
* **rest differential** = this team's days rest minus its opponent's. It is the
  only quantity here that compares two teams, so it needs both teams' schedules
  and is left ``None`` when either side is unknown.

Scope discipline: everything here is computed from game *dates* on an official
schedule listing. Tip times are used only to order games on the same date. A
date the schedule does not cover is reported as a coverage gap - the module never
treats "not in my rows" as "no game", because the published schedule rows in
this repository are a window, not the season. That is why ``coverage`` is part of
every result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class RestError(ValueError):
    """Raised when the schedule rows are inconsistent or out of coverage."""


def _as_date(value: str) -> date:
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except (TypeError, ValueError) as exc:
        raise RestError(f"unrecognised game date: {value!r}") from exc


@dataclass(frozen=True)
class ScheduleRow:
    """One game as printed by the official schedule, normalised to dates."""

    game_date: str
    away_team: str
    home_team: str
    tip: str = ""
    row_ref: str = ""          # e.g. "schedule PDF row 236"
    source_url: str = ""

    def date(self) -> date:
        return _as_date(self.game_date)

    def teams(self) -> Tuple[str, str]:
        if not self.away_team or not self.home_team:
            raise RestError(f"{self.row_ref or self.game_date}: away_team/home_team required")
        return self.away_team, self.home_team

    def validate(self) -> "ScheduleRow":
        self.date()
        self.teams()
        if self.source_url and not self.source_url.startswith("https://"):
            raise RestError(f"{self.row_ref}: source_url must be https://")
        return self


@dataclass(frozen=True)
class TeamDateLine:
    team: str
    game_date: str
    is_home: bool
    opponent: str
    row_ref: str
    source_url: str
    tip: str = ""


class TeamCalendar:
    """team -> sorted game dates, built only from the rows supplied."""

    def __init__(self, rows: Sequence[ScheduleRow]) -> None:
        lines: Dict[str, List[TeamDateLine]] = {}
        for row in rows:
            row.validate()
            away, home = row.teams()
            lines.setdefault(away, []).append(
                TeamDateLine(away, row.game_date, False, home, row.row_ref, row.source_url, row.tip)
            )
            lines.setdefault(home, []).append(
                TeamDateLine(home, row.game_date, True, away, row.row_ref, row.source_url, row.tip)
            )
        for team, entries in lines.items():
            entries.sort(key=lambda e: (_as_date(e.game_date), e.tip))
        self.lines = lines
        self.coverage = (
            min((_as_date(r.game_date) for r in rows), default=None),
            max((_as_date(r.game_date) for r in rows), default=None),
        ) if rows else (None, None)

    def dates_for(self, team: str) -> List[date]:
        return [_as_date(e.game_date) for e in self.lines.get(team, [])]

    def in_coverage(self, when: date) -> bool:
        start, end = self.coverage
        return start is not None and end is not None and start <= when <= end

    @property
    def row_count(self) -> int:
        return sum(len(v) for v in self.lines.values()) // 2


@dataclass(frozen=True)
class RestState:
    """One team's load state entering one game."""

    team: str
    game_date: str
    days_rest: Optional[int]
    previous_game_date: Optional[str]
    back_to_back: Optional[bool]
    games_in_last_4: int
    three_in_four: bool
    games_in_last_3: int
    two_in_three: bool
    games_in_last_6: int
    four_in_six: bool
    rest_advantage: Optional[int]
    coverage_complete: bool
    notes: Tuple[str, ...] = ()
    sources: Tuple[str, ...] = ()

    @property
    def label(self) -> str:
        if self.days_rest is None:
            return "first tracked game (no prior date inside coverage)"
        if self.back_to_back:
            return "back-to-back (0 days rest would be same-day; 1 day)"
        if self.three_in_four:
            return f"3-in-4 ({self.games_in_last_4} games in 4 days)"
        return f"{self.days_rest} days rest"


def _games_in_window(dates: Sequence[date], target: date, window: int) -> int:
    """Games whose date is in [target-window+1, target], the target game included."""
    start = target - timedelta(days=window - 1)
    return sum(1 for d in dates if start <= d <= target)


def rest_state(
    calendar: TeamCalendar,
    team: str,
    game_date: str,
    opponent: Optional[str] = None,
) -> RestState:
    """Compute this team's rest facts, with coverage gaps stated."""
    target = _as_date(game_date)
    dates = calendar.dates_for(team)
    if not dates:
        return RestState(
            team, game_date, None, None, None, 0, False, 0, False, 0, False, None, False,
            ("no schedule rows for this team inside the loaded window; rest is unmeasurable",),
        )
    earlier = [d for d in dates if d < target]
    same_day = [d for d in dates if d == target]
    if len(same_day) > 1:
        raise RestError(f"{team}: {len(same_day)} games printed on {game_date}; the source is ambiguous")
    prev = max(earlier) if earlier else None
    days_rest = (target - prev).days if prev is not None else None
    notes: List[str] = []
    if prev is None and not calendar.in_coverage(target - timedelta(days=1)):
        notes.append(
            "no previous game inside the loaded coverage; days-rest is unknown rather than 0"
        )
    coverage_complete = all(calendar.in_coverage(d) for d in (prev, target)) if prev else calendar.in_coverage(target)
    in4 = _games_in_window(dates, target, 4)
    in3 = _games_in_window(dates, target, 3)
    in6 = _games_in_window(dates, target, 6)
    advantage: Optional[int] = None
    if opponent is not None:
        opp_dates = calendar.dates_for(opponent)
        opp_earlier = [d for d in opp_dates if d < target]
        if opp_earlier:
            advantage = days_rest - (target - max(opp_earlier)).days if days_rest is not None else None
        else:
            notes.append(f"opponent {opponent} has no prior game inside coverage; rest differential unknown")
    return RestState(
        team=team,
        game_date=game_date,
        days_rest=days_rest,
        previous_game_date=prev.isoformat() if prev else None,
        back_to_back=(days_rest == 1) if days_rest is not None else None,
        games_in_last_4=in4,
        three_in_four=in4 >= 3,
        games_in_last_3=in3,
        two_in_three=in3 >= 2,
        games_in_last_6=in6,
        four_in_six=in6 >= 4,
        rest_advantage=advantage,
        coverage_complete=coverage_complete,
        notes=tuple(notes),
        sources=tuple(sorted({e.source_url for e in calendar.lines.get(team, []) if e.source_url})),
    )


def rest_and_travel(
    calendar: TeamCalendar,
    team: str,
    game_date: str,
    opponent: Optional[str] = None,
    venue_table: Optional[Mapping[str, object]] = None,
    previous_opponent: Optional[str] = None,
) -> Dict[str, object]:
    """Join the rest facts with the travel leg, keeping both verdicts separate.

    The join is deliberately shallow: a travel row that cannot be verified does
    not cancel a rest row that can, and vice versa. Each keeps its own code and
    its own source.
    """
    from .venues import TRAVEL_NO_SOURCE, leg_between, travel_leg  # local import: optional dependency

    state = rest_state(calendar, team, game_date, opponent)
    dates = calendar.dates_for(team)
    target = _as_date(game_date)
    earlier = [d for d in dates if d < target]
    out: Dict[str, object] = {
        "team": team,
        "game_date": game_date,
        "rest": {
            "days_rest": state.days_rest,
            "back_to_back": state.back_to_back,
            "three_in_four": state.three_in_four,
            "games_in_last_4": state.games_in_last_4,
            "games_in_last_3": state.games_in_last_3,
            "games_in_last_6": state.games_in_last_6,
            "rest_advantage": state.rest_advantage,
            "coverage_complete": state.coverage_complete,
            "label": state.label,
            "notes": list(state.notes),
            "sources": list(state.sources),
        },
        "travel": None,
        "travel_note": "no previous game inside coverage; there is no leg to measure",
    }
    if earlier and previous_opponent:
        prev_date = max(earlier)
        leg = (
            leg_between(team, prev_date.isoformat(), game_date, previous_opponent, opponent or "", venue_table)
            if opponent
            else travel_leg(team, prev_date.isoformat(), game_date, venue_table)
        )
        out["travel"] = {
            "from_date": prev_date.isoformat(),
            "to_date": game_date,
            "miles": leg.miles,
            "kilometres": leg.kilometres,
            "code": leg.code,
            "detail": leg.detail,
            "from_arena": leg.from_arena,
            "to_arena": leg.to_arena,
            "source_urls": list(leg.source_urls),
        }
        out["travel_note"] = leg.code
    elif earlier:
        out["travel_note"] = (
            "previous game date is known but the arena of the previous opponent is not registered; "
            f"{TRAVEL_NO_SOURCE}"
        )
    return out


def slate_rest_table(
    calendar: TeamCalendar,
    games: Sequence[Tuple[str, str, str]],
) -> List[Dict[str, object]]:
    """Rows for the slate/availability page: (game_date, away, home) -> rest rows."""
    rows: List[Dict[str, object]] = []
    for game_date, away, home in games:
        for team, opp in ((away, home), (home, away)):
            state = rest_state(calendar, team, game_date, opp)
            rows.append(
                {
                    "game_date": game_date,
                    "team": team,
                    "versus": opp,
                    "days_rest": state.days_rest,
                    "back_to_back": state.back_to_back,
                    "three_in_four": state.three_in_four,
                    "games_in_last_4": state.games_in_last_4,
                    "rest_advantage": state.rest_advantage,
                    "coverage_complete": state.coverage_complete,
                    "label": state.label,
                    "sources": list(state.sources),
                }
            )
    return rows


def coverage_gaps(calendar: TeamCalendar, dates: Sequence[str]) -> List[str]:
    """Dates that fall outside the loaded schedule window."""
    return [d for d in dates if not calendar.in_coverage(_as_date(d))]
