"""Team-strength model and originated spread/total lines.

Method (hypothesis S1/S2 in docs/strategy-framework.md):
  * recency-weighted points-per-possession for and against each team,
  * opponent-independent team strength multiplied through league average,
  * a predictive margin distribution (mean +/- sd), from which the
    model-originated fair spread is derived as the mean margin.

All constants below are UNFITTED engineering defaults documented in
docs/engine.md. They are NOT estimates about the NBA. With no authorized
games in the ledger the model refuses to produce a line.
"""

from __future__ import annotations

import math
from statistics import NormalDist
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .schema import TeamGame

# --- UNFITTED defaults (see docs/engine.md "Parameter register") -------------
HALF_LIFE_DAYS = 30.0          # recency decay half-life
HOME_ADVANTAGE_POINTS = None  # no free intercept; derive from measured home-win rate
MARGIN_SD_DEFAULT = 12.0       # unfitted predictive sd when residuals unavailable
MIN_GAMES_FOR_LINE = 5         # PROPOSED minimum per team before any line
# ---------------------------------------------------------------------------


@dataclass
class TeamStrength:
    team: str
    off_ppp: Optional[float]
    def_ppp: Optional[float]
    games_used: int
    weighted_games: float


@dataclass
class MarginForecast:
    home_team: str
    away_team: str
    expected_home_margin: Optional[float]
    margin_sd: float
    expected_total: Optional[float]
    home_strength: TeamStrength
    away_strength: TeamStrength
    notes: Tuple[str, ...]
    measured_home_win_rate: Optional[float] = None
    home_games_used: int = 0
    home_advantage_points: Optional[float] = None

    @property
    def originated_spread(self) -> Optional[float]:
        """Model-originated fair spread from the home team's perspective."""
        return self.expected_home_margin

    @property
    def originated_total(self) -> Optional[float]:
        return self.expected_total


def _weight(game_date: str, as_of: datetime) -> float:
    game_dt = datetime.fromisoformat(game_date).astimezone(timezone.utc)
    age_days = max((as_of - game_dt).total_seconds() / 86400.0, 0.0)
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def team_strength(
    games: Sequence[TeamGame], team: str, as_of: datetime
) -> TeamStrength:
    w_sum = 0.0
    off_num = 0.0
    def_num = 0.0
    count = 0
    for g in games:
        if g.team != team:
            continue
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue  # never use a game after the forecast timestamp
        w = _weight(g.game_date, as_of)
        if g.possessions is None or g.possessions <= 0:
            continue  # unknown pace stays missing; never substitute a default
        poss = g.possessions
        w_sum += w
        off_num += w * (g.points / poss)
        def_num += w * (g.opp_points / poss)
        count += 1
    if w_sum <= 0:
        return TeamStrength(team, None, None, 0, 0.0)
    return TeamStrength(team, off_num / w_sum, def_num / w_sum, count, w_sum)


def league_average_ppp(games: Sequence[TeamGame], as_of: datetime) -> Optional[float]:
    num = 0.0
    den = 0.0
    for g in games:
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        w = _weight(g.game_date, as_of)
        if g.possessions is None or g.possessions <= 0:
            continue  # unknown pace stays missing; never substitute a default
        poss = g.possessions
        num += w * (g.points / poss)
        den += w
    return num / den if den > 0 else None


def league_average_possessions(games: Sequence[TeamGame], as_of: datetime) -> Optional[float]:
    """Recency-weighted observed possessions; missing values are never imputed."""
    num = 0.0
    den = 0.0
    for g in games:
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        if g.possessions is None or g.possessions <= 0:
            continue
        w = _weight(g.game_date, as_of)
        num += w * g.possessions
        den += w
    return num / den if den > 0 else None


