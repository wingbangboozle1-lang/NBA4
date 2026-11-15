"""Minutes redistribution when a player is out.

The brief asks for an explicit rotation model: for each team, the top-eight
minutes shares and the replacement shares when a player is out.  This module
makes that arithmetic explicit and auditable:

* :func:`top_eight_shares` returns the rotation that carries the minutes,
  with the share of every player;
* :func:`redistribute_when_out` removes one player and states exactly how
  their minutes are re-allocated, under a declared redistribution rule.

Every share is computed from the minutes that were supplied.  Nothing is
assumed about how deep a bench is, and no production value is derived here -
minutes only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "TOP_EIGHT",
    "REDISTRIBUTION_METHODS",
    "PlayerShare",
    "Rotation",
    "minutes_shares",
    "top_eight_shares",
    "build_rotation",
    "redistribute_when_out",
]

TOP_EIGHT = 8
"""The size of the rotation the brief asks to be stated explicitly."""

REDISTRIBUTION_METHODS = ("equal", "proportional")
"""Declared re-allocation rules for the minutes of an absent player."""


@dataclass
class PlayerShare:
    """One player's share of a team's minutes."""

    player: str
    minutes: float
    share: float

    def as_row(self) -> Tuple[str, float, float]:
        return (self.player, self.minutes, self.share)


@dataclass
class Rotation:
    """A team's rotation: the top eight and the replacement pool."""

    team: str
    top: Tuple[PlayerShare, ...]
    replacements: Tuple[PlayerShare, ...]
    total_minutes: float
    games_used: int
    notes: Tuple[str, ...] = ()

    @property
    def is_measurable(self) -> bool:
        return self.total_minutes > 0

    def share_of(self, player: str) -> Optional[float]:
        for entry in list(self.top) + list(self.replacements):
            if entry.player == player:
                return entry.share
        return None

    def minutes_of(self, player: str) -> Optional[float]:
        for entry in list(self.top) + list(self.replacements):
            if entry.player == player:
                return entry.minutes
        return None


def minutes_shares(
    minutes_by_player: Mapping[str, float]
) -> Tuple[PlayerShare, ...]:
    """Convert a minutes map into shares, largest share first.

    A player with no minutes is omitted rather than given a zero share, so
    the returned shares always sum to one over the players who actually
    played.
    """
    total = sum(max(0.0, float(m)) for m in minutes_by_player.values())
    if total <= 0:
        return ()
    shares: List[PlayerShare] = []
    for player, minutes in minutes_by_player.items():
        m = max(0.0, float(minutes))
        if m <= 0:
            continue
        shares.append(PlayerShare(player, m, m / total))
    shares.sort(key=lambda s: (-s.minutes, s.player))
    return tuple(shares)


def top_eight_shares(
    minutes_by_player: Mapping[str, float]
) -> Tuple[Tuple[PlayerShare, ...], Tuple[PlayerShare, ...]]:
    """Split a minutes map into the top eight and the replacement pool."""
    shares = minutes_shares(minutes_by_player)
    return tuple(shares[:TOP_EIGHT]), tuple(shares[TOP_EIGHT:])


def build_rotation(
    team: str,
    minutes_by_player: Mapping[str, float],
    games_used: int = 0,
    notes: Sequence[str] = (),
) -> Rotation:
    """Build the rotation record for one team."""
    top, replacements = top_eight_shares(minutes_by_player)
    total = sum(m for m in minutes_by_player.values() if m > 0)
    all_notes = list(notes)
    if total <= 0:
        all_notes.append("no minutes supplied; the rotation is not measurable")
    if len(top) < TOP_EIGHT:
        all_notes.append(
            f"only {len(top)} players share minutes; the top-eight rotation is "
            "shorter than eight and the remainder is the replacement pool"
        )
    return Rotation(team, top, replacements, total, games_used, tuple(all_notes))


