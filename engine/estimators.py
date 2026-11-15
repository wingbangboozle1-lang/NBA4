"""Two independent estimators and their disagreement.

The brief requires that the site stops publishing a single blended rating as
the headline and publishes the **disagreement between two estimators** as the
headline signal instead, with the blend printed underneath.  That is only
meaningful if the two estimators are genuinely independent, so this module
keeps them independent by construction:

* ``PppEstimator`` uses **scores**: recency-weighted offensive and defensive
  points per possession, scaled by the measured pace of the matchup.  It
  never looks at whether a team won.
* ``OutcomeEstimator`` uses **results only**: a chronological Elo-style
  rating updated from win/loss outcomes.  It never looks at how many points
  were scored.

A shared input that both estimators use is the *home-court advantage*, and it
is **pinned to the measured home-win rate** instead of being fitted freely
(see :func:`measured_home_win_rate` and
:func:`implied_home_advantage_points`).

Every function here is pure and offline.  No NBA or market value is embedded
here; the caller supplies authorised game records.  A result that cannot be
computed is returned as ``None`` with a note - never as a default number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import NormalDist
from typing import Dict, List, Optional, Sequence, Tuple

from .schema import TeamGame

__all__ = [
    "EstimatorOutput",
    "Disagreement",
    "Pair",
    "pair_games",
    "measured_home_win_rate",
    "home_win_rate_interval",
    "implied_home_advantage_points",
    "PppEstimator",
    "OutcomeEstimator",
    "disagreement",
    "blend_estimators",
]

# --- PROPOSED / UNFITTED engineering defaults (docs/engine.md) ---------------
# The recency half-life and the Elo constants are model choices that must be
# re-estimated on authorised data before any value is published.  They are
# listed here so the method is explicit, not because they are fitted.
HALF_LIFE_DAYS = 30.0
ELO_SCALE = 400.0
ELO_K_FACTOR = 20.0
MIN_GAMES_FOR_ESTIMATE = 5
# ---------------------------------------------------------------------------

_STD_NORMAL = NormalDist()


@dataclass
class Pair:
    """One completed game reduced to the facts both estimators may use."""

    game_id: str
    game_date: str
    home_team: str
    away_team: str
    home_points: float
    away_points: float

    @property
    def home_won(self) -> bool:
        return self.home_points > self.away_points

    @property
    def margin(self) -> float:
        return self.home_points - self.away_points


@dataclass
class EstimatorOutput:
    """One estimator's answer for one matchup."""

    name: str
    expected_home_margin: Optional[float]
    home_win_probability: Optional[float]
    margin_sd: float
    games_used: int
    notes: Tuple[str, ...] = ()


@dataclass
class Disagreement:
    """The published headline: how far apart the two estimators are."""

    margin_gap: Optional[float]
    probability_gap: Optional[float]
    z_score: Optional[float]
    sd_gap: Optional[float]
    estimator_a: EstimatorOutput
    estimator_b: EstimatorOutput
    notes: Tuple[str, ...] = ()

    @property
    def is_measurable(self) -> bool:
        return self.margin_gap is not None

    @property
    def headline(self) -> str:
        """Short label used as the published headline for this matchup."""
        if self.margin_gap is None:
            return "Disagreement not measurable"
        if self.z_score is None:
            return f"Estimator gap {self.margin_gap:+.2f} pts (sd not measured)"
        return f"Estimator gap {self.margin_gap:+.2f} pts (z = {self.z_score:+.2f})"


