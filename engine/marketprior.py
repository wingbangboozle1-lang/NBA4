"""Market-anchored prior for the originated line.

The brief requires a market-anchored prior: the model line is blended with
the closing line, and the weights come from the **measured out-of-sample
log loss** of each side.  The blend is never allowed to be a free choice.

Rules enforced here:

* both log losses must be *measured* out-of-sample; a missing log loss
  produces no blend and a note, never a default weight;
* the weight is inverse log loss, so the better-scoring side (lower log
  loss) receives the larger weight;
* the unblended model value is returned beside the blend so a reader can see
  what the market contributed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

__all__ = [
    "MarketBlend",
    "blend_with_market",
    "blend_probability",
    "logit",
    "expit",
]


def logit(p: float) -> float:
    """Log-odds of a probability, clipped away from 0 and 1."""
    p = min(max(p, 1e-12), 1 - 1e-12)
    return math.log(p / (1 - p))


def expit(x: float) -> float:
    """Inverse of :func:`logit`."""
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class MarketBlend:
    """The blended value and the weights that produced it."""

    blended_value: Optional[float]
    model_value: Optional[float]
    market_value: Optional[float]
    weight_model: Optional[float]
    weight_market: Optional[float]
    notes: Tuple[str, ...] = ()

    @property
    def is_blended(self) -> bool:
        return self.blended_value is not None


def _weights(
    model_log_loss: Optional[float], market_log_loss: Optional[float]
) -> Tuple[Optional[float], Optional[float], Tuple[str, ...]]:
    notes = []
    if model_log_loss is None or market_log_loss is None:
        notes.append(
            "measured out-of-sample log loss is missing for one side, so no "
            "market-anchored prior is applied"
        )
        return None, None, tuple(notes)
    if model_log_loss <= 0 or market_log_loss <= 0:
        raise ValueError("log losses must be positive")
    w_model = 1.0 / model_log_loss
    w_market = 1.0 / market_log_loss
    total = w_model + w_market
    notes.append(
        "weights are inverse measured out-of-sample log loss "
        f"(model={model_log_loss:.4f}, market={market_log_loss:.4f})"
    )
    return w_model / total, w_market / total, tuple(notes)


def blend_with_market(
    model_line: Optional[float],
    market_line: Optional[float],
    model_log_loss: Optional[float],
    market_log_loss: Optional[float],
) -> MarketBlend:
    """Blend a model-originated line with the closing line.

    The blend is a straight convex combination of the two line values, with
    the weight set by the measured out-of-sample log loss of each side.
    """
    notes = []
    if model_line is None or market_line is None:
        notes.append("model line or closing line is missing; nothing is blended")
        return MarketBlend(None, model_line, market_line, None, None, tuple(notes))
    w_model, w_market, w_notes = _weights(model_log_loss, market_log_loss)
    notes.extend(w_notes)
    if w_model is None or w_market is None:
        return MarketBlend(None, model_line, market_line, None, None, tuple(notes))
    blended = w_model * model_line + w_market * market_line
    notes.append(
        "the unblended model line is kept beside the blend so the market's "
        "contribution is visible"
    )
    return MarketBlend(blended, model_line, market_line, w_model, w_market, tuple(notes))


def blend_probability(
    model_probability: Optional[float],
    market_probability: Optional[float],
    model_log_loss: Optional[float],
    market_log_loss: Optional[float],
) -> MarketBlend:
    """Blend two probabilities in log-odds space.

    Probabilities are blended on the log-odds scale, because a convex
    combination of probabilities distorts the tails and is not the same
    object as a convex combination of log losses.
    """
    notes = []
    if model_probability is None or market_probability is None:
        notes.append("model or market probability is missing; nothing is blended")
        return MarketBlend(None, model_probability, market_probability, None, None, tuple(notes))
    w_model, w_market, w_notes = _weights(model_log_loss, market_log_loss)
    notes.extend(w_notes)
    if w_model is None or w_market is None:
        return MarketBlend(
            None, model_probability, market_probability, None, None, tuple(notes)
        )
    blended_logit = w_model * logit(model_probability) + w_market * logit(market_probability)
    notes.append("the blend is computed on the log-odds scale and mapped back")
    return MarketBlend(
        expit(blended_logit),
        model_probability,
        market_probability,
        w_model,
        w_market,
        tuple(notes),
    )
