"""Probability helpers used by the origination and validation code.

Only the standard library is used. The normal helpers wrap
``statistics.NormalDist`` so that quantiles are exact inverse-CDF values
rather than approximations.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

__all__ = [
    "normal_cdf",
    "normal_quantile",
    "bernoulli_cdf",
    "beta_quantile_approx",
    "clamp",
    "MonteCarloResult",
]


def normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """CDF of a normal distribution."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    z = (x - mu) / sigma
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def normal_quantile(p: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """Inverse CDF (quantile) of a normal distribution."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must lie strictly between 0 and 1")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    z = _inverse_normal_cdf(p)
    return mu + sigma * z


def _inverse_normal_cdf(p: float) -> float:
    """Rational-approximation inverse standard normal CDF (Acklam)."""
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    elif p <= phigh:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
            ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
        )
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    # One Halley refinement step.
    e = normal_cdf(x) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def bernoulli_cdf(k: int, n: int, p: float) -> float:
    """Cumulative probability of a binomial count (used for over/under legs)."""
    if not 0 <= k <= n:
        return 0.0 if k < 0 else 1.0
    total = 0.0
    for i in range(k + 1):
        total += math.comb(n, i) * (p**i) * ((1 - p) ** (n - i))
    return min(1.0, max(0.0, total))


def beta_quantile_approx(p: float, alpha: float, beta: float) -> float:
    """Approximate Beta(alpha, beta) quantile via a normal approximation.

    Used only for illustrative interval reporting; the engine labels such
    intervals as approximations and never as calibrated coverage.
    """
    if alpha <= 0 or beta <= 0:
        raise ValueError("alpha and beta must be positive")
    mean = alpha / (alpha + beta)
    var = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
    return mean + math.sqrt(var) * _inverse_normal_cdf(p)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class MonteCarloResult:
    """Summary of a Monte Carlo estimate (estimate plus its standard error)."""

    estimate: float
    standard_error: float
    draws: int
    seed: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "draws": self.draws,
            "seed": self.seed,
        }
