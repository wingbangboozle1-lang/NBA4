"""Joint (parlay / prop-combo) probability estimation.

A parlay is a bet on the *joint* event. Multiplying marginal probabilities
assumes independence, which is exactly the assumption that fails for legs that
share a game (both teams' pace, the score margin, a shared team, minutes
substitution). This module therefore estimates the joint probability directly
with a Gaussian copula:

1. Each leg has a marginal probability ``p_i`` of hitting its threshold.
2. Each leg maps to a standard-normal latent variable ``z_i`` whose threshold
   is ``Phi^-1(p_i)``.
3. The latent variables are correlated through a supplied correlation matrix
   ``R`` (estimated from data - see ``engine.correlation``).
4. P(all legs hit) is estimated by Monte Carlo over a correlated normal draw,
   and the Monte Carlo standard error is reported with the estimate.

The independence variant is provided so the difference can be shown rather than
argued about; it is never used to price a combo unless the correlation matrix
is the identity because the leg pairs were verified as independent.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence

from .distributions import MonteCarloResult, normal_quantile

__all__ = [
    "ParlayLeg",
    "cholesky",
    "joint_probability",
    "independent_joint_probability",
    "ParlayEstimate",
]


@dataclass(frozen=True)
class ParlayLeg:
    """One leg of a combo: a marginal probability and the market it refers to."""

    leg_id: str
    event_id: str
    probability: float
    description: str = ""

    def __post_init__(self) -> None:
        if not 0.0 < self.probability < 1.0:
            raise ValueError("leg probability must lie strictly between 0 and 1")


@dataclass(frozen=True)
class ParlayEstimate:
    """A joint-probability estimate with uncertainty and the naive comparison."""

    joint_probability: float
    standard_error: float
    independent_probability: float
    dependence_effect: float
    draws: int
    seed: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "joint_probability": self.joint_probability,
            "standard_error": self.standard_error,
            "independent_probability": self.independent_probability,
            "dependence_effect": self.dependence_effect,
            "draws": self.draws,
            "seed": self.seed,
        }


def cholesky(matrix: Sequence[Sequence[float]]) -> list[list[float]]:
    """Lower-triangular Cholesky factor of a symmetric positive-definite matrix.

    Implemented directly so the engine has no third-party dependency. The
    matrix is validated for symmetry and positive definiteness so that a
    badly specified correlation matrix fails loudly.
    """
    n = len(matrix)
    if n == 0:
        raise ValueError("matrix must not be empty")
    for i in range(n):
        if len(matrix[i]) != n:
            raise ValueError("matrix must be square")
        for j in range(n):
            if abs(matrix[i][j] - matrix[j][i]) > 1e-9:
                raise ValueError("correlation matrix must be symmetric")
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            total = matrix[i][j] - sum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                if total <= 0:
                    raise ValueError("correlation matrix is not positive definite")
                lower[i][j] = math.sqrt(total)
            else:
                lower[i][j] = total / lower[j][j]
    return lower


def independent_joint_probability(legs: Sequence[ParlayLeg]) -> float:
    """Product of the marginals - the independence assumption, for comparison."""
    result = 1.0
    for leg in legs:
        result *= leg.probability
    return result


def joint_probability(
    legs: Sequence[ParlayLeg],
    correlation: Sequence[Sequence[float]],
    draws: int = 20000,
    seed: int = 20261114,
) -> ParlayEstimate:
    """Estimate P(all legs hit) under a Gaussian copula with the given correlations.

    The returned ``standard_error`` is the Monte Carlo standard error of the
    estimate; it describes simulation error, not the uncertainty of the
    underlying correlation estimates.
    """
    if not legs:
        raise ValueError("at least one leg is required")
    if draws <= 0:
        raise ValueError("draws must be positive")
    n = len(legs)
    if len(correlation) != n:
        raise ValueError("correlation matrix size does not match the number of legs")
    factor = cholesky(correlation)
    # A leg hits when its latent normal exceeds the threshold, so the threshold is
    # the (1 - p) quantile: P(Z >= Phi^-1(1 - p)) = p. Using Phi^-1(p) instead
    # silently inverts every marginal that is not exactly 0.5 (found 2026-11-15,
    # flag P8-01; it is invisible on 0.5/0.5 fixtures, which is how it survived).
    thresholds = [normal_quantile(1.0 - leg.probability) for leg in legs]
    rng = random.Random(seed)
    hits = 0
    for _ in range(draws):
        z = [rng.gauss(0.0, 1.0) for _ in range(n)]
        correlated = [
            sum(factor[i][k] * z[k] for k in range(i + 1)) for i in range(n)
        ]
        if all(correlated[i] >= thresholds[i] for i in range(n)):
            hits += 1
    estimate = hits / draws
    standard_error = math.sqrt(max(estimate * (1 - estimate), 0.0) / draws)
    independent = independent_joint_probability(legs)
    return ParlayEstimate(
        joint_probability=estimate,
        standard_error=standard_error,
        independent_probability=independent,
        dependence_effect=estimate - independent,
        draws=draws,
        seed=seed,
    )