def pair_games(games: Sequence[TeamGame]) -> List[Pair]:
    """Reduce team-level game rows to one row per game, home team first.

    The ledger stores one row per team per game.  A game is identified by its
    ``game_id``; the row whose ``is_home`` flag is set supplies the home
    points.  Games with a missing or duplicate home row are dropped and
    reported by the caller's notes rather than guessed.
    """
    by_id: Dict[str, Dict[str, TeamGame]] = {}
    for g in games:
        by_id.setdefault(g.game_id, {})[g.team] = g
    pairs: List[Pair] = []
    for game_id, rows in by_id.items():
        home = next((r for r in rows.values() if r.is_home), None)
        away = next((r for r in rows.values() if not r.is_home), None)
        if home is None or away is None:
            continue
        pairs.append(
            Pair(
                game_id=game_id,
                game_date=home.game_date,
                home_team=home.team,
                away_team=away.team,
                home_points=float(home.points),
                away_points=float(away.points),
            )
        )
    pairs.sort(key=lambda p: p.game_date)
    return pairs


def measured_home_win_rate(pairs: Sequence[Pair]) -> Optional[float]:
    """The measured home-win rate, used to pin home-court advantage.

    Returns ``None`` when there are no completed games: the rate is never
    replaced by a league-average assumption.
    """
    if not pairs:
        return None
    wins = sum(1 for p in pairs if p.home_won)
    return wins / len(pairs)


def home_win_rate_from_rows(
    games: Sequence[TeamGame], as_of: Optional[datetime] = None
) -> Tuple[Optional[float], int]:
    """The measured home-win rate straight from the ledger rows.

    The ledger stores one row per team per game.  A row flagged ``is_home``
    is a home game for that team, so the home-win rate is the share of
    those rows the home team won.  Games after ``as_of`` are ignored, so a
    forecast never sees a result it could not have known.

    Returns ``(rate, number_of_home_games)``; ``rate`` is ``None`` when no
    home game is available.
    """
    wins = 0
    total = 0
    for g in games:
        if not g.is_home:
            continue
        if as_of is not None:
            if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
                continue
        total += 1
        if g.points > g.opp_points:
            wins += 1
    if total == 0:
        return None, 0
    return wins / total, total


def home_win_rate_interval(
    home_win_rate: float, n_home_games: int, z: float = 1.959963984540054
) -> Tuple[float, float]:
    """Wilson score interval for a measured proportion.

    The interval is what makes the pinned home-court constant honest: the
    published value carries the sampling error of the measurement rather than
    pretending the rate is known exactly.
    """
    if n_home_games <= 0:
        raise ValueError("n_home_games must be positive")
    p = min(max(home_win_rate, 0.0), 1.0)
    n = float(n_home_games)
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)


def implied_home_advantage_points(
    home_win_rate: Optional[float],
    margin_sd: float,
    n_home_games: int = 0,
) -> Tuple[Optional[float], Optional[float], Optional[float], Tuple[str, ...]]:
    """Pin home-court advantage (in points) to the measured home-win rate.

    Under the normal margin model used by :mod:`engine.ratings`, a home edge
    of ``H`` points produces a home win probability ``Phi(H / sd)``.  Solving
    for ``H`` at the measured home-win rate gives the pinned constant.

    Returns ``(value, low, high, notes)``.  ``value`` is ``None`` when the
    rate was not measured.  ``low``/``high`` are the Wilson-interval bounds
    propagated through the same transform, or ``None`` when the sample size
    is not supplied.
    """
    notes: List[str] = []
    if home_win_rate is None:
        return None, None, None, (
            "home-win rate not measured; home-court advantage is not pinned",
        )
    if margin_sd <= 0:
        raise ValueError("margin_sd must be positive")
    if not (0.0 < home_win_rate < 1.0):
        notes.append(
            "measured home-win rate is 0 or 1; the normal transform is undefined "
            "at the boundary, so the pinned value is not reported"
        )
        return None, None, None, tuple(notes)
    value = _STD_NORMAL.inv_cdf(home_win_rate) * margin_sd
    low = high = None
    if n_home_games > 0:
        w_lo, w_hi = home_win_rate_interval(home_win_rate, n_home_games)
        if 0.0 < w_lo < 1.0 and 0.0 < w_hi < 1.0:
            low = _STD_NORMAL.inv_cdf(w_lo) * margin_sd
            high = _STD_NORMAL.inv_cdf(w_hi) * margin_sd
    notes.append(
        "home-court advantage is pinned to the measured home-win rate "
        f"({home_win_rate:.4f}); it is not a fitted free parameter"
    )
    notes.append(
        "the pinned value inherits the uncertainty of the margin standard "
        "deviation, which is itself an unfitted default until calibrated"
    )
    return value, low, high, tuple(notes)


