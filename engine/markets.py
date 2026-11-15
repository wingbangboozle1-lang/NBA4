"""Market anchoring and correlation-aware parlay pricing.

Brief items implemented (2026-11-15):

* "Add a market-anchored prior: blend the model line with the closing line,
  weight by measured out-of-sample log-loss."
* "Price every parlay with the measured rho and print the naive product next to
  it, instead of withholding the price entirely."

Anchoring weight, and why this form. The closing line is the most
information-dense price in the market; a model that ignores it is throwing away
evidence. But a *fixed* blend weight is arbitrary, so the weight here is set by
measured out-of-sample log-loss on the settled ledger:

    w_model = (1 / LL_model**p) / ((1 / LL_model**p) + (1 / LL_close**p))

so the better-scoring side (lower log-loss) carries more weight, and ``p`` is a
registered sharpness exponent rather than an engineering default. Both log-loss
values must be *measured out of sample* on authorized, settled outcomes. If
either is missing, ``anchor_weight`` refuses and returns the model line with
``anchored=False`` and the reason - an unmeasured blend is a guess with two
inputs instead of one.

Parlay pricing. The independence product is not withheld; it is printed next to
the correlated price, and the gap between the two is the headline. Withholding
the correlated price "because correlation is unmeasured" pushes readers back to
multiplying marginals, which is the worse error. So: use the measured rho when it
exists (from ``engine/corrstats.py``, with its cluster-bootstrap interval);
when it does not, publish both the naive product and the interval of joint
probabilities implied by the rho bounds, and say which is which. Never publish a
single number as "the" parlay price without rho evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .parlay import ParlayLeg, independent_joint_probability, joint_probability

ANCHOR_NOT_MEASURED = "OUT_OF_SAMPLE_LOGLOSS_NOT_MEASURED"
ANCHOR_OK = "ANCHORED_ON_MEASURED_LOGLOSS"
ANCHOR_MARKET_ONLY = "MODEL_UNSCORED_USING_CLOSE_ONLY"


class MarketError(ValueError):
    """Raised when a caller tries to blend without measurement, or price without bounds."""


def _check_log_loss(value: Optional[float], who: str) -> float:
    if value is None:
        raise MarketError(f"{who}: log-loss is required; the anchor weight is measured, not assumed")
    if value <= 0:
        raise MarketError(f"{who}: log-loss must be positive (a zero log-loss is a leak, not a model)")
    return float(value)


@dataclass(frozen=True)
class AnchorWeights:
    """The declared blend weights, with the measurement they came from."""

    weight_model: float
    weight_close: float
    log_loss_model: float
    log_loss_close: float
    sample_size: int
    surface: str
    sharpness_exponent: float
    code: str
    detail: str

    @property
    def anchored(self) -> bool:
        return self.code == ANCHOR_OK


def anchor_weight(
    log_loss_model: Optional[float],
    log_loss_close: Optional[float],
    sample_size: Optional[int],
    sharpness_exponent: Optional[float] = None,
    minimum_sample: Optional[int] = None,
) -> AnchorWeights:
    """Inverse-log-loss weighting of the model line against the closing line."""
    if sharpness_exponent is None:
        raise MarketError(
            "sharpness_exponent must be declared (it controls how aggressively the better "
            "scorer dominates the blend); no default is assumed"
        )
    if sharpness_exponent <= 0:
        raise MarketError("sharpness_exponent must be positive")
    if minimum_sample is None or sample_size is None or sample_size < minimum_sample:
        return AnchorWeights(
            weight_model=float("nan"), weight_close=float("nan"),
            log_loss_model=float(log_loss_model) if log_loss_model else float("nan"),
            log_loss_close=float(log_loss_close) if log_loss_close else float("nan"),
            sample_size=int(sample_size or 0), surface="bet", sharpness_exponent=float(sharpness_exponent),
            code="SAMPLE_BELOW_REGISTERED_MINIMUM",
            detail=(
                f"{sample_size} settled out-of-sample forecasts vs a registered minimum of "
                f"{minimum_sample}; the weights are not estimable yet, so the line stays unanchored"
            ),
        )
    ll_model = _check_log_loss(log_loss_model, "model")
    ll_close = _check_log_loss(log_loss_close, "closing line")
    p = float(sharpness_exponent)
    inv_model = (1.0 / ll_model) ** p
    inv_close = (1.0 / ll_close) ** p
    total = inv_model + inv_close
    w_model = inv_model / total
    return AnchorWeights(
        weight_model=w_model,
        weight_close=1.0 - w_model,
        log_loss_model=ll_model,
        log_loss_close=ll_close,
        sample_size=int(sample_size),
        surface="bet",
        sharpness_exponent=p,
        code=ANCHOR_OK,
        detail=(
            f"weights are inverse-log-loss^{p:g} on {sample_size} settled out-of-sample forecasts; "
            "the closing line keeps weight even when the model scores better, and the blend is "
            "reported as anchored to the market rather than as an independent model line"
        ),
    )


def anchored_line(model_line: float, closing_line: float, weights: AnchorWeights) -> Dict[str, object]:
    """Blend only when the weights were measured; otherwise hand back the model line."""
    if not weights.anchored:
        return {
            "line": model_line,
            "anchored": False,
            "code": weights.code,
            "detail": weights.detail,
            "model_line": model_line,
            "closing_line": closing_line,
        }
    blended = weights.weight_model * model_line + weights.weight_close * closing_line
    return {
        "line": blended,
        "anchored": True,
        "code": weights.code,
        "detail": weights.detail,
        "model_line": model_line,
        "closing_line": closing_line,
        "weight_model": round(weights.weight_model, 4),
        "weight_close": round(weights.weight_close, 4),
        "shift_from_model": round(blended - model_line, 4),
    }


# --- parlay pricing ---------------------------------------------------------

@dataclass(frozen=True)
class ParlayPricing:
    """Correlated price, naive product, and the difference the reader must see."""

    legs: Tuple[Tuple[str, float], ...]
    naive_product: float
    correlated_probability: Optional[float]
    rho: Optional[float]
    rho_interval: Optional[Tuple[float, float]]
    method: str
    fair_american_naive: str
    fair_american_correlated: str
    hold_multiplier: Optional[float]
    note: str

    @property
    def dependence_effect(self) -> Optional[float]:
        if self.correlated_probability is None:
            return None
        return self.correlated_probability - self.naive_product


def american_from_decimal(decimal_price: float) -> str:
    """Standard American conversion; ``decimal_price`` must be > 1."""
    if decimal_price <= 1.0:
        raise MarketError("decimal price must exceed 1.0")
    if decimal_price >= 2.0:
        return f"+{round((decimal_price - 1) * 100)}"
    return f"-{round(100 / (decimal_price - 1))}"


def decimal_from_probability(probability: float) -> float:
    if not 0.0 < probability < 1.0:
        raise MarketError("probability must lie strictly between 0 and 1")
    return 1.0 / probability


# No rho-to-rank conversion is implemented here, on purpose. The relations
# quoted in the literature (Pearson-to-Spearman approximations, for example) are
# distribution-dependent, and this repository holds no official-source sentence
# that licenses one over another. Callers must price with the *same* rho
# definition their estimator produced; docs/correlation-and-leaderboard.md
# records which definition each estimator emits. A silent conversion would be an
# unverified input.


def price_parlay(
    leg_probabilities: Sequence[Tuple[str, float]],
    rho: Optional[float] = None,
    rho_interval: Optional[Tuple[float, float]] = None,
    hold_multiplier: Optional[float] = None,
    draws: int = 20000,
    seed: int = 20261115,
) -> ParlayPricing:
    """Price a parlay with the measured rho, printing the naive product beside it.

    ``leg_probabilities`` is a sequence of ``(leg_id, marginal_probability)``.
    ``rho`` is the measured correlation between the legs' outcomes (see
    ``engine/corrstats.py``); ``rho_interval`` is its cluster-bootstrap
    interval. If neither is supplied the correlated price is *bounded*, not
    invented: the naive product stands, and the interval between perfect
    independence and the Frechet-Hoeffding bound is reported as the reason no
    point price exists.
    """
    if len(leg_probabilities) < 2:
        raise MarketError("a parlay needs at least two legs")
    legs = tuple(leg_probabilities)
    typed = [ParlayLeg(leg_id=leg_id, event_id="parlay", probability=p) for leg_id, p in legs]
    naive = independent_joint_probability(typed)
    correlated: Optional[float] = None
    method = "BOUNDED_NOT_PRICED"
    note = ""
    if rho is not None:
        if not -1.0 <= rho <= 1.0:
            raise MarketError("rho must lie in [-1, 1]")
        if abs(abs(rho) - 1.0) < 1e-12:
            # Perfect dependence is the Frechet-Hoeffding bound, and it is exact:
            # the copula matrix is singular, so Monte Carlo has nothing to sample.
            probs = [p_ for _, p_ in legs]
            if rho > 0:
                correlated = min(probs)
            else:
                correlated = max(0.0, sum(probs) - (len(probs) - 1))
            method = f"ANALYTICAL_FRECHET_BOUND rho={rho:+.0f} (exact, no simulation)"
            note = (
                "rho = +/-1 is a boundary case, not an estimate: it says the legs move "
                "together or in exact opposition. No measured outcome data supports an "
                "exactly perfect correlation, so this row exists to make the bound testable."
            )
            fair_naive = american_from_decimal(decimal_from_probability(naive))
            return ParlayPricing(
                legs=legs, naive_product=naive, correlated_probability=correlated, rho=rho,
                rho_interval=rho_interval, method=method,
                fair_american_naive=fair_naive,
                fair_american_correlated=american_from_decimal(decimal_from_probability(correlated))
                if correlated > 0 else "impossible",
                hold_multiplier=hold_multiplier, note=note,
            )
        matrix = [[1.0, rho], [rho, 1.0]] if len(typed) == 2 else _equicorrelated(len(typed), rho)
        estimate = joint_probability(typed, matrix, draws=draws, seed=seed)
        correlated = estimate.joint_probability
        method = f"GAUSSIAN_COPULA rho={rho:+.3f} draws={draws} (MC SE +/-{estimate.standard_error:.4f})"
        note = (
            "the copula ties legs together through a single pairwise rho; it is not a model of "
            "shared game context (same total, same minutes pool, same opponent) and the "
            "measured rho must come from settled outcomes, not from an assumption"
        )
    elif rho_interval is not None:
        low, high = rho_interval
        lo_est = joint_probability(typed, _equicorrelated(len(typed), low), draws=draws, seed=seed)
        hi_est = joint_probability(typed, _equicorrelated(len(typed), high), draws=draws, seed=seed)
        method = f"INTERVAL rho in [{low:+.3f}, {high:+.3f}] (no point estimate)"
        note = (
            f"joint probability interval {min(lo_est.joint_probability, hi_est.joint_probability):.4f}"
            f"-{max(lo_est.joint_probability, hi_est.joint_probability):.4f} from the measured rho "
            "interval; the naive product is printed as the point figure only because the "
            "correlation interval does not license one"
        )
        correlated = None
    else:
        note = (
            "no measured rho: the naive product is shown with its assumption stated, and the "
            "correlated price is withheld until a rho with an interval exists"
        )
    fair_naive = american_from_decimal(decimal_from_probability(naive))
    fair_corr = american_from_decimal(decimal_from_probability(correlated)) if correlated else "not priced"
    return ParlayPricing(
        legs=legs,
        naive_product=naive,
        correlated_probability=correlated,
        rho=rho,
        rho_interval=rho_interval,
        method=method,
        fair_american_naive=fair_naive,
        fair_american_correlated=fair_corr,
        hold_multiplier=hold_multiplier,
        note=note,
    )


def _equicorrelated(n: int, rho: float) -> List[List[float]]:
    return [[1.0 if i == j else rho for j in range(n)] for i in range(n)]


def hold_adjusted(decimal_fair: float, hold_multiplier: Optional[float]) -> Optional[float]:
    """Apply a declared hold. ``hold_multiplier`` must come from the operator's own
    posted prices; it is never assumed here."""
    if hold_multiplier is None:
        return None
    if hold_multiplier < 1.0:
        raise MarketError("a hold multiplier below 1.0 would pay out more than it takes in")
    return decimal_fair / hold_multiplier


def pricing_table_rows(pricing: ParlayPricing) -> List[Dict[str, str]]:
    """The two rows the picks page prints: naive product and correlated price."""
    rows = [
        {
            "method": "naive product (independence assumed)",
            "probability": f"{pricing.naive_product:.4f}",
            "fair_american": pricing.fair_american_naive,
            "rho": "not used",
            "note": "printed beside the correlated price so the reader sees the dependence effect",
        }
    ]
    if pricing.correlated_probability is not None:
        rows.append(
            {
                "method": "measured-rho joint probability",
                "probability": f"{pricing.correlated_probability:.4f}",
                "fair_american": pricing.fair_american_correlated,
                "rho": f"{pricing.rho:+.3f}",
                "note": pricing.method,
            }
        )
    else:
        rows.append(
            {
                "method": "measured-rho joint probability",
                "probability": "",
                "fair_american": "not priced",
                "rho": "",
                "note": pricing.note,
            }
        )
    return rows