def redistribute_when_out(
    rotation: Rotation,
    out_player: str,
    method: str = "equal",
    max_share: Optional[float] = None,
) -> Dict[str, object]:
    """State the replacement shares when one player is out.

    ``method``:

    * ``"equal"`` - the absent player's minutes are split equally across the
      replacement pool;
    * ``"proportional"`` - they are split in proportion to the replacement
      players' current shares.

    ``max_share`` optionally caps any single player's resulting share; the
    overflow is redistributed over the remaining recipients.  The result
    always reports the minutes added to each replacement player and the
    remaining share that could not be placed (if a cap makes that happen).

    Nothing here is a forecast of production; it is the arithmetic of where
    minutes go.
    """
    if method not in REDISTRIBUTION_METHODS:
        raise ValueError(f"method must be one of {REDISTRIBUTION_METHODS}")
    if not rotation.is_measurable:
        return {
            "team": rotation.team,
            "out_player": out_player,
            "measurable": False,
            "shares": (),
            "minutes_added": (),
            "unplaced_minutes": 0.0,
            "notes": ("rotation has no measurable minutes",),
        }

    share = rotation.share_of(out_player)
    minutes = rotation.minutes_of(out_player)
    if share is None or minutes is None:
        return {
            "team": rotation.team,
            "out_player": out_player,
            "measurable": False,
            "shares": (),
            "minutes_added": (),
            "unplaced_minutes": 0.0,
            "notes": (f"{out_player} is not in the supplied rotation",),
        }

    pool = list(rotation.replacements)
    notes = [
        f"{out_player} holds {share:.4f} of the team's minutes "
        f"({minutes:.1f} minutes); it is redistributed to "
        f"{len(pool)} replacement player(s) by the '{method}' rule"
    ]
    if not pool:
        return {
            "team": rotation.team,
            "out_player": out_player,
            "measurable": False,
            "shares": (),
            "minutes_added": (),
            "unplaced_minutes": minutes,
            "notes": tuple(
                notes
                + [
                    "no replacement player is available in the supplied minutes, "
                    "so the minutes are unplaced",
                ]
            ),
        }

    if method == "equal":
        weights = [1.0 / len(pool)] * len(pool)
    else:
        pool_total = sum(p.share for p in pool)
        if pool_total <= 0:
            weights = [1.0 / len(pool)] * len(pool)
        else:
            weights = [p.share / pool_total for p in pool]

    added_minutes: List[float] = []
    for p, w in zip(pool, weights):
        added_minutes.append(minutes * w)

    # Cap each recipient's resulting share; any overflow moves to the
    # recipients that still have room, and whatever cannot be placed stays
    # explicitly unplaced.  The invariant
    # sum(minutes_added) + unplaced_minutes == the absent player's minutes
    # holds at every step.
    unplaced = 0.0
    if max_share is not None:
        if not 0 < max_share <= 1:
            raise ValueError("max_share must be in (0, 1]")
        eps = 1e-12
        for _ in range(len(pool) + 1):
            over = [
                i
                for i, p in enumerate(pool)
                if p.share + added_minutes[i] / rotation.total_minutes > max_share + eps
            ]
            if not over:
                break
            overflow = 0.0
            for i in over:
                room = max(0.0, max_share - pool[i].share)
                cap_minutes = room * rotation.total_minutes
                spill = added_minutes[i] - cap_minutes
                added_minutes[i] = cap_minutes
                overflow += spill
            if overflow <= eps:
                break
            free = [
                i
                for i, p in enumerate(pool)
                if p.share + added_minutes[i] / rotation.total_minutes < max_share - eps
            ]
            free_room = sum(
                max(
                    0.0,
                    max_share - pool[i].share - added_minutes[i] / rotation.total_minutes,
                )
                for i in free
            )
            if not free or free_room <= eps:
                unplaced += overflow
                break
            for i in free:
                room = max(
                    0.0,
                    max_share - pool[i].share - added_minutes[i] / rotation.total_minutes,
                )
                give = overflow * (room / free_room)
                added_minutes[i] += give
                overflow -= give
            unplaced += overflow

    new_shares: List[PlayerShare] = []
    for p, added in zip(pool, added_minutes):
        new_shares.append(
            PlayerShare(p.player, p.minutes, p.share + added / rotation.total_minutes)
        )
    new_shares.sort(key=lambda s: (-s.share, s.player))

    if unplaced > 1e-9:
        notes.append(
            f"{unplaced:.3f} minutes could not be placed under the "
            f"{max_share} share cap and stay unplaced"
        )
    return {
        "team": rotation.team,
        "out_player": out_player,
        "measurable": True,
        "method": method,
        "out_player_share": share,
        "out_player_minutes": minutes,
        "shares": tuple(new_shares),
        "minutes_added": tuple(
            (p.player, added) for p, added in zip(pool, added_minutes)
        ),
        "unplaced_minutes": unplaced,
        "notes": tuple(notes),
    }
