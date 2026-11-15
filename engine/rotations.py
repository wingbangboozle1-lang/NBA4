"""Minutes redistribution when a player is out, and the availability column.

Brief items implemented (2026-11-15):

* "Model minutes redistribution explicitly: for each team, the top-8 minutes
  shares and the replacement shares when a player is out."
* "Put rotation availability on the picks page as its own column."

Model. A team has 240 team-minutes in regulation (five players x 48 minutes),
plus five per overtime period. Minutes are a **fixed budget**: when one player's
minutes fall, an equal amount must appear somewhere else. So the model is a
redistribution of a constant, not a rescaling:

    removed_minutes = sum(shortfall of each unavailable player)
    new_share(p)    = old_share(p) + removed_minutes * weight(p) / sum(weights)

``weights`` are caller-supplied replacement weights (coach-behaviour
parameters). They are never defaulted here, because "who absorbs the minutes" is
the empirical question the model has to answer, and a guessed weight would put
the answer in the input. Validity checks: shares must be non-negative, must not
exceed the game length, and a top-8 group must not exceed the team budget.

The published artefacts are deliberately two-step and separately labelled:
(1) the *observation* - minutes shares from an authorised box score; (2) the
*scenario* - the redistribution under a stated weight vector. The injury status
itself comes from ``engine/injurydiff.py``; nothing in this module converts a
status into minutes on its own (that mapping lives in ``engine/injuries.py`` and
is UNVALIDATED).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

REGULATION_TEAM_MINUTES = 240.0   # 5 x 48, arithmetic not an estimate
MINUTES_PER_OVERTIME = 5.0
TOP_N = 8

STATE_UNRESOLVED = "UNRESOLVED"
STATE_RESOLVED = "RESOLVED"


class RotationError(ValueError):
    """Raised when a rotation is internally inconsistent."""


@dataclass(frozen=True)
class PlayerMinutes:
    """One player's minutes in one game window, as observed."""

    player: str
    minutes: float
    games: int = 1

    def validate(self) -> "PlayerMinutes":
        if not self.player:
            raise RotationError("player name required")
        if self.minutes < 0:
            raise RotationError(f"{self.player}: negative minutes")
        if self.games <= 0:
            raise RotationError(f"{self.player}: games must be positive")
        if self.minutes / self.games > 53.0:
            raise RotationError(f"{self.player}: average minutes above the physical ceiling")
        return self

    @property
    def average(self) -> float:
        return self.minutes / self.games


@dataclass(frozen=True)
class TeamRotation:
    """One team's rotation over a window, in per-game average minutes."""

    team: str
    window: str
    players: Tuple[PlayerMinutes, ...]
    game_minutes: float = REGULATION_TEAM_MINUTES
    source_url: str = ""
    source_stamp: str = ""
    verified: bool = False

    def validate(self) -> "TeamRotation":
        if not self.team:
            raise RotationError("team required")
        if self.game_minutes < REGULATION_TEAM_MINUTES:
            raise RotationError("game_minutes cannot be below regulation team minutes")
        total = sum(p.average for p in self.players)
        if total > self.game_minutes + 1e-9:
            raise RotationError(
                f"{self.team}: rotation averages sum to {total:.1f} minutes, above the "
                f"{self.game_minutes:.0f}-minute team budget"
            )
        names = [p.player for p in self.players]
        if len(names) != len(set(names)):
            raise RotationError(f"{self.team}: duplicate player rows")
        return self

    @property
    def top_n(self) -> Tuple[PlayerMinutes, ...]:
        return tuple(sorted(self.players, key=lambda p: -p.average))[:TOP_N]

    def shares(self) -> Dict[str, float]:
        """Share of the team's minutes budget per player."""
        return {p.player: p.average / self.game_minutes for p in self.players}

    def top8_share_sum(self) -> float:
        return sum(p.average for p in self.top_n) / self.game_minutes


