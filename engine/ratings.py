"""Team-strength model and originated spread/total lines.

Method (hypothesis S1/S2 in docs/strategy-framework.md):
  * recency-weighted points-per-possession for and against each team,
  * opponent-independent team strength multiplied through league average,
  * a predictive margin distribution (mean +/- sd), from which the
  model-originated fair spread is derived as the mean margin.

Two properties the project brief requires are enforced here:

* **Home-court advantage is pinned, not fitted.**  The home edge is derived
  from the *measured home-win rate* (see
  :func:`engine.estimators.implied_home_advantage_points`) and is applied
  exactly once: it neutralises the home games in the historical PPP ratings
  and is then restored for the forecast.  It is never a free parameter.
* **The total is possessions x points-per-possession.**  It is not an
  average of two team scoring averages.

All constants below are UNFITTED engineering defaults documented in
docs/engine.md. They are NOT estimates about the NBA. With no authorized
games in the ledger the model refuses to produce a line.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .estimators import home_win_rate_from_rows, implied_home_advantage_points
from .schema import TeamGame

# --- UNFITTED defaults (see docs/engine.md "Parameter register") -------------
HALF_LIFE_DAYS = 30.0          # recency decay half-life
DEFAULT_POSSESSIONS = 100.0    # neutral per-game possessions if feed lacks pace
HOME_ADVANTAGE_POINTS = 0.0    # unfitted; superseded by the pinned constant
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
    notes: Tuple[str, ...] = ()

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
    """Recency-weighted points per possession for and against a team."""
    w_sum = 0.0
    off_num = 0.0
    def_num = 0.0
    poss_num = 0.0
    count = 0
    for g in games:
        if g.team != team:
            continue
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue  # never use a game after the forecast timestamp
        w = _weight(g.game_date, as_of)
        poss = g.possessions if g.possessions and g.possessions > 0 else DEFAULT_POSSESSIONS
        w_sum += w
        off_num += w * (g.points / poss)
        def_num += w * (g.opp_points / poss)
        poss_num += w * poss
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
        poss = g.possessions if g.possessions and g.possessions > 0 else DEFAULT_POSSESSIONS
        num += w * (g.points / poss)
        den += w
    return num / den if den > 0 else None


def measured_pace(games: Sequence[TeamGame], as_of: datetime) -> Optional[float]:
    """Weighted mean possessions per game from the authorised rows.

    The total is modelled as this pace multiplied by points per possession,
    so the pace has to be measured rather than assumed.
    """
    num = 0.0
    den = 0.0
    for g in games:
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        poss = g.possessions if g.possessions and g.possessions > 0 else None
        if poss is None:
            continue
        w = _weight(g.game_date, as_of)
        num += w * poss
        den += w
    return num / den if den > 0 else None


def pinned_home_advantage(
    games: Sequence[TeamGame],
    as_of: datetime,
    margin_sd: float = MARGIN_SD_DEFAULT,
) -> Tuple[Optional[float], Optional[float], Optional[float], Tuple[str, ...]]:
    """The home-court constant, pinned to the measured home-win rate.

    Returns ``(value, low, high, notes)``.  ``value`` is ``None`` when the
    rate could not be measured, in which case no line is produced at all -
    the constant is never assumed.
    """
    rate, n_home = home_win_rate_from_rows(games, as_of=as_of)
    if rate is None:
        return None, None, None, (
            "no home game is available in the authorised rows, so the "
            "home-court advantage cannot be pinned to a measured home-win rate",
        )
    return implied_home_advantage_points(rate, margin_sd, n_home_games=n_home)


def neutral_ppp_strength(
    games: Sequence[TeamGame],
    team: str,
    as_of: datetime,
    home_advantage_points: float,
) -> Tuple[Optional[float], Optional[float], int]:
    """Home-neutral points per possession for and against a team.

    Home games are adjusted by the pinned home-court constant so that the
    rating is a *neutral-court* strength; the constant is added back once,
    for the forecast, and therefore is not double counted.
    """
    w_sum = 0.0
    off_num = 0.0
    def_num = 0.0
    count = 0
    for g in games:
        if g.team != team:
            continue
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        poss = g.possessions if g.possessions and g.possessions > 0 else DEFAULT_POSSESSIONS
        w = _weight(g.game_date, as_of)
        adj = home_advantage_points if g.is_home else 0.0
        w_sum += w
        off_num += w * ((g.points - adj) / poss)
        def_num += w * ((g.opp_points - adj) / poss)
        count += 1
    if w_sum <= 0:
        return None, None, 0
    return off_num / w_sum, def_num / w_sum, count


def margin_forecast(
    games: Sequence[TeamGame],
    home_team: str,
    away_team: str,
    as_of: datetime,
    home_advantage: Optional[float] = None,
    margin_sd: float = MARGIN_SD_DEFAULT,
) -> MarginForecast:
    """Originate a spread and a total for one matchup.

    ``home_advantage=None`` (the default) means the constant is **pinned to
    the measured home-win rate** of the supplied authorised rows.  Supplying
    a number overrides it, and the forecast then records that the caller
    supplied the constant rather than the measurement.
    """
    notes: List[str] = []
    rate, n_home = home_win_rate_from_rows(games, as_of=as_of)
    if home_advantage is None:
        hca, hca_low, hca_high, hca_notes = implied_home_advantage_points(
            rate, margin_sd, n_home_games=n_home
        )
        notes.extend(hca_notes)
        if hca is None:
            notes.append(
                "no line is originated: the home-court constant could not be "
                "pinned to a measured home-win rate"
            )
            return MarginForecast(
                home_team, away_team, None, margin_sd, None,
                TeamStrength(home_team, None, None, 0, 0.0),
                TeamStrength(away_team, None, None, 0, 0.0),
                tuple(notes),
            )
        notes.append(
            f"the pinned home-court constant is {hca:.2f} points "
            f"(measured home-win rate {rate:.4f} over {n_home} home game(s))"
        )
    else:
        hca = home_advantage
        notes.append(
            "the home-court constant was supplied by the caller; it is not the "
            "measured home-win-rate constant"
        )

    home = team_strength(games, home_team, as_of)
    away = team_strength(games, away_team, as_of)
    league = league_average_ppp(games, as_of)
    h_off, h_def, h_games = neutral_ppp_strength(games, home_team, as_of, hca)
    a_off, a_def, a_games = neutral_ppp_strength(games, away_team, as_of, hca)
    if (
        league is None
        or h_off is None
        or a_off is None
        or h_games < MIN_GAMES_FOR_LINE
        or a_games < MIN_GAMES_FOR_LINE
    ):
        notes.append(
            "insufficient authorized games for one or both teams "
            f"({home_team}: {h_games}, {away_team}: {a_games}); "
            "no line originated"
        )
        return MarginForecast(
            home_team, away_team, None, margin_sd, None, home, away, tuple(notes)
        )

    poss = measured_pace(games, as_of) or DEFAULT_POSSESSIONS
    # Expected points = possessions x points per possession.
    home_pts = poss * (h_off * a_def / league)
    away_pts = poss * (a_off * h_def / league)
    margin = home_pts - away_pts + hca
    total = home_pts + away_pts
    notes.append(
        f"the total is {poss:.2f} possessions x points per possession, not an "
        "average of the two teams' scoring averages"
    )
    notes.append(
        "margin sd uses UNFITTED default; calibrate on authorized residuals"
    )
    return MarginForecast(
        home_team, away_team, margin, margin_sd, total, home, away, tuple(notes)
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