def measured_home_win_rate(games: Sequence[TeamGame], as_of: datetime) -> Tuple[Optional[float], int]:
    """Return the observed pre-as-of home win rate and unique home-game count.

    Each completed game must contribute exactly one home-team row. The function
    excludes future games and rejects duplicate home rows rather than silently
    overweighting duplicated observations.
    """
    outcomes: Dict[str, bool] = {}
    for game in games:
        if not game.is_home:
            continue
        if datetime.fromisoformat(game.game_date).astimezone(timezone.utc) > as_of:
            continue
        if game.game_id in outcomes:
            raise ValueError(f"duplicate home-team result for game_id {game.game_id!r}")
        outcomes[game.game_id] = game.points > game.opp_points
    if not outcomes:
        return None, 0
    return sum(outcomes.values()) / len(outcomes), len(outcomes)


def home_advantage_from_win_rate(rate: float, margin_sd: float) -> float:
    """Map measured home-win frequency to a normal-margin point equivalent.

    This is a deterministic parameterization, not an estimated causal effect:
    it assumes a normal neutral-game margin with the supplied SD. Extreme rates
    (0 or 1) are not clipped; they are rejected because they imply infinity.
    """
    if not math.isfinite(rate) or not 0.0 < rate < 1.0:
        raise ValueError("measured home win rate must be strictly between 0 and 1")
    if not math.isfinite(margin_sd) or margin_sd <= 0:
        raise ValueError("margin_sd must be finite and positive")
    return NormalDist().inv_cdf(rate) * margin_sd


def margin_forecast(
    games: Sequence[TeamGame],
    home_team: str,
    away_team: str,
    as_of: datetime,
) -> MarginForecast:
    notes: List[str] = []
    home = team_strength(games, home_team, as_of)
    away = team_strength(games, away_team, as_of)
    league = league_average_ppp(games, as_of)
    possessions = league_average_possessions(games, as_of)
    home_win_rate, home_games_used = measured_home_win_rate(games, as_of)
    if (
        league is None
        or possessions is None
        or home.off_ppp is None
        or away.off_ppp is None
        or home.games_used < MIN_GAMES_FOR_LINE
        or away.games_used < MIN_GAMES_FOR_LINE
        or home_win_rate is None
        or home_win_rate <= 0.0
        or home_win_rate >= 1.0
    ):
        notes.append(
            "insufficient authorized games for one or both teams "
            f"({home.team}: {home.games_used}, {away.team}: {away.games_used}); "
            "no line originated"
        )
        return MarginForecast(
            home_team, away_team, None, MARGIN_SD_DEFAULT, None, home, away, tuple(notes),
            home_win_rate, home_games_used, None
        )
    # Expected points scored = possessions * (own offense x opponent defense / league)
    poss = possessions
    home_pts = poss * (home.off_ppp * away.def_ppp / league)
    away_pts = poss * (away.off_ppp * home.def_ppp / league)
    home_advantage = home_advantage_from_win_rate(home_win_rate, MARGIN_SD_DEFAULT)
    margin = home_pts - away_pts + home_advantage
    total = home_pts + away_pts
    # Residual spread: use default until calibrated residuals are stored.
    notes.append("margin sd uses UNFITTED default; calibrate on authorized residuals")
    notes.append("home-court point equivalent is derived from measured pre-as-of home-win rate; normal-margin mapping is an unvalidated assumption")
    return MarginForecast(
        home_team, away_team, margin, MARGIN_SD_DEFAULT, total, home, away, tuple(notes),
        home_win_rate, home_games_used, home_advantage
    )


def win_probability(expected_margin: float, margin_sd: float = MARGIN_SD_DEFAULT) -> float:
    """P(home win) under a normal margin approximation."""
    if margin_sd <= 0:
        raise ValueError("margin_sd must be positive")
    z = expected_margin / margin_sd
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def cover_probability(
    expected_margin: float, spread: float, margin_sd: float = MARGIN_SD_DEFAULT
) -> float:
    """P(home margin > spread) under the normal margin approximation.

    'spread' is given from the home team's perspective (e.g. -3.5 means the
    home team is a 3.5-point favourite).
    """
    z = (expected_margin - spread) / margin_sd
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
