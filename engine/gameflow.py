"""Game-flow scenario distributions (hypothesis S6).

Scenarios are defined by explicit margin thresholds fixed in advance
(PROPOSED defaults below; to be preregistered and validated before use).
A narrative label is never produced without its trigger, and player-minute
conditioning is a scenario multiplier, not a story.

Scenario probabilities come from the predictive margin distribution in
engine.ratings - a distribution, not a deterministic script.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import math

# --- PROPOSED scenario thresholds (margin from home team's perspective) ------
SEPARATION_MARGIN = 12.0   # |margin| >= 12 -> separation/blowout risk
COMPETITIVE_MARGIN = 5.0   # |margin| <= 5 -> competitive finish
BLOWOUT_MINUTES_MULTIPLIER = 0.9   # starter minutes in separation scenarios
# ---------------------------------------------------------------------------


@dataclass
class GameFlowScenarios:
    p_competitive: float
    p_separation_home: float
    p_separation_away: float
    p_moderate: float
    starter_minutes_multiplier: float
    notes: Tuple[str, ...]


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def scenario_distribution(
    expected_margin: float, margin_sd: float
) -> GameFlowScenarios:
    if margin_sd <= 0:
        raise ValueError("margin_sd must be positive")
    p_comp = _normal_cdf((COMPETITIVE_MARGIN - expected_margin) / margin_sd) - _normal_cdf(
        (-COMPETITIVE_MARGIN - expected_margin) / margin_sd
    )
    p_sep_home = 1.0 - _normal_cdf((SEPARATION_MARGIN - expected_margin) / margin_sd)
    p_sep_away = _normal_cdf((-SEPARATION_MARGIN - expected_margin) / margin_sd)
    p_moderate = max(0.0, 1.0 - p_comp - p_sep_home - p_sep_away)
    return GameFlowScenarios(
        p_competitive=p_comp,
        p_separation_home=p_sep_home,
        p_separation_away=p_sep_away,
        p_moderate=p_moderate,
        starter_minutes_multiplier=BLOWOUT_MINUTES_MULTIPLIER,
        notes=(
            "thresholds are PROPOSED (docs/engine.md) and unvalidated; "
            "probabilities derive from the normal margin approximation only",
        ),
    )


def minutes_multiplier_by_flow(scenarios: GameFlowScenarios) -> float:
    """Expected starter-minutes multiplier averaged over scenarios."""
    p_sep = scenarios.p_separation_home + scenarios.p_separation_away
    return (1.0 - p_sep) * 1.0 + p_sep * scenarios.starter_minutes_multiplier
