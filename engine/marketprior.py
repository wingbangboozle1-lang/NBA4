"""Market prices as a model *prior*, under the rights gate (task AN, gap 10).

Two separate questions, kept separate here on purpose:

1. **Do we have the right to use it?** ``engine/contracts.require_allowed_use``
   (gate G0) implements the NBA Terms of Use position that Statistics may not be used
   in connection with any gambling activity. A market quote — or any derived
   probability — is a *gambling* input, so it can enter a published bet surface only
   when that gate has cleared, which today it has not (COORDINATION.md IR-T4).
2. **What does the price imply?** :func:`implied_probability` does that arithmetic
   for a two-way market: remove the vig by normalising the two sides, and optionally
   shrink the model toward the no-vig price with a preregistered weight
   (``engine/correlation.shrink``).

This module will compute the implied probability for *audit* purposes when the quote
is a recorded observation (the snapshot documents the line as published, which is
news reporting), but :func:`prior_or_refusal` refuses to feed it into anything the
site presents as a bet unless the caller passes ``rights_cleared=True`` **and** a
quote whose ``allowed_use`` field says so. A refusal here is a fact about
licensing, not about the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .contracts import require_allowed_use
from .correlation import shrink
from .inputs import MissingInput, official_link, require

__all__ = ["Quote", "implied_probability", "no_vig_pair", "prior_or_refusal", "NO_AUTHORISATION"]

NO_AUTHORISATION = "NO AUTHORISATION"


@dataclass(frozen=True)
class Quote:
    """One printed market price, with the document that printed it."""

    leg_id: str
    side: str  # e.g. "HOME", "AWAY", "OVER", "UNDER"
    american_odds: float | None = None
    decimal_odds: float | None = None
    implied_probability: float | None = None  # when the source prints it directly
    source_url: str = ""
    source_time: str = ""
    observed_at: str = ""
    allowed_use: str = ""
    provider: str = ""

    def probability(self) -> float:
        """Convert the printed price to a probability. Arithmetic, not modelling."""
        if self.implied_probability is not None:
            p = float(self.implied_probability)
        elif self.decimal_odds:
            p = 1.0 / float(self.decimal_odds)
        elif self.american_odds:
            a = float(self.american_odds)
            # +130 pays 1.30 on 1 -> p = 100/(130+100); -150 pays 1.00 on 1.50 -> p = 150/(150+100)
            p = 100.0 / (a + 100.0) if a > 0 else -a / (-a + 100.0)
        else:
            raise MissingInput(
                f"{self.leg_id}/{self.side}: the quote prints no price, so no probability is derived; a "
                "close-to-even default is not substituted"
            )
        if not 0.0 < p < 1.0:
            raise MissingInput(f"{self.leg_id}/{self.side}: price converts to {p}, outside (0, 1)")
        return p


def no_vig_pair(home: Quote, away: Quote) -> dict[str, Any]:
    """Strip the vig by normalising two sides; refuses if they do not sum sensibly."""
    ph, pa = home.probability(), away.probability()
    total = ph + pa
    if total <= 1.0:
        raise MissingInput(
            f"{home.leg_id}: the two sides sum to {total:.4f}, which is not over 1.00 — a two-way market with "
            "no vig is not what was printed, so the normalisation is refused"
        )
    return {
        "leg_id": home.leg_id,
        "raw_home": round(ph, 4),
        "raw_away": round(pa, 4),
        "overround": round(total - 1.0, 4),
        "novig_home": round(ph / total, 4),
        "novig_away": round(pa / total, 4),
        "rule": "each side divided by the sum of both sides; no juice model, no hold estimate",
        "source_url": official_link(home.source_url or away.source_url, where=f"{home.leg_id} quote pair"),
    }


def implied_probability(quote: Quote, *, purpose: str = "audit of a published line") -> dict[str, Any]:
    """Report what a printed price implies, with the purpose recorded verbatim."""
    require(purpose, "purpose", needed_for=f"{quote.leg_id} implied probability")
    return {
        "leg_id": quote.leg_id,
        "side": quote.side,
        "implied_probability": round(quote.probability(), 4),
        "purpose": purpose,
        "source_url": quote.source_url,
        "source_time": quote.source_time,
        "observed_at": quote.observed_at,
    }


def prior_or_refusal(
    model_p: float,
    quotes: Sequence[Quote],
    *,
    weight: float,
    rights_cleared: bool,
    pre_registered: bool,
    source_url: str = "",
) -> dict[str, Any]:
    """Blend the model with the no-vig market price, or refuse and say what is missing.

    ``weight`` is the preregistered shrinkage toward the market (0 = model only,
    1 = market only) and must be inside [0, 1]; the refusal path returns
    :data:`NO_AUTHORISATION` with no blended number at all.
    """
    require(quotes, "market quotes", needed_for="a market prior")
    if not 0.0 <= weight <= 1.0:
        raise MissingInput(f"shrinkage weight {weight} is not inside [0, 1]")
    legs: dict[str, list[Quote]] = {}
    for quote in quotes:
        legs.setdefault(quote.leg_id, []).append(quote)
    priors, refusals = {}, []
    for leg_id, pair in legs.items():
        try:
            require_allowed_use(pair[0], purpose="model input / bet surface")
        except Exception as exc:  # RightsError and any contract failure are refusals
            refusals.append({"leg_id": leg_id, "status": NO_AUTHORISATION, "reason": str(exc)})
            continue
        if len(pair) != 2:
            refusals.append(
                {"leg_id": leg_id, "status": "INCOMPLETE", "reason": f"{len(pair)} of 2 sides printed"}
            )
            continue
        try:
            market = no_vig_pair(*pair)
        except MissingInput as exc:
            refusals.append({"leg_id": leg_id, "status": "REFUSED", "reason": str(exc)})
            continue
        if not (rights_cleared and pre_registered):
            refusals.append(
                {
                    "leg_id": leg_id,
                    "status": NO_AUTHORISATION,
                    "reason": "rights gate G0 or the pre-registration gate has not cleared this run, so the "
                    "market prior is not applied to any published number",
                }
            )
            continue
        market_p = market["novig_home"] if pair[0].side.upper() == "HOME" else market["novig_away"]
        priors[leg_id] = {
            "model_p": round(model_p, 4),
            "market_p": market_p,
            "prior_weight": weight,
            "blended_p": round(shrink(model_p, market_p, weight), 4),
            "source_url": market["source_url"],
        }
    return {
        "priors": priors,
        "refusals": refusals,
        "surface": "model only" if not priors else "model + market",
        "gate": {"rights_cleared": rights_cleared, "pre_registered": pre_registered},
    }
