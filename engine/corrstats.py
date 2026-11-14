"""Correlation and joint-event estimation for parlays/prop combos (gate G8).

"Correlation" is measured per leg pair and conditioning set - never assumed.
Continuous relationships use Pearson correlation of pregame-model residuals
(NIST definition, docs/sources.md STAT-01). Binary threshold legs use direct
joint-event rates and the phi coefficient. Uncertainty is estimated by
bootstrapping GAME clusters so legs from one game are not treated as
independent observations (STAT-02), and unstable estimates shrink toward
zero under a fixed prior weight.

Every estimate is returned with its sample count and interval; a blank
(empty) result means "not measured", never zero.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple


@dataclass
class CorrelationEstimate:
    kind: str  # "pearson_residual" | "phi_binary" | "joint_rate"
    value: Optional[float]
    ci_low: Optional[float]
    ci_high: Optional[float]
    n: int
    clusters: int
    shrunk: bool
    notes: Tuple[str, ...]


def pearson(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    n = len(x)
    if n != len(y) or n < 2:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sxx * syy)


def phi(a: Sequence[bool], b: Sequence[bool]) -> Optional[float]:
    n = len(a)
    if n != len(b) or n < 2:
        return None
    n11 = sum(1 for p, q in zip(a, b) if p and q)
    n10 = sum(1 for p, q in zip(a, b) if p and not q)
    n01 = sum(1 for p, q in zip(a, b) if not p and q)
    n00 = sum(1 for p, q in zip(a, b) if not p and not q)
    den = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if den == 0:
        return None
    return (n11 * n00 - n10 * n01) / den


def joint_rate(a: Sequence[bool], b: Sequence[bool]) -> Optional[float]:
    if not a or len(a) != len(b):
        return None
    return sum(1 for p, q in zip(a, b) if p and q) / len(a)


def shrink_toward_zero(r: float, n: int, prior_n: float = 10.0) -> float:
    """Fixed shrinkage rule: r * n / (n + prior_n).

    prior_n is a preregisterable parameter (default 10 games of prior weight).
    Shrinkage is applied to unstable small-sample estimates, not to hide them:
    the raw value is always reported beside the shrunk value.
    """
    return r * n / (n + prior_n)


def cluster_bootstrap_ci(
    values: Sequence[Tuple[str, float]],
    stat_fn: Callable[[List[float]], Optional[float]],
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 20261114,
) -> Tuple[Optional[float], Optional[float]]:
    """Percentile CI from resampling game clusters with replacement.

    values: (game_id, observation) pairs. The statistic is computed per
    bootstrap resample of whole games (STAT-02 caution: bootstrap is not
    universally appropriate - intervals are reported as estimates, not
    guarantees).
    """
    by_game: dict = {}
    for gid, v in values:
        by_game.setdefault(gid, []).append(v)
    games = sorted(by_game)
    if len(games) < 2:
        return None, None
    rng = random.Random(seed)
    samples: List[float] = []
    for _ in range(n_boot):
        picked: List[float] = []
        for _ in range(len(games)):
            picked.extend(by_game[rng.choice(games)])
        s = stat_fn(picked)
        if s is not None:
            samples.append(s)
    if len(samples) < 10:
        return None, None
    samples.sort()
    lo = samples[int((alpha / 2) * len(samples))]
    hi = samples[min(int((1 - alpha / 2) * len(samples)), len(samples) - 1)]
    return lo, hi


def residual_correlation_estimate(
    residuals_x: Sequence[Tuple[str, float]],
    residuals_y: Sequence[Tuple[str, float]],
    shrink: bool = True,
) -> CorrelationEstimate:
    """Pearson correlation of two residual series paired by game_id.

    Within each game, observations pair in their listed order (leg 1 with
    leg 1, leg 2 with leg 2, ...). Games with unequal leg counts are
    truncated to the shorter side and noted.
    """
    x_by_game: dict = {}
    y_by_game: dict = {}
    for g, v in residuals_x:
        x_by_game.setdefault(g, []).append(v)
    for g, v in residuals_y:
        y_by_game.setdefault(g, []).append(v)
    pairs: List[Tuple[str, float, float]] = []
    truncated = False
    for g in sorted(set(x_by_game) & set(y_by_game)):
        xs_g, ys_g = x_by_game[g], y_by_game[g]
        if len(xs_g) != len(ys_g):
            truncated = True
        for xv, yv in zip(xs_g, ys_g):
            pairs.append((g, xv, yv))
    if len(pairs) < 2:
        return CorrelationEstimate(
            "pearson_residual", None, None, None, len(pairs), 0, False,
            ("no paired licensed residual observations; value stays blank",),
        )
    games = [g for g, _, _ in pairs]
    xs = [v for _, v, _ in pairs]
    ys = [v for _, _, v in pairs]
    r = pearson(xs, ys)
    clusters = len(set(games))

    # Bootstrap over game clusters using paired per-game lists.
    by_game: dict = {}
    for g, xv, yv in pairs:
        by_game.setdefault(g, []).append((xv, yv))
    gids = sorted(by_game)
    lo = hi = None
    if clusters >= 2:
        rng = random.Random(20261114)
        boot: List[float] = []
        for _ in range(1000):
            xs_b: List[float] = []
            ys_b: List[float] = []
            for _ in range(len(gids)):
                for xv, yv in by_game[rng.choice(gids)]:
                    xs_b.append(xv)
                    ys_b.append(yv)
            rb = pearson(xs_b, ys_b)
            if rb is not None:
                boot.append(rb)
        if len(boot) >= 10:
            boot.sort()
            lo = boot[25]
            hi = boot[min(974, len(boot) - 1)]
    shrunk = shrink_toward_zero(r, clusters) if (r is not None and shrink) else r
    notes = [
        "raw r="
        + (f"{r:.4f}" if r is not None else "n/a")
        + "; shrunk toward 0 with prior_n=10 game clusters; interval is a "
        "bootstrap estimate, not a guarantee (STAT-02)",
    ]
    if truncated:
        notes.append("games with unequal leg counts were truncated to the shorter side")
    return CorrelationEstimate(
        "pearson_residual", r if not shrink else shrunk, lo, hi,
        len(pairs), clusters, shrink, tuple(notes),
    )


def joint_event_estimate(
    legs_a: Sequence[Tuple[str, bool]],
    legs_b: Sequence[Tuple[str, bool]],
) -> CorrelationEstimate:
    """Direct joint-event probability and phi for two binary legs."""
    dict_b = dict(legs_b)
    pairs = [(g, v, dict_b[g]) for g, v in legs_a if g in dict_b]
    if len(pairs) < 2:
        return CorrelationEstimate(
            "phi_binary", None, None, None, len(pairs), 0, False,
            ("no paired settled leg outcomes; joint probability stays blank",),
        )
    a = [v for _, v, _ in pairs]
    b = [v for _, _, v in pairs]
    r = phi(a, b)
    return CorrelationEstimate(
        "phi_binary", r, None, None, len(pairs), len({g for g, _, _ in pairs}), False,
        (f"joint rate = {joint_rate(a, b):.4f}; phi reported with sample count",),
    )
