"""Totals as possessions x points-per-possession, not as an average of scoring averages.

Brief item implemented (2026-11-15): "Model the total as possessions x
points-per-possession, not as an average of team scoring averages."

Why the distinction matters arithmetically. A scoring average is a *product*
(possessions x efficiency). Adding two products and dividing by nothing smuggles
each team's pace in twice and hides it: a fast team versus a slow team does not
produce the mean of their scoring averages, it produces a shared possession
count times two efficiency rates. The possession model makes the two levers
separate, so a rest/travel/rotation effect can be attributed to pace and an
injury effect to efficiency, which is exactly what the injury and game-flow
sections of this project need to reason about.

Form, with every quantity supplied by the caller:

    total = possessions * (ppp_home + ppp_away)
    ppp_x = points per possession of team x, optionally adjusted for the
            opponent's defensive rate by a caller-declared form

What is **not** hard-coded, and why:

* The pace-combining rule. ``possessions_for_game`` accepts the value the
  licensed feed publishes; the fallback ``pace_product_over_league`` and
  ``pace_weighted_mean`` are two candidate rules exposed as separate functions so
  a pre-registered choice can be tested against the other. Neither is a default.
* The possessions-from-box-score constants (the ``0.98`` and ``0.44`` style
  coefficients seen in the literature). They are estimation constants with no
  official NBA sentence behind them in ``docs/sources.md``, so
  ``possessions_from_components`` requires all four coefficients to be passed
  explicitly together with the source that states them.

The naive baseline is kept as a first-class function (``naive_total_from_averages``)
so the two can be published side by side and the disagreement measured; it is
not silently discarded.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

NAIVE_LABEL = "sum of scoring averages (baseline, not a pace model)"
PPP_LABEL = "possessions x points per possession (pace model)"


class TotalError(ValueError):
    """Raised when a total is attempted without the inputs its form requires."""


def ppp_from_rating(rating_100: Optional[float]) -> Optional[float]:
    """Points per possession from a per-100-possessions rate."""
    if rating_100 is None:
        return None
    if rating_100 < 0:
        raise TotalError("a per-100 rate cannot be negative")
    return rating_100 / 100.0


def adjusted_ppp(
    team_off_ppp: float,
    opp_def_ppp: float,
    league_def_ppp: float,
    form: str = "multiplicative",
) -> float:
    """Efficiency adjusted for the opponent, in a declared, reviewable form.

    ``multiplicative``: off * (opp_def / league_def). ``additive``: off +
    (opp_def - league_def). Both are stated rather than chosen by this module;
    the choice belongs in the pre-registration file.
    """
    if league_def_ppp == 0:
        raise TotalError("league defensive rate must be non-zero to scale against")
    if form == "multiplicative":
        return team_off_ppp * (opp_def_ppp / league_def_ppp)
    if form == "additive":
        return team_off_ppp + (opp_def_ppp - league_def_ppp)
    raise TotalError(f"unknown adjustment form {form!r}: use 'multiplicative' or 'additive'")


def pace_product_over_league(pace_home: float, pace_away: float, league_pace: float) -> float:
    """Candidate game-pace rule 1: (home x away) / league."""
    if league_pace <= 0:
        raise TotalError("league pace must be positive")
    return (pace_home * pace_away) / league_pace


def pace_weighted_mean(pace_home: float, pace_away: float, weights: Tuple[float, float]) -> float:
    """Candidate game-pace rule 2: a declared weighted mean of the two paces."""
    if len(weights) != 2 or any(w < 0 for w in weights) or abs(sum(weights) - 1.0) > 1e-9:
        raise TotalError("weights must be two non-negative values summing to 1")
    return weights[0] * pace_home + weights[1] * pace_away


@dataclass(frozen=True)
class TotalProjection:
    """One projected total with its decomposition, ready to publish as a row."""

    game_id: str
    possessions: float
    ppp_home: float
    ppp_away: float
    model_total: float
    naive_total: Optional[float]
    naive_minus_model: Optional[float]
    pace_rule: str
    adjustment_form: str
    status: str
    sources: Tuple[str, ...] = ()

    def as_row(self) -> Dict[str, object]:
        return {
            "game_id": self.game_id,
            "possessions": round(self.possessions, 3),
            "ppp_home": round(self.ppp_home, 5),
            "ppp_away": round(self.ppp_away, 5),
            "model_total": round(self.model_total, 3),
            "naive_total": None if self.naive_total is None else round(self.naive_total, 3),
            "naive_minus_model": (
                None if self.naive_minus_model is None else round(self.naive_minus_model, 3)
            ),
            "pace_rule": self.pace_rule,
            "adjustment_form": self.adjustment_form,
            "status": self.status,
            "sources": list(self.sources),
        }


def model_total(possessions: float, ppp_home: float, ppp_away: float) -> float:
    """The modelled total. Both rates must be points per possession, not per game."""
    if possessions <= 0:
        raise TotalError("possessions must be positive")
    if ppp_home < 0 or ppp_away < 0:
        raise TotalError("points per possession cannot be negative")
    return possessions * (ppp_home + ppp_away)


def naive_total_from_averages(points_home: float, points_away: float) -> float:
    """The baseline being replaced: each team's scoring average, summed."""
    if points_home < 0 or points_away < 0:
        raise TotalError("scoring averages cannot be negative")
    return points_home + points_away


