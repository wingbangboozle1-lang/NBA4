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
    thresholds = [normal_quantile(leg.probability) for leg in legs]
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


# ---------------------------------------------------------------------------
# Ticket resolution under the push/void rule, and the correlation (rho) feed.
# Added under task AN: the module could price a joint event but could not say
# what happens to a ticket when a leg pushes, is voided, or has not settled.
# ---------------------------------------------------------------------------

__all__ += [
    "SETTLED_STATES",
    "LEG_STATES",
    "PUSH_RULE",
    "TicketLeg",
    "resolve_ticket",
    "rho_from_feed",
]

#: States an official result document can settle a leg into, as printed.
SETTLED_STATES = ("HIT", "MISS", "PUSH", "VOID")
#: Plus the one state that is not a result: the document has not printed one yet.
LEG_STATES = SETTLED_STATES + ("UNSETTLED",)

#: Push/void rule as published on the site. A push or a void removes the leg and the
#: ticket re-prices on what remains; it is never scored as a win, and a ticket with
#: no live legs has no outcome to report. An unsettled leg blocks the whole ticket.
PUSH_RULE = (
    "A PUSH or VOID leg is removed and the ticket re-prices on the remaining legs at their "
    "original odds; a MISS makes the ticket a MISS; an UNSETTLED leg blocks the ticket."
)


@dataclass(frozen=True)
class TicketLeg:
    """One leg with its settlement state and its original price.

    ``american_odds`` is used only to re-express a reduced ticket's price when every
    remaining leg is priced; an unpriced leg is reported as unpriced, never as even
    money.
    """

    leg_id: str
    state: str
    american_odds: float | None = None
    settled_from: str = ""  # official document URL that printed the result

    def __post_init__(self) -> None:
        if self.state not in LEG_STATES:
            raise ValueError(
                f"leg state must be one of {LEG_STATES}; {self.state!r} is not a settlement state"
            )
        if not str(self.settled_from).startswith("https://"):
            raise ValueError(
                f"{self.leg_id}: settled_from must be an https:// official URL; a leg with no citable result "
                "document is not a settled leg"
            )


def _decimal(american: float) -> float:
    """American price to decimal, the arithmetic a reader can check by hand."""
    if american == 0:
        raise ValueError("american odds cannot be zero")
    return 1.0 + (100.0 / abs(american) if american < 0 else american / 100.0)


def resolve_ticket(legs: Sequence[TicketLeg]) -> dict[str, object]:
    """Apply the push/void rule to a ticket and report only what is settled.

    ``outcome`` is HIT when every live leg hit, MISS when any live leg missed,
    ``BLOCKED`` while a leg is UNSETTLED, and ``ALL_LEGS_REMOVED`` when every leg
    pushed or voided (no outcome is invented for that case).
    """
    if not legs:
        raise ValueError("at least one leg is required")
    blocked = [leg.leg_id for leg in legs if leg.state == "UNSETTLED"]
    removed = [leg.leg_id for leg in legs if leg.state in ("PUSH", "VOID")]
    live = [leg for leg in legs if leg.state not in ("PUSH", "VOID")]
    priced = [leg for leg in live if leg.american_odds is not None and leg.state in SETTLED_STATES]
    combined = 1.0
    for leg in priced:
        combined *= _decimal(float(leg.american_odds))
    if blocked:
        outcome = "BLOCKED"
    elif any(leg.state == "MISS" for leg in live):
        outcome = "MISS"
    elif not live:
        outcome = "ALL_LEGS_REMOVED"
    elif all(leg.state == "HIT" for leg in live):
        outcome = "HIT"
    else:  # pragma: no cover - every state is covered above
        outcome = "BLOCKED"
    full = bool(priced) and len(priced) == len(live) and outcome in ("HIT", "MISS")
    return {
        "outcome": outcome,
        "legs": len(legs),
        "live_legs": len(live),
        "removed_legs": removed,
        "reduced_legs": [leg.leg_id for leg in live],
        "blocked_legs": blocked,
        "rule": PUSH_RULE,
        "priced_legs": len(priced),
        "combined_decimal": round(combined, 4) if full else None,
        "note": (
            "product of the remaining legs' printed decimal equivalents"
            if full
            else "combined price omitted: a live leg has no printed price, or the ticket is not settled, "
            "so no price is invented"
        ),
        "source_urls": sorted({leg.settled_from for leg in legs}),
    }


def rho_from_feed(
    pairs: "dict[tuple[str, str], Sequence[tuple[float, float]]]",
    *,
    prior: float = 0.0,
    prior_weight: float = 0.0,
    min_pairs: int = 20,
) -> dict[str, object]:
    """Estimate the leg-pair correlation rho that :func:`joint_probability` consumes.

    ``pairs`` maps a leg-pair to aligned (leg_a, leg_b) observations from a licensed
    results feed. A pair with fewer than ``min_pairs`` observations gets no published
    estimate: the caller is told the sample is too small and which value was used
    instead, so a same-game parlay is never priced as if independent by silence.
    """
    from .correlation import pearson, shrink  # local import keeps parlay's import cost low

    out: dict[str, float] = {}
    refusals: list[dict[str, object]] = []
    for key, rows in pairs.items():
        label = "|".join(sorted(key))
        if len(rows) < min_pairs:
            refusals.append(
                {
                    "pair": list(key),
                    "observations": len(rows),
                    "required": min_pairs,
                    "rho_used": prior,
                    "basis": "no estimate published; the configured prior stands in and is reported as such",
                }
            )
            out[label] = prior
            continue
        xs = [float(a) for a, _ in rows]
        ys = [float(b) for _, b in rows]
        out[label] = round(shrink(pearson(xs, ys), prior, prior_weight), 4)
    return {
        "rho": out,
        "refusals": refusals,
        "prior": prior,
        "prior_weight": prior_weight,
        "min_pairs": min_pairs,
        "note": "shrink(estimate, prior, prior_weight): prior_weight 0.0 uses the raw estimate unshrunk, "
        "and prior 0.0 means no pull toward independence",
    }
