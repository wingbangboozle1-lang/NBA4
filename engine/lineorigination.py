"""Model-originated lines, fair probabilities and market-price handling.

Design rules implemented here:

* A *model-originated* line is derived only from a predictive distribution
  supplied by the caller. It is never copied from, or anchored to, a market
  quote. Market quotes are handled separately by :func:`devig_two_way` and
  friends, and any comparison between the two is an explicit, later step.
* No parameter has a default value. If a caller cannot supply an authorised
  estimate, the constructor raises instead of substituting a plausible number.
* Rounding increments (the step used to publish a line) are market
  conventions. They are supplied by the caller from the market specification;
  this module never assumes one.

The maths implemented here is standard distributional arithmetic:

* fair spread  = expected margin (home points - away points)
* fair total   = expected home points + expected away points
* P(cover)     = 1 - F_margin(line) for the home side, F_margin(line) for away
* fair decimal price = 1 / P(win)
* net edge     = P(win) * decimal_price - 1   (stake 1 unit)
* de-vig       = removing the bookmaker margin from a two-way price pair
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal, Sequence

from .distributions import clamp, normal_cdf, normal_quantile

__all__ = [
    "GameScoreModel",
    "PlayerPropModel",
    "DevigMethod",
    "originate_spread",
    "originate_total",
    "cover_probability",
    "total_probability",
    "fair_decimal_price",
    "net_edge",
    "devig_two_way",
    "margin_of_two_way",
    "originate_prop_line",
    "prop_probability",
    "round_to_increment",
]

Side = Literal["home", "away", "over", "under"]
DevigMethod = Literal["multiplicative", "additive", "shin"]


@dataclass(frozen=True)
class GameScoreModel:
    """A pregame score distribution for one game.

    All fields must be supplied by the caller from an authorised model. The
    class deliberately has no defaults: an unset parameter is a bug, not a
    number to be guessed.
    """

    expected_home_points: float
    expected_away_points: float
    margin_sd: float
    total_sd: float
    model_version: str

    def __post_init__(self) -> None:
        if self.margin_sd <= 0 or self.total_sd <= 0:
            raise ValueError("margin_sd and total_sd must be positive")
        if not self.model_version:
            raise ValueError("model_version is required")

    @property
    def expected_margin(self) -> float:
        """Expected home-minus-away points."""
        return self.expected_home_points - self.expected_away_points

    @property
    def expected_total(self) -> float:
        """Expected combined points."""
        return self.expected_home_points + self.expected_away_points


@dataclass(frozen=True)
class PlayerPropModel:
    """Minutes x per-minute production model for one player prop.

    ``minutes_corr_with_rate`` is the correlation between the player's minutes
    and his per-minute output rate inside a game. A value of 0 means the two
    are treated as independent; the engine does not assume independence - the
    caller must supply the estimated value (or 0.0 explicitly) and record it.
    Like every field here it has no default: forgetting it is a bug, not an
    invitation to guess.
    """

    expected_minutes: float
    minutes_sd: float
    rate_mean: float
    rate_sd: float
    minutes_corr_with_rate: float
    model_version: str

    def __post_init__(self) -> None:
        if self.minutes_sd < 0 or self.rate_sd < 0:
            raise ValueError("standard deviations cannot be negative")
        if not -1.0 <= self.minutes_corr_with_rate <= 1.0:
            raise ValueError("minutes_corr_with_rate must lie in [-1, 1]")
        if not self.model_version:
            raise ValueError("model_version is required")

    @property
    def expected_total(self) -> float:
        """Expected stat total (minutes x per-minute rate)."""
        return self.expected_minutes * self.rate_mean

    @property
    def total_variance(self) -> float:
        """Variance of the product of minutes and rate, using the moments."""
        m, s = self.expected_minutes, self.minutes_sd
        mu, sr = self.rate_mean, self.rate_sd
        rho = self.minutes_corr_with_rate
        var_m = s * s
        var_r = sr * sr
        cov = rho * s * sr
        return (m * m) * var_r + (mu * mu) * var_m + 2 * m * mu * cov

    @property
    def total_sd(self) -> float:
        return math.sqrt(self.total_variance)


def round_to_increment(value: float, increment: float | None) -> float:
    """Round a line to the market's published increment.

    ``increment`` is supplied from the market specification (for example 0.5
    for a spread). ``None`` returns the unrounded value, which is what a model
    should store; rounding happens only at the publication step.
    """
    if increment is None:
        return value
    if increment <= 0:
        raise ValueError("increment must be positive")
    return round(value / increment) * increment


def originate_spread(model: GameScoreModel, increment: float | None = None) -> float:
    """Model-originated fair spread, expressed as home-minus-away points."""
    return round_to_increment(model.expected_margin, increment)


def originate_total(model: GameScoreModel, increment: float | None = None) -> float:
    """Model-originated fair game total."""
    return round_to_increment(model.expected_total, increment)


def cover_probability(model: GameScoreModel, line: float, side: Side) -> float:
    """Probability that a side covers a spread line.

    ``side='home'`` -> P(home margin + line > 0); ``side='away'`` is the
    complement. The distribution is the model-supplied normal margin.
    """
    if side not in ("home", "away"):
        raise ValueError("side must be 'home' or 'away'")
    p_home = 1.0 - normal_cdf(-line, model.expected_margin, model.margin_sd)
    return p_home if side == "home" else 1.0 - p_home


def total_probability(model: GameScoreModel, line: float, side: Side) -> float:
    """Probability that the combined score is over/under a total line."""
    if side not in ("over", "under"):
        raise ValueError("side must be 'over' or 'under'")
    p_over = 1.0 - normal_cdf(line, model.expected_total, model.total_sd)
    return p_over if side == "over" else 1.0 - p_over


def fair_decimal_price(probability: float) -> float:
    """Decimal price that is fair for a probability (no margin)."""
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must lie strictly between 0 and 1")
    return 1.0 / probability


def net_edge(probability: float, decimal_price: float) -> float:
    """Net return per unit staked when a fair probability is offered a price."""
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must lie strictly between 0 and 1")
    if decimal_price <= 1.0:
        raise ValueError("decimal_price must be greater than 1.0")
    return probability * decimal_price - 1.0


def margin_of_two_way(price_a: float, price_b: float) -> float:
    """Bookmaker margin of a two-way market, as a fraction of stake."""
    if price_a <= 1.0 or price_b <= 1.0:
        raise ValueError("prices must be greater than 1.0")
    return (1.0 / price_a + 1.0 / price_b) - 1.0


def devig_two_way(
    price_a: float,
    price_b: float,
    method: DevigMethod = "multiplicative",
    shin_z: float | None = None,
) -> tuple[float, float]:
    """Remove the bookmaker margin from a two-way price pair.

    Returns the implied probabilities for side A and side B. The methods are
    the standard published transformations; the *choice* of method is a market
    decision that must be declared in the market specification before any
    comparison is made.

    * ``multiplicative`` - proportional: p_a = (1/price_a) / sum(1/price).
    * ``additive``     - subtract the margin evenly from both sides.
    * ``shin``         - Shin's method, which protects the favourite-longshot
      bias; ``shin_z`` is the insider-trading parameter and must be supplied.
    """
    if price_a <= 1.0 or price_b <= 1.0:
        raise ValueError("prices must be greater than 1.0")
    implied_a = 1.0 / price_a
    implied_b = 1.0 / price_b
    total = implied_a + implied_b
    if method == "multiplicative":
        return implied_a / total, implied_b / total
    if method == "additive":
        margin = total - 1.0
        return max(0.0, implied_a - margin / 2.0), max(0.0, implied_b - margin / 2.0)
    if method == "shin":
        if shin_z is None:
            raise ValueError("shin_z must be supplied for the shin method")
        return _shin_devig(implied_a, implied_b, shin_z)
    raise ValueError(f"unknown de-vig method: {method!r}")


def _shin_devig(implied_a: float, implied_b: float, z: float) -> tuple[float, float]:
    """Shin's method for removing the favourite-longshot bias.

    With overround ``S = p_a + p_b`` and the insider-trading parameter ``z``,
    Shin's transformation gives, for each side::

        p_i = (sqrt(z^2 + 4 (1 - z) p_i^2 / S) - z) / (2 (1 - z))

    The two results are then normalised so that they sum to one.
    """
    if z <= 0:
        raise ValueError("shin_z must be positive")
    total = implied_a + implied_b
    if total <= 0:
        raise ValueError("invalid price pair")
    transformed: list[float] = []
    for implied in (implied_a, implied_b):
        value = (
            math.sqrt(z * z + 4 * (1 - z) * (implied * implied) / total) - z
        ) / (2 * (1 - z))
        transformed.append(max(0.0, value))
    scale = sum(transformed)
    if scale <= 0:
        raise ValueError("invalid price pair")
    return clamp(transformed[0] / scale), clamp(transformed[1] / scale)


def originate_prop_line(
    model: PlayerPropModel,
    quantile: float = 0.5,
    increment: float | None = None,
) -> float:
    """Model-originated player-prop line at a given quantile of the total.

    The default quantile is the median of the predictive distribution. A median
    line is a statement about the centre of the distribution; it is not a claim
    about the most likely single value.
    """
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must lie strictly between 0 and 1")
    mean = model.expected_total
    sd = model.total_sd
    if sd == 0:
        return round_to_increment(mean, increment)
    return round_to_increment(normal_quantile(quantile, mean, sd), increment)


def prop_probability(model: PlayerPropModel, line: float, over: bool = True) -> float:
    """Probability that a player prop finishes over (or under) a line."""
    mean = model.expected_total
    sd = model.total_sd
    if sd == 0:
        p_over = 1.0 if mean > line else (0.5 if mean == line else 0.0)
    else:
        p_over = 1.0 - normal_cdf(line, mean, sd)
    return p_over if over else 1.0 - p_over


def expected_correlation_from_pairs(pairs: Iterable[tuple[float, float]]) -> float:
    """Average of supplied (x, y) pairs - a helper for tests and diagnostics."""
    values = [r for x, y in pairs for r in (x, y)]
    if not values:
        raise ValueError("no pairs supplied")
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    return math.sqrt(var) if var > 0 else 0.0


def summarise_probabilities(probabilities: Sequence[float]) -> dict[str, float]:
    """Small helper for reporting a set of probabilities (mean, min, max)."""
    if not probabilities:
        return {"mean": float("nan"), "min": float("nan"), "max": float("nan")}
    return {
        "mean": sum(probabilities) / len(probabilities),
        "min": min(probabilities),
        "max": max(probabilities),
    }
