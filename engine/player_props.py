"""Player-prop distributions (hypothesis S3 in docs/strategy-framework.md).

Method: minutes distribution x conditional per-minute production, with
empirical-Bayes shrinkage of per-minute rates toward a population baseline.
Injury availability enters only through engine.injuries scenario multipliers,
never as a direct production adjustment.

All prior weights and clamps are UNFITTED/PROPOSED defaults (docs/engine.md).
A prop line is never produced from fewer than MIN_GAMES_FOR_PROP authorized
player games.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from .schema import PlayerGame

# --- UNFITTED / PROPOSED defaults ------------------------------------------
PRIOR_WEIGHT_GAMES = 8.0     # shrinkage prior strength, in equivalent games
MINUTES_CLAMP = (0.0, 48.0)  # regulation ceiling; OT handled separately
MIN_GAMES_FOR_PROP = 5       # PROPOSED minimum before any prop forecast
PROP_SD_PER_MIN_DEFAULT = 0.35  # UNFITTED production sd per minute
# ---------------------------------------------------------------------------


@dataclass
class PlayerRate:
    player: str
    minutes_mean: Optional[float]
    pts_per_min: Optional[float]
    reb_per_min: Optional[float]
    ast_per_min: Optional[float]
    games_used: int


@dataclass
class PropForecast:
    player: str
    stat: str  # "points" | "rebounds" | "assists"
    expected_value: Optional[float]
    sd: float
    minutes_mean: Optional[float]
    games_used: int
    notes: Tuple[str, ...]

    def over_probability(self, line: float) -> Optional[float]:
        if self.expected_value is None:
            return None
        z = (self.expected_value - line) / self.sd if self.sd > 0 else 0.0
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _weighted_rate(
    games: Sequence[PlayerGame],
    player: str,
    stat: str,
    population_rate: float,
    as_of,
) -> Tuple[Optional[float], int]:
    from datetime import datetime, timezone

    num = 0.0
    den = 0.0
    count = 0
    for g in games:
        if g.player != player:
            continue
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        value = {"points": g.points, "rebounds": g.rebounds, "assists": g.assists}[stat]
        num += value
        den += max(g.minutes, 1e-6)
        count += 1
    if count == 0:
        return None, 0
    raw_rate = num / den if den > 0 else 0.0
    # Shrink toward the population rate with PRIOR_WEIGHT_GAMES worth of
    # minutes at roughly 30 minutes per game.
    prior_minutes = PRIOR_WEIGHT_GAMES * 30.0
    shrunk = (num + population_rate * prior_minutes) / (den + prior_minutes)
    return shrunk, count


def player_prop_forecast(
    games: Sequence[PlayerGame],
    player: str,
    stat: str,
    population_rate_per_min: float,
    as_of,
    availability_multiplier: float = 1.0,
) -> PropForecast:
    """Forecast a per-game prop distribution for one player/stat.

    availability_multiplier comes from engine.injuries scenarios and is
    applied to expected minutes only. It is an UNVALIDATED scenario input,
    not an injury-impact estimate.
    """
    notes = []
    minutes_sum = 0.0
    minutes_n = 0
    for g in games:
        if g.player != player:
            continue
        from datetime import datetime, timezone

        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        minutes_sum += g.minutes
        minutes_n += 1
    rate, used = _weighted_rate(games, player, stat, population_rate_per_min, as_of)
    if minutes_n == 0 or rate is None:
        return PropForecast(
            player, stat, None, PROP_SD_PER_MIN_DEFAULT * 30.0, None, 0,
            ("no authorized player games; no prop forecast",),
        )
    minutes_mean = min(max(minutes_sum / minutes_n, MINUTES_CLAMP[0]), MINUTES_CLAMP[1])
    minutes_mean = minutes_mean * availability_multiplier
    if used < MIN_GAMES_FOR_PROP:
        notes.append(
            f"only {used} authorized games; below proposed minimum {MIN_GAMES_FOR_PROP}"
        )
        return PropForecast(
            player, stat, None, PROP_SD_PER_MIN_DEFAULT * minutes_mean, minutes_mean,
            used, tuple(notes),
        )
    expected = rate * minutes_mean
    sd = PROP_SD_PER_MIN_DEFAULT * math.sqrt(max(minutes_mean, 1.0))
    notes.append("rate shrank toward population baseline (prior weight is UNFITTED)")
    return PropForecast(player, stat, expected, sd, minutes_mean, used, tuple(notes))
