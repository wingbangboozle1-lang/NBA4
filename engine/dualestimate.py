"""Model-vs-market disagreement, counted rather than averaged away (task AN, gap 5).

The brief wants the model and the market kept as *two estimates* and their
disagreement measured, not blended silently. Two things are computed here:

1. :func:`compare` — one (model, market) pair: the difference in probability
   points, the same difference scaled by the model's predictive sd, and a band
   label. The band edges are the published constants below, not tuned.
2. :func:`disagreement_statistics` — the distribution of pairs across bands, with
   per-variant counts, and a refusal to report a mean when the sample is smaller
   than :data:`MIN_PAIRS`.

No market value is ever assumed: if a leg has no quote, :func:`compare` raises
:class:`~engine.inputs.MissingInput` and :func:`bands_from_records` counts the leg
under ``NO MARKET`` without inventing a number for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .inputs import NO_INPUT, MissingInput, official_link, require, require_min

__all__ = [
    "BAND_EDGES",
    "MIN_PAIRS",
    "Pair",
    "Comparison",
    "compare",
    "disagreement_statistics",
    "bands_from_records",
]

# |model p - market p| in probability points; the top band is "large disagreement".
BAND_EDGES: tuple[float, ...] = (0.02, 0.05, 0.10)
BAND_NAMES: tuple[str, ...] = ("AGREE (<=2pt)", "SMALL (2-5pt)", "MEDIUM (5-10pt)", "LARGE (>10pt)")
MIN_PAIRS = 10  # PROPOSED: below this the distribution is a count only, no mean


@dataclass(frozen=True)
class Pair:
    leg_id: str
    variant: str  # which model variant produced the estimate
    model_p: float
    market_p: float | None
    model_sd: float | None = None  # predictive sd in probability points, when carried

    def validated(self) -> "Pair":
        require(self.leg_id, "leg_id", needed_for="a model-vs-market pair")
        require(self.variant, "variant", needed_for="a model-vs-market pair")
        if not 0.0 <= self.model_p <= 1.0:
            raise MissingInput(f"{self.leg_id}: model probability {self.model_p} is not inside [0, 1]")
        if self.market_p is not None and not 0.0 <= self.market_p <= 1.0:
            raise MissingInput(f"{self.leg_id}: market probability {self.market_p} is not inside [0, 1]")
        return self


@dataclass(frozen=True)
class Comparison:
    leg_id: str
    variant: str
    model_p: float
    market_p: float | None
    difference: float | None  # model minus market, probability points
    band: str
    z: float | None
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "leg_id": self.leg_id,
            "variant": self.variant,
            "model_p": self.model_p,
            "market_p": self.market_p,
            "difference": None if self.difference is None else round(self.difference, 4),
            "band": self.band,
            "z": None if self.z is None else round(self.z, 3),
            "note": self.note,
        }


def _band(absolute_difference: float) -> str:
    for edge, name in zip(BAND_EDGES, BAND_NAMES[:-1]):
        if absolute_difference <= edge:
            return name
    return BAND_NAMES[-1]


def compare(pair: Pair, *, margin_sd_points: float | None = None) -> Comparison:
    """Label one pair. Refuses when the market side is missing."""
    pair.validated()
    if pair.market_p is None:
        raise MissingInput(
            f"{pair.leg_id}: no market probability for this leg, so no disagreement is computed; the leg is "
            "counted under NO MARKET instead"
        )
    diff = pair.model_p - pair.market_p
    z = None
    sd = pair.model_sd if pair.model_sd is not None else margin_sd_points
    if sd is not None:
        if sd <= 0:
            raise MissingInput(f"{pair.leg_id}: sd must be positive to scale a difference")
        z = diff / sd
    return Comparison(
        leg_id=pair.leg_id,
        variant=pair.variant,
        model_p=pair.model_p,
        market_p=pair.market_p,
        difference=diff,
        band=_band(abs(diff)),
        z=z,
        note="" if z is not None else "no predictive sd carried; z-score not computed",
    )


def disagreement_statistics(pairs: Sequence[Pair], *, source_url: str = "") -> dict[str, Any]:
    """Counts by band, per variant, plus a mean only when the sample is large enough."""
    comparisons, no_market = [], []
    for pair in pairs:
        try:
            comparisons.append(compare(pair))
        except MissingInput:
            no_market.append(pair)
    bands = {name: 0 for name in BAND_NAMES}
    for c in comparisons:
        bands[c.band] += 1
    by_variant: dict[str, dict[str, int]] = {}
    for c in comparisons:
        slot = by_variant.setdefault(c.variant, {name: 0 for name in BAND_NAMES})
        slot[c.band] += 1
    out: dict[str, Any] = {
        "pairs": len(pairs),
        "compared": len(comparisons),
        "no_market": len(no_market),
        "bands": bands,
        "by_variant": by_variant,
        "band_edges_probability_points": list(BAND_EDGES),
        "source_url": source_url,
    }
    try:
        require_min(comparisons, MIN_PAIRS, needed_for="a mean model-market difference")
    except MissingInput as exc:
        out["mean_absolute_difference"] = NO_INPUT
        out["mean_refusal"] = str(exc)
        return out
    out["mean_absolute_difference"] = round(sum(abs(c.difference) for c in comparisons) / len(comparisons), 4)
    out["mean_signed_difference"] = round(sum(c.difference for c in comparisons) / len(comparisons), 4)
    return out


def bands_from_records(
    records: Iterable[dict[str, Any]], *, source_url: str
) -> list[list[str]]:
    """Render-ready rows: band, count, share, what the band means, official link.

    ``records`` are dicts with ``band``/``count``; the share uses the total of the
    counts, so it is arithmetic on printed values only.
    """
    rows = list(records)
    total = sum(int(r["count"]) for r in rows)
    link = official_link(source_url, where="disagreement band table")
    out = [
        [
            r["band"],
            str(r["count"]),
            f"{(r['count'] / total * 100):.1f}%" if total else NO_INPUT,
            r.get("note", ""),
            link,
        ]
        for r in rows
    ]
    out.append(["TOTAL", str(total), "100.0%" if total else NO_INPUT, "sum of the bands above", link])
    return out
