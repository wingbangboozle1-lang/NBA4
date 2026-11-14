"""Correlation estimators for same-game legs.

Everything here is a *measurement tool*. None of it produces an NBA number by
itself: a coefficient is only meaningful when the caller supplies the leg
definitions, the sample window and the conditioning set, and when the sample
is large enough for the estimate to mean anything.

Implemented:

* ``pearson``  - linear association between two continuous series (the
  definition NIST's handbook uses; range -1..+1).
* ``spearman`` - rank association, robust to monotone non-linearity.
* ``phi`` / ``yule_q`` - association between two binary legs (a player prop
  crossing a threshold is binary).
* ``cluster_bootstrap_ci`` - uncertainty interval that resamples whole games
  (or dates) rather than individual observations, because several legs of one
  game are not independent observations.
* ``shrink`` - the preregistered rule that pulls unstable estimates toward a
  prior, so that a single noisy game cannot create a "signal".
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Sequence

__all__ = [
    "pearson",
    "spearman",
    "phi",
    "yule_q",
    "cluster_bootstrap_ci",
    "shrink",
    "CorrelationResult",
]


@dataclass(frozen=True)
class CorrelationResult:
    """An estimate with the information required to judge it."""

    estimate: float
    lower: float | None
    upper: float | None
    sample_size: int
    cluster_count: int
    method: str

    def as_dict(self) -> dict[str, object]:
        return {
            "estimate": self.estimate,
            "lower": self.lower,
            "upper": self.upper,
            "sample_size": self.sample_size,
            "cluster_count": self.cluster_count,
            "method": self.method,
        }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Pearson product-moment correlation coefficient.

    Requires at least two paired observations and non-zero variance in both
    series; otherwise the estimate is undefined and a :class:`ValueError` is
    raised rather than a silent 0.0.
    """
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have the same length")
    if len(xs) < 2:
        raise ValueError("at least two paired observations are required")
    mx, my = _mean(xs), _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        raise ValueError("correlation is undefined for a constant series")
    return num / (den_x * den_y)


def _ranks(values: Sequence[float]) -> list[float]:
    """Average ranks, handling ties."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation (Pearson correlation of the ranks)."""
    return pearson(_ranks(xs), _ranks(ys))


def phi(xs: Sequence[bool], ys: Sequence[bool]) -> float:
    """Phi coefficient for two binary series in {0, 1}."""
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have the same length")
    n11 = sum(1 for x, y in zip(xs, ys) if x and y)
    n10 = sum(1 for x, y in zip(xs, ys) if x and not y)
    n01 = sum(1 for x, y in zip(xs, ys) if not x and y)
    n00 = sum(1 for x, y in zip(xs, ys) if not x and not y)
    denom = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denom == 0:
        raise ValueError("phi is undefined when a series is constant")
    return (n11 * n00 - n10 * n01) / denom


def yule_q(xs: Sequence[bool], ys: Sequence[bool]) -> float:
    """Yule's Q association for two binary series (odds-ratio based)."""
    n11 = sum(1 for x, y in zip(xs, ys) if x and y)
    n10 = sum(1 for x, y in zip(xs, ys) if x and not y)
    n01 = sum(1 for x, y in zip(xs, ys) if not x and y)
    n00 = sum(1 for x, y in zip(xs, ys) if not x and not y)
    if n11 * n00 == 0 or n10 * n01 == 0:
        raise ValueError("yule_q is undefined when a cell count is zero")
    return (n11 * n00 - n10 * n01) / (n11 * n00 + n10 * n01)


def cluster_bootstrap_ci(
    values_by_cluster: dict[str, list[tuple[float, float]]],
    statistic: Callable[[Sequence[tuple[float, float]]], float],
    resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 20261114,
) -> tuple[float, float]:
    """Bootstrap interval that resamples whole clusters (games or dates).

    ``values_by_cluster`` maps a cluster id (for example a game id) to the
    paired observations inside that cluster. Resampling clusters - rather than
    rows - keeps the dependence between legs of the same game intact, which is
    the point of the method.

    The returned interval is an estimate of sampling uncertainty under the
    bootstrap's assumptions. It is not a guarantee about future results.
    """
    if not values_by_cluster:
        raise ValueError("no clusters supplied")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")
    rng = random.Random(seed)
    cluster_ids = list(values_by_cluster)
    estimates: list[float] = []
    for _ in range(resamples):
        sample: list[tuple[float, float]] = []
        for _ in range(len(cluster_ids)):
            chosen = rng.choice(cluster_ids)
            sample.extend(values_by_cluster[chosen])
        try:
            estimates.append(statistic(sample))
        except ValueError:
            # A degenerate resample (constant series) has no estimate; skip it
            # rather than substituting a value.
            continue
    if not estimates:
        raise ValueError("bootstrap produced no usable estimates")
    estimates.sort()
    alpha = (1.0 - confidence) / 2.0
    lower = estimates[max(0, int(math.floor(alpha * len(estimates))))]
    upper = estimates[min(len(estimates) - 1, int(math.ceil((1 - alpha) * len(estimates))) - 1)]
    return lower, upper


def shrink(estimate: float, prior: float, weight: float) -> float:
    """Shrink an estimate toward a prior with a preregistered weight.

    ``weight`` is the share of the prior in the result (0 keeps the estimate,
    1 replaces it with the prior). The weight must be fixed before the
    holdout is opened; the engine does not choose it.
    """
    if not 0.0 <= weight <= 1.0:
        raise ValueError("weight must lie within [0, 1]")
    return (1.0 - weight) * estimate + weight * prior


def correlation_with_uncertainty(
    values_by_cluster: dict[str, list[tuple[float, float]]],
    method: str = "pearson",
    resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 20261114,
) -> CorrelationResult:
    """Convenience wrapper: estimate a correlation and its cluster interval."""
    flat = [pair for pairs in values_by_cluster.values() for pair in pairs]
    if method == "pearson":
        estimate = pearson([p[0] for p in flat], [p[1] for p in flat])
        statistic: Callable[[Sequence[tuple[float, float]]], float] = lambda pairs: pearson(
            [p[0] for p in pairs], [p[1] for p in pairs]
        )
    elif method == "spearman":
        estimate = spearman([p[0] for p in flat], [p[1] for p in flat])
        statistic = lambda pairs: spearman(  # noqa: E731
            [p[0] for p in pairs], [p[1] for p in pairs]
        )
    else:
        raise ValueError(f"unsupported method: {method!r}")
    lower, upper = cluster_bootstrap_ci(
        values_by_cluster, statistic, resamples=resamples, confidence=confidence, seed=seed
    )
    return CorrelationResult(
        estimate=estimate,
        lower=lower,
        upper=upper,
        sample_size=len(flat),
        cluster_count=len(values_by_cluster),
        method=method,
    )
