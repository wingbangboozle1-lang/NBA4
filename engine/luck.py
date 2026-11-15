"""Luck accounting: per-team z-scores and a publication gate on luck-leaners.

Brief item implemented (2026-11-15): "Report luck as a z-score per team and
refuse to publish a strategy that leans on a team outside the noise band."

What this can and cannot do, stated plainly:

* Luck here means **record versus expectation**: how far a team's observed wins
  sit from what the model expected, measured in units of the sampling noise of
  that expectation. A large |z| means the record is not explained by the
  expected true ability *plus* ordinary variance, so a strategy whose edge comes
  from that record is carrying an unexplained component.
* It cannot remove randomness from games. It quantifies it. The Ksa's own
  guidance is quoted in ``docs/sources.md`` on precisely this point ("Winning
  or losing is almost always determined by coincidence or chance, not by your
  insight or practice"), which is why the honest control is a refusal rule, not
  a claim of luck removal.
* The z-score is only as good as the expectation fed to it. ``variance`` must
  be supplied by the caller (binomial variance is offered as a helper, not as an
  assumption baked into the gate) and the noise band is a registered policy
  number, never a default.

Refusal semantics: a strategy is refused publication when any team it leans on
has |z| beyond the declared band, when the band is unregistered, or when the
team's expectation is itself unmeasured. Failure is the default state.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

BAND_UNSET = "BAND_UNSET"


class LuckError(ValueError):
    """Raised on inconsistent inputs to the luck computation."""


@dataclass(frozen=True)
class TeamLuck:
    """One team's luck z-score for one window."""

    team: str
    window: str
    games: int
    observed_wins: Optional[float]
    expected_wins: Optional[float]
    variance: Optional[float]
    z: Optional[float]
    band: str
    source_url: str
    note: str = ""

    @property
    def measured(self) -> bool:
        return self.z is not None

    @property
    def outside_noise_band(self) -> Optional[bool]:
        if self.z is None or self.band == BAND_UNSET:
            return None
        return self.band != "INSIDE"


def binomial_variance(games: int, win_probability: float) -> float:
    """Variance of a win total under independent games at a fixed probability.

    Offered as a helper because it is the reference distribution the gate needs
    most often; using it is a modelling choice the caller makes explicitly, and
    it understates variance when game outcomes are correlated (rest, travel,
    roster availability), which is why ``LuckPolicy.correlated_inflation``
    exists.
    """
    if games <= 0:
        raise LuckError("games must be positive")
    if not 0.0 < win_probability < 1.0:
        raise LuckError("win_probability must lie strictly between 0 and 1")
    return games * win_probability * (1.0 - win_probability)


@dataclass(frozen=True)
class LuckPolicy:
    """The registered noise-band policy for one leaderboard cycle."""

    z_threshold: Optional[float]
    alpha: Optional[float]
    correlated_inflation: Optional[float]
    registered_by: str
    registered_at: Optional[str]

    @property
    def registered(self) -> bool:
        return (
            self.z_threshold is not None
            and self.alpha is not None
            and self.correlated_inflation is not None
            and self.correlated_inflation >= 1.0
            and bool(self.registered_at)
        )

    def band_for(self, z: Optional[float]) -> str:
        if not self.registered or z is None:
            return BAND_UNSET
        return "INSIDE" if abs(z) <= float(self.z_threshold) else "OUTSIDE"


def team_luck(
    team: str,
    window: str,
    games: int,
    observed_wins: Optional[float],
    expected_wins: Optional[float],
    variance: Optional[float],
    policy: LuckPolicy,
    source_url: str,
) -> TeamLuck:
    """z = (observed - expected) / sqrt(variance), with the band applied."""
    if observed_wins is None or expected_wins is None or variance is None or variance <= 0:
        return TeamLuck(
            team, window, games, observed_wins, expected_wins, variance, None, BAND_UNSET,
            source_url,
            "unmeasured: an expectation and a variance must both come from an authorised "
            "source; no z-score is published without them",
        )
    if not source_url.startswith("https://"):
        raise LuckError(f"{team}: the win total needs an https official source URL")
    z = (observed_wins - expected_wins) / math.sqrt(variance)
    return TeamLuck(
        team, window, games, observed_wins, expected_wins, variance, z,
        policy.band_for(z), source_url,
        "z is a record-versus-expectation statistic, not a statement about the team's quality",
    )


@dataclass(frozen=True)
class LuckGate:
    """The publish/refuse decision for one strategy."""

    strategy_id: str
    publish: bool
    code: str
    detail: str
    offenders: Tuple[str, ...] = ()
    unmeasured: Tuple[str, ...] = ()


def strategy_luck_gate(
    strategy_id: str,
    leaned_on_teams: Sequence[str],
    luck_by_team: Mapping[str, TeamLuck],
    policy: LuckPolicy,
) -> LuckGate:
    """Refuse publication when the strategy leans on a team outside the band."""
    if not leaned_on_teams:
        return LuckGate(
            strategy_id, False, "UNDECLARED_UNIVERSE",
            "a strategy must declare the teams it leans on; an undeclared "
            "lean cannot be checked against the noise band",
        )
    if not policy.registered:
        return LuckGate(
            strategy_id, False, BAND_UNSET,
            "no noise band is registered (z threshold, alpha and the correlated-outcome "
            "inflation must all be declared before any strategy is published)",
            (), tuple(leaned_on_teams),
        )
    offenders: List[str] = []
    unmeasured: List[str] = []
    for team in leaned_on_teams:
        luck = luck_by_team.get(team)
        if luck is None:
            unmeasured.append(team)
            continue
        if not luck.measured:
            unmeasured.append(team)
            continue
        if luck.outside_noise_band:
            offenders.append(team)
    if unmeasured:
        return LuckGate(
            strategy_id, False, "LUCK_UNMEASURED",
            "no measured z-score for: " + ", ".join(unmeasured)
            + " - a strategy whose lean cannot be checked is not published",
            (), tuple(unmeasured),
        )
    if offenders:
        return LuckGate(
            strategy_id, False, "LUCK_LEAN_OUTSIDE_BAND",
            "leans on team(s) with |z| beyond the registered band: " + ", ".join(offenders)
            + f" (threshold {policy.z_threshold})",
            tuple(offenders), (),
        )
    return LuckGate(
        strategy_id, True, "BAND_CLEAN",
        f"every leaned-on team sits inside the noise band at |z| <= {policy.z_threshold}; "
        "this clears the luck check only - the rights, leakage, calibration and sample gates "
        "are separate and still apply",
    )


def luck_table_rows(luck_by_team: Mapping[str, TeamLuck]) -> List[Dict[str, str]]:
    """Rows for the leaderboard page: team, record, expectation, z, band, source."""
    rows: List[Dict[str, str]] = []
    for team in sorted(luck_by_team):
        luck = luck_by_team[team]
        rows.append(
            {
                "team": team,
                "window": luck.window,
                "games": str(luck.games),
                "observed_wins": "" if luck.observed_wins is None else f"{luck.observed_wins:g}",
                "expected_wins": "" if luck.expected_wins is None else f"{luck.expected_wins:.2f}",
                "z": "" if luck.z is None else f"{luck.z:+.2f}",
                "band": luck.band,
                "source_url": luck.source_url,
            }
        )
    return rows
