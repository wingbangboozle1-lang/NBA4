"""Rest, back-to-back, 3-in-4 and travel distance.

Rest days, back-to-back flags and 3-in-4 flags are computed from the
official schedule - the schedule is the only source of tip dates and times,
so it is the only source used here.

Travel distance needs a **sourced arena-coordinate table**: the coordinates
of each venue, with the official source that publishes them.  A venue whose
coordinates are not confirmed by an official source has no coordinate, and
therefore no travel distance - the value stays blank rather than being
estimated.

The distance metric is the great-circle (haversine) distance between the two
venue coordinates, in statute miles.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "EARTH_RADIUS_MILES",
    "Arena",
    "TeamLoad",
    "haversine_miles",
    "load_arenas",
    "compute_load",
]

EARTH_RADIUS_MILES = 3958.7613
"""Mean Earth radius in statute miles (IUGG mean radius, 6371.0088 km)."""


@dataclass
class Arena:
    """One venue and the official source that publishes its coordinates."""

    team: str
    venue: str
    city: str
    latitude: Optional[float]
    longitude: Optional[float]
    source_url: str
    source_label: str = ""
    verified: bool = True
    note: str = ""

    @property
    def has_coordinates(self) -> bool:
        return (
            self.latitude is not None
            and self.longitude is not None
            and self.verified
        )


@dataclass
class TeamLoad:
    """Schedule load for one team in one game."""

    team: str
    game_id: str
    tip_time: str
    rest_days: Optional[float]
    is_back_to_back: Optional[bool]
    is_three_in_four: Optional[bool]
    games_in_next_four_days: Optional[int]
    travel_miles: Optional[float]
    previous_venue: Optional[str]
    notes: Tuple[str, ...] = ()


def haversine_miles(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Great-circle distance in statute miles between two coordinates."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(min(1.0, math.sqrt(a)))


def load_arenas(path: str | Path) -> Dict[str, Arena]:
    """Load the sourced arena-coordinate table.

    The file is JSON: ``{"arenas": [{"team", "venue", "city", "latitude",
    "longitude", "source_url", "source_label", "verified", "note"}]}``.
    A row whose coordinates are missing, unverified or missing its official
    source URL is still loaded, but it carries no usable coordinate and
    therefore produces no travel distance.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    arenas: Dict[str, Arena] = {}
    for row in raw.get("arenas", []):
        lat = row.get("latitude")
        lon = row.get("longitude")
        source_url = row.get("source_url") or ""
        verified = bool(row.get("verified", False))
        if not source_url.startswith("https://"):
            verified = False
        if lat is not None and lon is not None and not verified:
            # An unverified coordinate is not usable evidence.
            lat = lon = None
        arenas[row["team"]] = Arena(
            team=row["team"],
            venue=row.get("venue", ""),
            city=row.get("city", ""),
            latitude=None if lat is None else float(lat),
            longitude=None if lon is None else float(lon),
            source_url=source_url,
            source_label=row.get("source_label", ""),
            verified=verified,
            note=row.get("note", ""),
        )
    return arenas


def _tip_dt(tip_time: str) -> datetime:
    return datetime.fromisoformat(tip_time).astimezone(timezone.utc)


def compute_load(
    games: Sequence,
    arenas: Mapping[str, Arena],
) -> Dict[str, TeamLoad]:
    """Compute rest, back-to-back, 3-in-4 and travel for every team/game.

    ``games`` are objects carrying ``game_id``, ``tip_time``, ``home_team``
    and ``away_team`` (the engine's :class:`engine.schema.SlateGame` satisfies
    this).  The result is keyed ``"<game_id>:<team>"``.
    """
    ordered = sorted(games, key=lambda g: _tip_dt(g.tip_time))
    by_team: Dict[str, List] = {}
    for g in ordered:
        by_team.setdefault(g.home_team, []).append(g)
        by_team.setdefault(g.away_team, []).append(g)

    out: Dict[str, TeamLoad] = {}
    for team, team_games in by_team.items():
        for idx, g in enumerate(team_games):
            notes: List[str] = []
            tip = _tip_dt(g.tip_time)
            rest: Optional[float] = None
            back_to_back: Optional[bool] = None
            three_in_four: Optional[bool] = None
            count: Optional[int] = None
            travel: Optional[float] = None
            previous_venue: Optional[str] = None

            if idx > 0:
                prev = team_games[idx - 1]
                prev_tip = _tip_dt(prev.tip_time)
                rest = (tip - prev_tip).total_seconds() / 86400.0
                back_to_back = rest < 1.0
                # The venue the team last played at: its own arena when it was
                # home, the opponent's arena when it was on the road.  In both
                # cases the previous game's home team names that arena.
                previous_venue = prev.home_team
                arena_now = arenas.get(g.home_team if team == g.home_team else g.away_team)
                arena_prev = arenas.get(previous_venue)
                if (
                    arena_now
                    and arena_prev
                    and arena_now.has_coordinates
                    and arena_prev.has_coordinates
                ):
                    travel = haversine_miles(
                        arena_prev.latitude, arena_prev.longitude,
                        arena_now.latitude, arena_now.longitude,
                    )
                else:
                    missing = []
                    if not (arena_now and arena_now.has_coordinates):
                        missing.append(arena_now.team if arena_now else "the current venue")
                    if not (arena_prev and arena_prev.has_coordinates):
                        missing.append(arena_prev.team if arena_prev else previous_venue)
                    notes.append(
                        "travel distance not measured: the arena coordinate for "
                        + " and ".join(missing)
                        + " is not confirmed by an official source"
                    )
            else:
                notes.append("first game in the supplied schedule window: no rest or travel value")

            window_end = tip.timestamp() + 4 * 86400.0
            count = sum(
                1
                for other in team_games
                if tip.timestamp() <= _tip_dt(other.tip_time).timestamp() <= window_end
            )
            three_in_four = count >= 3

            out[f"{g.game_id}:{team}"] = TeamLoad(
                team=team,
                game_id=g.game_id,
                tip_time=g.tip_time,
                rest_days=rest,
                is_back_to_back=back_to_back,
                is_three_in_four=three_in_four,
                games_in_next_four_days=count,
                travel_miles=travel,
                previous_venue=previous_venue,
                notes=tuple(notes),
            )
    return out