def _weight(game_date: str, as_of: datetime) -> float:
    game_dt = datetime.fromisoformat(game_date).astimezone(timezone.utc)
    age_days = max((as_of - game_dt).total_seconds() / 86400.0, 0.0)
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


class PppEstimator:
    """Estimator A: points-based, possession-scaled, margin in points.

    Uses the score and (when supplied) the possession count of each game.
    It never uses the win/loss label, so it is independent of
    :class:`OutcomeEstimator`.
    """

    name = "A: possession-based PPP rating"

    def __init__(self, default_possessions: Optional[float] = None) -> None:
        self.default_possessions = default_possessions

    def estimate(
        self,
        games: Sequence[TeamGame],
        home_team: str,
        away_team: str,
        as_of: datetime,
        margin_sd: float,
        home_advantage_points: Optional[float] = None,
        measured_home_rate: Optional[float] = None,
    ) -> EstimatorOutput:
        notes: List[str] = []
        home = _weighted_ppp(games, home_team, as_of)
        away = _weighted_ppp(games, away_team, as_of)
        league = _league_ppp(games, as_of)
        if (
            home is None
            or away is None
            or league is None
            or home[2] < MIN_GAMES_FOR_ESTIMATE
            or away[2] < MIN_GAMES_FOR_ESTIMATE
        ):
            notes.append(
                "insufficient authorised games for a possession-based estimate "
                f"({home_team}: {home[2] if home else 0}, "
                f"{away_team}: {away[2] if away else 0} games)"
            )
            return EstimatorOutput(self.name, None, None, margin_sd, 0, tuple(notes))

        h_off, h_def, h_games = home
        a_off, a_def, a_games = away
        poss = _measured_pace(games, as_of, self.default_possessions)
        if poss is None:
            notes.append(
                "measured pace unavailable and no default was supplied; the "
                "possession x PPP total cannot be formed"
            )
            return EstimatorOutput(self.name, None, None, margin_sd, 0, tuple(notes))
        notes.append(
            f"pace {poss:.2f} possessions per game (weighted mean of the "
            "authorised game rows that carry a possession count)"
        )

        home_pts = poss * (h_off * a_def / league)
        away_pts = poss * (a_off * h_def / league)
        margin = home_pts - away_pts

        if home_advantage_points is not None:
            hca = home_advantage_points
            if measured_home_rate is None:
                notes.append(
                    "home-court constant supplied by the caller; its derivation "
                    "is not shown here"
                )
        else:
            hca, _, _, hca_notes = implied_home_advantage_points(
                measured_home_rate, margin_sd, n_home_games=len(games)
            )
            notes.extend(hca_notes)
            if hca is None:
                notes.append(
                    "home-court advantage could not be pinned, so no margin is "
                    "produced by this estimator"
                )
                return EstimatorOutput(self.name, None, None, margin_sd, 0, tuple(notes))
        margin += hca

        prob = _normal_cdf(margin / margin_sd)
        notes.append(
            "expected points are possessions x points-per-possession; the "
            "total is not an average of team scoring averages"
        )
        return EstimatorOutput(
            self.name, margin, prob, margin_sd, min(h_games, a_games), tuple(notes)
        )


