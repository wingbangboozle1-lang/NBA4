"""Independent margin estimators and disagreement-first reporting.

These are research implementations, not trained or production-eligible models.
Both receive the same pre-as-of authorized ledger and measured home-win-rate
anchor, but estimate team strength differently: (1) matchup PPP against the
opponent's defense and (2) the difference in historical team point-differential
means, halved as a simple pairwise-strength baseline. The disagreement is the
primary signal; the arithmetic average is secondary and is never called a
confidence probability.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple

from .ratings import (
    MARGIN_SD_DEFAULT,
    MIN_GAMES_FOR_LINE,
    MarginForecast,
    margin_forecast,
    measured_home_win_rate,
)
from .schema import TeamGame


@dataclass(frozen=True)
class EstimatorComparison:
    home_team: str
    away_team: str
    estimator_a_matchup_ppp: Optional[float]
    estimator_b_point_differential: Optional[float]
    disagreement_points: Optional[float]
    blended_margin_secondary: Optional[float]
    measured_home_win_rate: Optional[float]
    home_games_used: int
    notes: Tuple[str, ...]

    @property
    def primary_confidence_signal(self) -> Optional[float]:
        """Absolute estimator disagreement in points; smaller means agreement."""
        return self.disagreement_points


def _team_margin_mean(games: Sequence[TeamGame], team: str, as_of: datetime) -> tuple[Optional[float], int]:
    rows = [g for g in games
            if g.team == team and datetime.fromisoformat(g.game_date).astimezone(timezone.utc) <= as_of]
    if not rows:
        return None, 0
    return sum(g.points - g.opp_points for g in rows) / len(rows), len(rows)


def compare_estimators(
    games: Sequence[TeamGame], home_team: str, away_team: str, as_of: datetime
) -> EstimatorComparison:
    """Compute two margins, primary disagreement and secondary arithmetic mean.

    Missing data, too few games, or an unmeasurable empirical home-rate anchor
    leaves all headline outputs blank. No fallback or fabricated value is used.
    """
    a: MarginForecast = margin_forecast(games, home_team, away_team, as_of)
    home_mean, home_n = _team_margin_mean(games, home_team, as_of)
    away_mean, away_n = _team_margin_mean(games, away_team, as_of)
    rate, home_n_games = measured_home_win_rate(games, as_of)
    notes = list(a.notes)
    b: Optional[float] = None
    if home_mean is None or away_mean is None or home_n < MIN_GAMES_FOR_LINE or away_n < MIN_GAMES_FOR_LINE:
        notes.append("point-differential estimator lacks the proposed minimum games")
    elif rate is None or rate <= 0.0 or rate >= 1.0:
        notes.append("point-differential estimator suppressed: measured home-win rate cannot be mapped to finite points")
    else:
        # The baseline's pairwise strength approximation is deliberately simple
        # and is to be tested, not treated as a fitted NBA estimate.
        from .ratings import home_advantage_from_win_rate
        b = 0.5 * (home_mean - away_mean) + home_advantage_from_win_rate(rate, MARGIN_SD_DEFAULT)
    margins = [x for x in (a.expected_home_margin, b) if x is not None]
    if len(margins) != 2:
        return EstimatorComparison(
            home_team, away_team, a.expected_home_margin, b, None, None,
            rate, home_n_games, tuple(notes),
        )
    return EstimatorComparison(
        home_team, away_team, a.expected_home_margin, b,
        abs(margins[0] - margins[1]), sum(margins) / 2.0,
        rate, home_n_games, tuple(notes),
    )
