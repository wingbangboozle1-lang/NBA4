"""Minutes concentration and replacement-minutes share (task AN, gap 9).

Two published measures, both computed only from printed box-score minutes:

* **top-8 share** — the share of a team's game minutes taken by its eight heaviest
  users. The brief names eight; the constant is printed so a reader can recompute.
* **replacement share** — the minutes belonging to unavailable players, expressed
  as a share of the team's total, i.e. how much production has to be replaced.

Both need the *team total minutes*, which the official box score prints in the team
line ("TEAM" row: MIN). When it is absent the module refuses: summing the player
rows and calling that the total silently drops the bench/adjustment line and would
overstate the share of any rotation. And an unavailable player can only be credited
with minutes when a printed line ties them to a team — an injury row whose team cell
was dropped at a page break is counted, not attributed (see ``engine/injurystore``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .inputs import MissingInput, official_link, require
from .injurystore import InjuryRow

__all__ = ["TOP_N", "MinutesRow", "top_n_share", "replacement_share", "rotation_availability"]

TOP_N = 8  # the brief's "top 8" concentration window


@dataclass(frozen=True)
class MinutesRow:
    team: str
    player: str
    minutes: float
    game_id: str = ""
    source_url: str = ""


def _team_total(rows: Sequence[MinutesRow], team: str) -> tuple[float, str]:
    """Read the printed TEAM MIN line; refuse when it is not there."""
    totals = [r for r in rows if r.player.upper() in ("TEAM", "TEAM TOTAL", "TOTALS")]
    if not totals:
        raise MissingInput(
            f"{team}: no printed team total minutes line, so the share denominator is unknown; the player rows "
            "are not summed to create one"
        )
    total = totals[0].minutes
    if total <= 0:
        raise MissingInput(f"{team}: the team total minutes line prints {total}, which cannot be a denominator")
    return float(total), "printed team MIN line"


def top_n_share(rows: Sequence[MinutesRow], team: str, *, n: int = TOP_N, source_url: str = "") -> dict[str, Any]:
    """Share of team minutes held by the ``n`` heaviest users, plus who they are."""
    require(rows, "box-score minutes rows", needed_for=f"{team} minutes concentration")
    mine = [r for r in rows if r.team == team and r.player.upper() not in ("TEAM", "TEAM TOTAL", "TOTALS")]
    if len(mine) < n:
        raise MissingInput(
            f"{team}: only {len(mine)} player lines printed, fewer than the {n} needed for a top-{n} share"
        )
    total, basis = _team_total(rows, team)
    heaviest = sorted(mine, key=lambda r: -r.minutes)[:n]
    held = sum(r.minutes for r in heaviest)
    if held > total + 1e-9:
        raise MissingInput(
            f"{team}: the top-{n} minutes ({held:g}) exceed the printed team total ({total:g}); the extraction "
            "is inconsistent and no share is published"
        )
    return {
        "team": team,
        "n": n,
        "team_minutes": total,
        "basis": basis,
        "top_minutes": round(held, 2),
        "share": round(held / total, 4),
        "players": [
            {
                "player": r.player,
                "minutes": r.minutes,
                "share_of_team": round(r.minutes / total, 4),
                "source_url": r.source_url or source_url,
            }
            for r in heaviest
        ],
        "source_url": official_link(source_url, where=f"{team} minutes share") if source_url else "",
    }


def replacement_share(
    unavailable: Sequence[InjuryRow],
    minutes: Sequence[MinutesRow],
    team: str,
    *,
    source_url: str = "",
) -> dict[str, Any]:
    """Minutes that must be replaced, as a share of the team total.

    A player is credited with minutes only when a printed ``MinutesRow`` exists for
    them on this team, i.e. only from a real box score. A player with no printed line
    (season-long absence, late signing) is listed as *unattributed* and excluded from
    the numerator, with the count reported.
    """
    require(unavailable, "unavailable players", needed_for=f"{team} replacement share")
    total, basis = _team_total(minutes, team)
    by_player = {r.player: r for r in minutes if r.team == team}
    attributed, unattributed, dropped_team_cell = [], [], 0
    for row in unavailable:
        if not row.aligned:
            dropped_team_cell += 1
            continue
        if row.team != team:
            continue
        line = by_player.get(row.player)
        if line is None:
            unattributed.append(row.player)
        else:
            attributed.append((row.player, line.minutes))
    held = sum(m for _, m in attributed)
    return {
        "team": team,
        "team_minutes": total,
        "basis": basis,
        "players_with_minutes": [
            {"player": p, "minutes": m, "share_of_team": round(m / total, 4)} for p, m in attributed
        ],
        "replacement_minutes": round(held, 2),
        "replacement_share": round(held / total, 4),
        "unattributed_players": unattributed,
        "rows_excluded_for_missing_team_cell": dropped_team_cell,
        "note": "unattributed players are excluded from the numerator: the box score prints no line for them, "
        "and an average is not substituted",
        "source_url": official_link(source_url, where=f"{team} replacement share") if source_url else "",
    }


def rotation_availability(
    team: str,
    *,
    roster_minutes: Sequence[MinutesRow],
    unavailable: Sequence[InjuryRow],
    source_url: str = "",
) -> dict[str, Any]:
    """Who is left, in minutes order, once printed unavailability is removed.

    Returns the remaining rotation and the count of players whose availability could
    not be resolved from the extraction; it never reorders a rotation on assumption.
    """
    total, basis = _team_total(roster_minutes, team)
    out_names = {r.player for r in unavailable if r.aligned and r.team == team and r.status}
    remaining = [r for r in roster_minutes if r.team == team and r.player.upper() not in ("TEAM", "TEAM TOTAL", "TOTALS") and r.player not in out_names]
    if not remaining:
        raise MissingInput(f"{team}: every printed player is listed unavailable; no rotation remains to report")
    return {
        "team": team,
        "team_minutes": total,
        "basis": basis,
        "available_players": len(remaining),
        "top8_available_minutes": round(sum(r.minutes for r in sorted(remaining, key=lambda r: -r.minutes)[:TOP_N]), 2),
        "removed": sorted(out_names),
        "note": "players with an unresolved (unaligned) injury row are not removed: their team cell was not "
        "printed, so removing them would attribute a row to this team",
        "source_url": official_link(source_url, where=f"{team} rotation availability") if source_url else "",
    }