class OutcomeEstimator:
    """Estimator B: results-only Elo rating, no points used.

    The rating is updated chronologically from win/loss outcomes.  The
    home bonus is derived from the measured home-win rate, so it is pinned
    rather than fitted.
    """

    name = "B: results-only Elo rating"

    def __init__(
        self,
        scale: float = ELO_SCALE,
        k_factor: float = ELO_K_FACTOR,
    ) -> None:
        self.scale = scale
        self.k_factor = k_factor

    def ratings(
        self, pairs: Sequence[Pair], measured_home_rate: Optional[float] = None
    ) -> Dict[str, float]:
        """Chronological Elo ratings keyed by team name."""
        home_bonus = 0.0
        if measured_home_rate is not None and 0.0 < measured_home_rate < 1.0:
            # Elo logistic at zero rating difference:
            #   E_home = 1 / (1 + 10 ** (-(H) / scale)) = measured_home_rate
            home_bonus = -self.scale * math.log10((1 - measured_home_rate) / measured_home_rate)
        ratings: Dict[str, float] = {}
        for p in pairs:
            rh = ratings.get(p.home_team, 1500.0)
            ra = ratings.get(p.away_team, 1500.0)
            exp_home = 1.0 / (1.0 + 10 ** (-((rh - ra) + home_bonus) / self.scale))
            score_home = 1.0 if p.home_won else 0.0
            ratings[p.home_team] = rh + self.k_factor * (score_home - exp_home)
            ratings[p.away_team] = ra + self.k_factor * ((1 - score_home) - (1 - exp_home))
        return ratings

    def estimate(
        self,
        games: Sequence[TeamGame],
        home_team: str,
        away_team: str,
        as_of: datetime,
        margin_sd: float,
        measured_home_rate: Optional[float] = None,
    ) -> EstimatorOutput:
        notes: List[str] = []
        pairs = [
            p
            for p in pair_games(games)
            if datetime.fromisoformat(p.game_date).astimezone(timezone.utc) <= as_of
        ]
        played_home = sum(1 for p in pairs if p.home_team == home_team)
        played_away = sum(1 for p in pairs if p.away_team == away_team)
        if played_home < MIN_GAMES_FOR_ESTIMATE or played_away < MIN_GAMES_FOR_ESTIMATE:
            notes.append(
                "insufficient authorised games for a results-only estimate "
                f"({home_team}: {played_home}, {away_team}: {played_away})"
            )
            return EstimatorOutput(self.name, None, None, margin_sd, 0, tuple(notes))
        if measured_home_rate is None:
            notes.append(
                "measured home-win rate not supplied; the home bonus is not "
                "pinned and this estimator declines to report a margin"
            )
            return EstimatorOutput(self.name, None, None, margin_sd, 0, tuple(notes))
        ratings = self.ratings(pairs, measured_home_rate)
        rh = ratings.get(home_team, 1500.0)
        ra = ratings.get(away_team, 1500.0)
        home_bonus = -self.scale * math.log10((1 - measured_home_rate) / measured_home_rate)
        exp_home = 1.0 / (1.0 + 10 ** (-((rh - ra) + home_bonus) / self.scale))
        prob = min(max(exp_home, 1e-12), 1 - 1e-12)
        margin = _STD_NORMAL.inv_cdf(prob) * margin_sd
        notes.append(
            "this estimator used win/loss outcomes only; the points scored "
            "were not read"
        )
        notes.append(
            "the home bonus is pinned to the measured home-win rate "
            f"({measured_home_rate:.4f}), not fitted"
        )
        return EstimatorOutput(
            self.name, margin, prob, margin_sd, min(played_home, played_away), tuple(notes)
        )


