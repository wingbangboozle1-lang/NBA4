"""Rest, back-to-backs and official disruption notices (task AN, gap 8).

The brief asks for travel/rest load to be *measured from official inputs*, not
guessed from a team's schedule reputation. Three things are computed:

* :func:`rest` — hours between two printed tips (this is arithmetic on the schedule
  extraction, so it always has a value once both tips are printed);
* :func:`back_to_back` and :func:`games_in_nights` — counts over a printed window,
  which *refuse* when the supplied games do not cover every night in the window,
  because a partial slate under-counts;
* :func:`disruption` — a published travel disruption (e.g. a nationwide ground
  stop) tied to a named official document, and nothing else.

2026-11-14 real case, recorded in the session notes: the Friday ground stop delayed
both Chicago (arrived Minneapolis on game day) and Cleveland's return; the Bulls won
short-handed. That is an *input* to a flag, never a coefficient fitted from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

from .inputs import MissingInput, official_link, require

__all__ = ["rest_hours", "BackToBack", "back_to_back", "games_in_nights", "Disruption", "disruption", "load_slate_days"]

BACK_TO_BACK_HOURS = 48.0  # published threshold: next tip inside 48 h of the previous tip


@dataclass(frozen=True)
class Tip:
    game_id: str
    team: str
    tip_utc: str

    def dt(self) -> datetime:
        value = require(self.tip_utc, "tip_utc", needed_for=f"{self.team} rest calculation")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise MissingInput(f"{self.game_id}: tip_utc must carry a UTC offset; ET tips are not assumed")
        return parsed.astimezone(timezone.utc)


def rest_hours(previous: Tip, current: Tip) -> float:
    """Hours from one printed tip to the next. Both tips must come from a document."""
    if previous.team != current.team:
        raise MissingInput(f"rest: {previous.team} and {current.team} are different teams")
    return round((current.dt() - previous.dt()).total_seconds() / 3600.0, 4)


@dataclass(frozen=True)
class BackToBack:
    team: str
    previous_tip: str
    current_tip: str
    rest: float
    is_back_to_back: bool
    short_rest: bool
    source_url: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "team": self.team,
            "previous_tip": self.previous_tip,
            "current_tip": self.current_tip,
            "rest_hours": self.rest,
            "back_to_back": self.is_back_to_back,
            "under_36_hours": self.short_rest,
            "source_url": self.source_url,
        }


def back_to_back(previous: Tip, current: Tip, *, source_url: str = "", short_rest_hours: float = 36.0) -> BackToBack:
    """Second game of a split pair, measured tip-to-tip.

    ``short_rest_hours`` is printed separately from the 48 h definition so a caller
    can flag "tight" without redefining a back-to-back.
    """
    gap = rest_hours(previous, current)
    if gap < 0:
        raise MissingInput(f"{current.team}: the 'current' tip precedes the 'previous' tip; inputs are swapped")
    return BackToBack(
        team=current.team,
        previous_tip=previous.tip_utc,
        current_tip=current.tip_utc,
        rest=gap,
        is_back_to_back=gap <= BACK_TO_BACK_HOURS,
        short_rest=gap <= short_rest_hours,
        source_url=official_link(source_url, where=f"{current.team} rest") if source_url else "",
    )


def games_in_nights(tips: Sequence[Tip], *, team: str, window_nights: int, anchor: str) -> dict[str, Any]:
    """Count a team's games in a printed number of nights, or refuse for incomplete coverage.

    ``anchor`` is the last date of the window; the count is only emitted when the
    supplied tips span the whole window (every night present as a calendar date, even
    if a night has no game for this team), because a slate that stops at 11/16 cannot
    answer "4 games in 4 nights" for a window ending 11/18.
    """
    require(tips, "team tips", needed_for=f"{team} {window_nights}-night load")
    mine = [t for t in tips if t.team == team]
    end = datetime.fromisoformat(anchor).date()
    days_needed = {end.toordinal() - i for i in range(window_nights)}
    present = {t.dt().date().toordinal() for t in tips}
    missing = sorted(days_needed - present)
    if missing:
        return {
            "team": team,
            "window_nights": window_nights,
            "games": None,
            "status": "REFUSED",
            "reason": (
                f"the supplied slate does not print games for {len(missing)} night(s) in the window "
                f"(ordinals {missing}); a partial slate would under-count"
            ),
        }
    in_window = [t for t in mine if end.toordinal() - window_nights < t.dt().date().toordinal() <= end.toordinal()]
    return {
        "team": team,
        "window_nights": window_nights,
        "games": len(in_window),
        "fifth_in_four": len(in_window) >= 5,
        "status": "OK",
        "game_ids": [t.game_id for t in in_window],
    }


@dataclass(frozen=True)
class Disruption:
    """An official travel-disruption notice that applies to a team's travel."""

    team: str
    notice_url: str
    notice_time_utc: str
    applies_to_game_id: str
    label: str
    penalty_allowed: bool = False
    note: str = (
        "A published ground stop is an availability/rest input, not a fitted point value. Any penalty remains "
        "0.0 until a calibration is preregistered and cleared by rights gate G0."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "team": self.team,
            "notice_url": self.notice_url,
            "notice_time_utc": self.notice_time_utc,
            "game_id": self.applies_to_game_id,
            "label": self.label,
            "penalty_points": 0.0,
            "penalty_allowed": self.penalty_allowed,
            "note": self.note,
        }


def disruption(
    *,
    team: str,
    notice_url: str,
    notice_time_utc: str,
    game_id: str,
    label: str,
    affected_game_ids: Sequence[str] = (),
) -> Disruption:
    """Attach a named notice to a game. The notice must print the game it affects.

    ``affected_game_ids`` is the set the *document* lists as affected (the schedule
    page, a postponed-game notice, a team travel note). When the document prints no
    such list, the flag records the notice without a penalty: the link from "ground
    stop" to "this team was delayed" is then unproven, and unproven is what gets
    published.
    """
    require(label, "label", needed_for=f"{team} disruption flag")
    link = official_link(notice_url, where=f"{team} disruption notice")
    require(notice_time_utc, "notice_time_utc", needed_for=f"{team} disruption notice timing")
    stamp = datetime.fromisoformat(notice_time_utc)
    if stamp.tzinfo is None:
        raise MissingInput(f"{team}: notice_time_utc must carry a UTC offset")
    applies = not affected_game_ids or game_id in set(affected_game_ids)
    return Disruption(
        team=team,
        notice_url=link,
        notice_time_utc=notice_time_utc,
        applies_to_game_id=game_id,
        label=label,
        penalty_allowed=False,
        note=(
            "the notice lists this game as affected; still no penalty value is applied without a "
            "preregistered calibration"
            if applies
            else "the notice does not list this game; recorded as an unlinked notice, no flag on the game"
        ),
    )


def load_slate_days(games: Iterable[dict[str, Any]], *, team_names: Sequence[str] | None = None) -> dict[str, list[Tip]]:
    """Group a slate extraction's games into per-team tips.

    ``games`` rows are the schedule-snapshot dicts (``away``/``home``/``tip_*``); the
    caller converts ET tips to UTC because the printed page carries an ET column and a
    local column, and the offset for a given date is an explicit conversion.
    """
    out: dict[str, list[Tip]] = {}
    for row in games:
        for side in ("away", "home"):
            team = row.get(side)
            if not team or (team_names and team not in team_names):
                continue
            tip = row.get(f"tip_{side}_utc") or row.get("tip_utc")
            if not tip:
                continue
            out.setdefault(team, []).append(Tip(str(row.get("row", row.get("game_id", "?"))), team, tip))
    return out