def redistribution(
    rotation: TeamRotation,
    out_players: Mapping[str, float],
    replacement_weights: Mapping[str, float],
    label: str = "scenario",
) -> Dict[str, object]:
    """Reallocate the minutes of unavailable players across the stated pool.

    ``out_players`` maps a player to the minutes they *lose* (their full average
    if they are out, part of it if they are limited). ``replacement_weights``
    maps each remaining player to the share of the freed minutes they absorb.
    Weights must be non-negative; they may sum to less than 1, in which case the
    remainder is reported as ``unallocated_minutes`` rather than being silently
    spread - minutes that nobody is declared to absorb are a modelling gap.
    """
    rotation.validate()
    if not out_players:
        raise RotationError("no unavailable players supplied; nothing to redistribute")
    if not replacement_weights:
        raise RotationError(
            "replacement weights are required; the engine will not assume who absorbs minutes"
        )
    known = {p.player: p.average for p in rotation.players}
    freed = 0.0
    removals: Dict[str, float] = {}
    for player, lost in out_players.items():
        if player not in known:
            raise RotationError(f"{player}: not part of this rotation; check the roster source")
        if lost < 0 or lost > known[player]:
            raise RotationError(
                f"{player}: lost minutes {lost} outside the observed range 0..{known[player]}"
            )
        removals[player] = lost
        freed += lost
    total_weight = sum(replacement_weights.values())
    if total_weight <= 0:
        raise RotationError("replacement weights must sum to a positive number")
    if any(w < 0 for w in replacement_weights.values()):
        raise RotationError("replacement weights must be non-negative")
    for player in replacement_weights:
        if player in removals:
            raise RotationError(f"{player}: an unavailable player cannot absorb their own minutes")

    new_average: Dict[str, float] = dict(known)
    for player, lost in removals.items():
        new_average[player] = known[player] - lost
    allocated = 0.0
    added: Dict[str, float] = {}
    scale = 1.0 if total_weight <= 1.0 else total_weight
    for player, weight in replacement_weights.items():
        share = (weight / scale) * freed
        new_average[player] = new_average.get(player, 0.0) + share
        added[player] = share
        allocated += share
    unallocated = freed - allocated
    if any(v < 0 for v in new_average.values()):
        raise RotationError("redistribution produced negative minutes")
    if sum(new_average.values()) > rotation.game_minutes + 1e-6:
        raise RotationError("redistribution exceeds the team minutes budget")

    before_top = rotation.top_n
    after_view = TeamRotation(
        team=rotation.team,
        window=rotation.window,
        players=tuple(PlayerMinutes(name, avg, 1) for name, avg in new_average.items()),
        game_minutes=rotation.game_minutes,
        source_url=rotation.source_url,
        source_stamp=rotation.source_stamp,
        verified=rotation.verified,
    ).validate()
    after_top = after_view.top_n
    return {
        "team": rotation.team,
        "window": rotation.window,
        "label": label,
        "freed_minutes": round(freed, 3),
        "unallocated_minutes": round(unallocated, 3),
        "removed": {k: round(v, 3) for k, v in removals.items()},
        "added": {k: round(v, 3) for k, v in added.items()},
        "top8_before": [(p.player, round(p.average, 2)) for p in before_top],
        "top8_after": [(p.player, round(p.average, 2)) for p in after_top],
        "top8_share_before": round(sum(p.average for p in before_top) / rotation.game_minutes, 4),
        "top8_share_after": round(sum(p.average for p in after_top) / rotation.game_minutes, 4),
        "budget_check": round(sum(new_average.values()), 6),
        "game_minutes": rotation.game_minutes,
        "status": "PROPOSED/UNVALIDATED - a scenario arithmetic of a fixed budget, not a fitted model",
        "source_url": rotation.source_url,
    }


def availability_column(
    rotation: Optional[TeamRotation],
    reported_out: Sequence[str],
    unresolved: Sequence[str],
    max_reported_out: Optional[int] = None,
) -> Dict[str, object]:
    """The rotation-availability column for the picks page.

    The column reports *rotation structure and reporting state*, never a
    probability. ``max_reported_out`` is a registered threshold: when supplied
    and exceeded, the column flags the row as rotation-unstable so a reader sees
    the condition without the site having to publish a number.
    """
    if rotation is None:
        return {
            "text": "UNAVAILABLE - no authorised minutes observation for this team",
            "top8_share": None,
            "reported_out": len(reported_out),
            "unresolved": list(unresolved),
            "flag": "NO_MINUTES_SOURCE",
        }
    rotation.validate()
    known = {p.player for p in rotation.players}
    not_in_rotation = [p for p in reported_out if p not in known]
    over_threshold = (
        max_reported_out is not None and len(reported_out) > int(max_reported_out)
    )
    flag = "ROTATION_UNSTABLE" if over_threshold else ("UNRESOLVED_REPORTS" if unresolved else "OK")
    text = (
        f"top-{TOP_N} holds {rotation.top8_share_sum() * 100:.1f}% of minutes; "
        f"{len(reported_out)} reported out"
        + (f" ({', '.join(sorted(reported_out))})" if reported_out else "")
        + (f"; {len(not_in_rotation)} reported name(s) not in the observed rotation" if not_in_rotation else "")
        + (f"; {len(unresolved)} status(es) unresolved" if unresolved else "")
    )
    return {
        "text": text,
        "top8_share": round(rotation.top8_share_sum(), 4),
        "reported_out": len(reported_out),
        "unresolved": list(unresolved),
        "not_in_rotation": not_in_rotation,
        "rotation_unstable": over_threshold,
        "flag": flag,
        "source_url": rotation.source_url,
    }