def disagreement(
    estimator_a: EstimatorOutput,
    estimator_b: EstimatorOutput,
) -> Disagreement:
    """Compare two estimator outputs.  This is the published headline."""
    notes: List[str] = []
    if estimator_a.expected_home_margin is None or estimator_b.expected_home_margin is None:
        return Disagreement(
            None, None, None, None, estimator_a, estimator_b,
            ("at least one estimator produced no value; the gap stays blank",),
        )
    gap = estimator_a.expected_home_margin - estimator_b.expected_home_margin
    prob_gap: Optional[float] = None
    if (
        estimator_a.home_win_probability is not None
        and estimator_b.home_win_probability is not None
    ):
        prob_gap = estimator_a.home_win_probability - estimator_b.home_win_probability
    sd_gap = math.sqrt(estimator_a.margin_sd**2 + estimator_b.margin_sd**2)
    z = gap / sd_gap if sd_gap > 0 else None
    notes.append(
        "the gap is the headline confidence signal; the blend underneath is "
        "secondary and is only formed when both estimators produced a value"
    )
    if sd_gap > 0:
        notes.append(
            "z compares the gap with the combined margin dispersion of the two "
            "estimators; a large |z| means the two views are not interchangeable"
        )
    return Disagreement(gap, prob_gap, z, sd_gap, estimator_a, estimator_b, tuple(notes))


def blend_estimators(
    gap: Disagreement,
    model_log_loss: Optional[float],
    market_log_loss: Optional[float],
) -> Tuple[Optional[float], Optional[float], Optional[float], Tuple[str, ...]]:
    """Blend the two estimators underneath the disagreement headline.

    Weights come from the **measured out-of-sample log loss** of each
    estimator: the lower the log loss, the larger the weight.  When either
    log loss has not been measured, no blend is produced - the disagreement
    is published on its own.

    Returns ``(blended_margin, weight_a, weight_b, notes)``.
    """
    notes: List[str] = []
    if not gap.is_measurable:
        return None, None, None, ("no measurable disagreement to blend",)
    if model_log_loss is None or market_log_loss is None:
        notes.append(
            "out-of-sample log loss is not measured for both estimators, so no "
            "blend is published; the disagreement stands alone"
        )
        return None, None, None, tuple(notes)
    if model_log_loss <= 0 or market_log_loss <= 0:
        raise ValueError("log losses must be positive")
    w_a = 1.0 / model_log_loss
    w_b = 1.0 / market_log_loss
    total = w_a + w_b
    wa, wb = w_a / total, w_b / total
    blended = wa * float(gap.estimator_a.expected_home_margin) + wb * float(
        gap.estimator_b.expected_home_margin
    )
    notes.append(
        "weights are inverse measured out-of-sample log loss "
        f"(A={model_log_loss:.4f}, B={market_log_loss:.4f}) -> "
        f"w_A={wa:.3f}, w_B={wb:.3f}"
    )
    notes.append("the blend is printed underneath the disagreement headline")
    return blended, wa, wb, tuple(notes)


# --- internal helpers -------------------------------------------------------


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _weighted_ppp(
    games: Sequence[TeamGame], team: str, as_of: datetime
) -> Optional[Tuple[float, float, int]]:
    w_sum = 0.0
    off = 0.0
    dfn = 0.0
    count = 0
    for g in games:
        if g.team != team:
            continue
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        poss = g.possessions if g.possessions and g.possessions > 0 else None
        if poss is None:
            continue
        w = _weight(g.game_date, as_of)
        w_sum += w
        off += w * (g.points / poss)
        dfn += w * (g.opp_points / poss)
        count += 1
    if w_sum <= 0 or count == 0:
        return None
    return off / w_sum, dfn / w_sum, count


def _league_ppp(games: Sequence[TeamGame], as_of: datetime) -> Optional[float]:
    num = 0.0
    den = 0.0
    for g in games:
        if datetime.fromisoformat(g.game_date).astimezone(timezone.utc) > as_of:
            continue
        poss = g.possessions if g.possessions and g.possessions > 0 else None
        if poss is None:
            continue
        w = _weight(g.game_date, as_of)
        num += w * (g.points / poss)
        den += w
    if den <= 0:
        return None
    return num / den


def _measured_pace(
    games: Sequence[TeamGame],
    as_of: datetime,
    default_possessions: Optional[float] = None,
) -> Optional[float]:
    """Weighted mean possessions per game, from the authorised rows."""
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
    if den > 0:
        return num / den
    return default_possessions