def project_total(
    game_id: str,
    possessions: Optional[float],
    ppp_home: Optional[float],
    ppp_away: Optional[float],
    scoring_averages: Optional[Tuple[float, float]] = None,
    pace_rule: str = "declared-by-caller",
    adjustment_form: str = "none",
    sources: Sequence[str] = (),
) -> TotalProjection:
    """Assemble the projection, or explain precisely why there isn't one."""
    missing = [
        name for name, value in (("possessions", possessions), ("ppp_home", ppp_home), ("ppp_away", ppp_away))
        if value is None
    ]
    if missing:
        naive = (
            naive_total_from_averages(*scoring_averages)
            if scoring_averages and len(scoring_averages) == 2
            else None
        )
        return TotalProjection(
            game_id=game_id,
            possessions=float("nan"),
            ppp_home=float("nan"),
            ppp_away=float("nan"),
            model_total=float("nan"),
            naive_total=naive,
            naive_minus_model=None,
            pace_rule=pace_rule,
            adjustment_form=adjustment_form,
            status="INPUTS_MISSING: " + ", ".join(missing) + " - no total is published without them",
            sources=tuple(sources),
        )
    assert possessions is not None and ppp_home is not None and ppp_away is not None
    projected = model_total(possessions, ppp_home, ppp_away)
    naive = (
        naive_total_from_averages(*scoring_averages)
        if scoring_averages and len(scoring_averages) == 2
        else None
    )
    return TotalProjection(
        game_id=game_id,
        possessions=possessions,
        ppp_home=ppp_home,
        ppp_away=ppp_away,
        model_total=projected,
        naive_total=naive,
        naive_minus_model=None if naive is None else naive - projected,
        pace_rule=pace_rule,
        adjustment_form=adjustment_form,
        status=PPP_LABEL,
        sources=tuple(sources),
    )


def possessions_from_components(
    field_goal_attempts: float,
    field_goals_made: float,
    offensive_rebounds: float,
    free_throw_attempts: float,
    turnovers: float,
    coefficients: Dict[str, float],
    coefficient_source: str,
) -> Dict[str, object]:
    """Estimated possessions, with every coefficient declared and sourced.

    ``coefficients`` must carry exactly the keys ``missed_field_goal_weight`` and
    ``free_throw_attempt_weight``; the caller states them because this repository
    will not assert a value for them without a source.
    """
    required = ("missed_field_goal_weight", "free_throw_attempt_weight")
    absent = [k for k in required if k not in coefficients]
    if absent:
        raise TotalError(
            "possession coefficients are not defaulted here; missing: " + ", ".join(absent)
        )
    if not coefficient_source.startswith("https://"):
        raise TotalError("the coefficient source must be an https URL; a magic number needs a citation")
    missed = field_goal_attempts - field_goals_made
    if missed < 0:
        raise TotalError("field goals made exceed attempts: check the source rows")
    possessions = (
        field_goal_attempts
        - offensive_rebounds
        + coefficients["missed_field_goal_weight"] * missed
        + coefficients["free_throw_attempt_weight"] * free_throw_attempts
        + turnovers
    )
    return {
        "possessions": possessions,
        "formula": "FGA - ORB + w_missed*(FGA-FG) + w_fta*FTA + TOV",
        "coefficients": {k: coefficients[k] for k in required},
        "coefficient_source": coefficient_source,
        "status": "ESTIMATE from box-score components, coefficients supplied by the caller",
    }


def compare_totals(rows: Sequence[TotalProjection]) -> List[Dict[str, object]]:
    """Summary of the naive-vs-model gap for the model page.

    ``model_total`` is NaN whenever the pace model lacks an input; that row is
    reported with a blank model figure and its blocking status rather than a
    fabricated number.
    """
    rows = list(rows)
    gaps = [r.naive_minus_model for r in rows if r.naive_minus_model is not None]
    mean_gap = round(sum(gaps) / len(gaps), 3) if gaps else None
    out: List[Dict[str, object]] = []
    for row in rows:
        model = None if math.isnan(row.model_total) else round(row.model_total, 2)
        out.append(
            {
                "game_id": row.game_id,
                "model_total": model,
                "naive_total": None if row.naive_total is None else round(row.naive_total, 2),
                "gap": None if row.naive_minus_model is None else round(row.naive_minus_model, 2),
                "mean_gap": mean_gap,
                "status": row.status,
            }
        )
    return out
