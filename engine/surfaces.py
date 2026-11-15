"""Surface separation: what may be published now, and what stays gated.

Brief item implemented (2026-11-15): "Split the site into 'projection' (safe to
publish now) and 'bet' (gated) surfaces, and never mix them."

The split is enforced at the *field* level, not the page level, because pages
change and fields do not. Each published field is declared in exactly one
surface:

* ``projection`` - a model or observational quantity that can be published today
  because it is either a documented method, an official observation, or a
  derived count over official schedule rows. No price, no stake, no edge.
* ``bet`` - anything a reader could act on as a wager: an edge against a market
  price, a price or payout, a pick/selection with a stake, a parlay quote, a
  settlement of a wager, a leaderboard reward. Publishing these requires the
  rights gate (G0) and the pre-registration + validation gates to have passed on
  authorized data, which is not the state of this repository.

Rules implemented here:

1. ``classify(field)`` returns the declared surface; an undeclared field is an
   error, so new fields cannot sneak in without a decision.
2. ``project_view`` keeps only projection fields. ``bet_view`` returns *nothing
   but gate status* unless ``bet_gate_open`` is True; when a bet-gated field is
   requested while the gate is closed, the value is replaced by a stub carrying
   the blocking reason codes - it is never rendered as a number.
3. ``assert_not_mixed`` refuses a rendered row that carries a bet-surface value
   inside a projection-surface payload (and vice versa). ``scripts/check_site.py``
   calls ``audit_page_surface`` with it, so the site fails its own build check if
   a page mixes the two.

The point of the strict version is that "safe to publish now" and "gated" have
different legal footings (see ``docs/sources.md`` on NBA Terms and the Ksa
guidance), so mixing them would let a reader treat an unpublished-risk number as
a published fact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

PROJECTION = "projection"
BET = "bet"
SURFACES = (PROJECTION, BET)

# Declared surface of every field the site or the engine may publish.
FIELD_SURFACES: Dict[str, str] = {
    # --- projection: safe to publish now -----------------------------------
    "schedule_row": PROJECTION,
    "tip_time": PROJECTION,
    "matchup": PROJECTION,
    "game_date": PROJECTION,
    "days_rest": PROJECTION,
    "back_to_back": PROJECTION,
    "three_in_four": PROJECTION,
    "games_in_last_4": PROJECTION,
    "rest_advantage": PROJECTION,
    "travel_leg_miles": PROJECTION,
    "injury_report_revision_time": PROJECTION,
    "injury_report_retrieval_time": PROJECTION,
    "injury_status_as_printed": PROJECTION,
    "injury_reason_as_printed": PROJECTION,
    "injury_status_change": PROJECTION,
    "rotation_availability": PROJECTION,
    "top8_minutes_share": PROJECTION,
    "minutes_redistribution_scenario": PROJECTION,
    "estimator_disagreement": PROJECTION,
    "estimator_disagreement_band": PROJECTION,
    "blended_rating_footnote": PROJECTION,
    "home_court_advantage_basis": PROJECTION,
    "luck_zscore": PROJECTION,
    "luck_noise_band": PROJECTION,
    "model_line_unpriced": PROJECTION,
    "model_total_possessions_x_ppp": PROJECTION,
    "naive_total_baseline": PROJECTION,
    "preregistration_status": PROJECTION,
    "preregistration_hash": PROJECTION,
    "ledger_seal_root": PROJECTION,
    "ledger_settlement_stamp": PROJECTION,
    "gate_status": PROJECTION,
    "source_link": PROJECTION,
    "verification_flag": PROJECTION,
    # --- bet: gated ---------------------------------------------------------
    "benchmark_price": BET,
    "market_line": BET,
    "edge_vs_market": BET,
    "fair_price": BET,
    "payout": BET,
    "stake": BET,
    "parlay_quote": BET,
    "pick_selection": BET,
    "recommended_bet": BET,
    "roi": BET,
    "yield_percent": BET,
    "wager_size": BET,
    "settled_wager": BET,
    "leaderboard_reward": BET,
    "closing_line": BET,
    "anchored_line": BET,
    "clv": BET,
}

BET_GATE_NAME = "G0_RIGHTS_AND_VALIDATION"


class SurfaceError(ValueError):
    """Raised on an undeclared field or a mixed-surface render."""


def classify(name: str) -> str:
    key = name.strip()
    if key not in FIELD_SURFACES:
        raise SurfaceError(
            f"field {name!r} has no declared surface; add it to FIELD_SURFACES with an "
            "explicit PROJECTION or BET classification (and register the decision)"
        )
    return FIELD_SURFACES[key]


def fields_of(surface: str) -> Tuple[str, ...]:
    if surface not in SURFACES:
        raise SurfaceError(f"unknown surface {surface!r}")
    return tuple(sorted(k for k, v in FIELD_SURFACES.items() if v == surface))


@dataclass(frozen=True)
class BetGate:
    """The gate state that decides whether any bet-surface value may render."""

    cleared: bool
    reason_codes: Tuple[str, ...]
    checked_at: str
    evidence: Tuple[str, ...] = ()

    @staticmethod
    def blocked(reason_codes: Sequence[str], checked_at: str) -> "BetGate":
        return BetGate(False, tuple(reason_codes), checked_at)


def project_view(record: Mapping[str, object]) -> Dict[str, object]:
    """Only projection-surface fields pass through; anything else is dropped loudly."""
    out: Dict[str, object] = {}
    dropped: Dict[str, str] = {}
    for key, value in record.items():
        surface = classify(key)
        if surface == PROJECTION:
            out[key] = value
        else:
            dropped[key] = f"{surface}: withheld by the surface split"
    if dropped:
        out["_withheld"] = dropped
    return out


def bet_view(record: Mapping[str, object], gate: BetGate) -> Dict[str, object]:
    """Bet-surface fields render only when the gate is cleared; else stubs."""
    out: Dict[str, object] = {"_gate": {"cleared": gate.cleared, "reasons": list(gate.reason_codes),
                                         "checked_at": gate.checked_at}}
    for key, value in record.items():
        surface = classify(key)
        if surface != BET:
            continue
        if gate.cleared:
            out[key] = value
        else:
            out[key] = {
                "value": None,
                "status": "GATED",
                "gate": BET_GATE_NAME,
                "reason_codes": list(gate.reason_codes),
                "note": "the projection surface carries the underlying estimate; this field is "
                        "a wager-facing quantity and is not published while the gate is closed",
            }
    return out


def assert_not_mixed(payload: Mapping[str, object], surface: str, where: str = "") -> None:
    """Refuse a payload that carries a value from the other surface.

    A ``None``/empty/gated-stub value from the other surface is allowed, because
    the whole point of the split is that the *absence* is legible: a reader sees a
    gate notice, not a number.
    """
    if surface not in SURFACES:
        raise SurfaceError(f"unknown surface {surface!r}")
    for key, value in payload.items():
        if key.startswith("_"):
            continue
        declared = classify(key)
        if declared == surface:
            continue
        if _is_empty_or_stub(value):
            continue
        raise SurfaceError(
            f"{where or 'payload'}: field {key!r} belongs to the {declared} surface and carries a "
            f"value inside a {surface} render; the surfaces must never mix"
        )


def _is_empty_or_stub(value: object) -> bool:
    if value is None or value == "" or value == [] or value == {}:
        return True
    if isinstance(value, Mapping):
        if value.get("status") == "GATED":
            return True
        if value.get("value") is None and "status" in value:
            return True
    return False


def audit_page_surface(html: str, blocked_fields: Sequence[str]) -> List[str]:
    """Site-level guard used by ``scripts/check_site.py``.

    ``blocked_fields`` are substrings that identify a bet-gated column header on a
    projection page. If such a header is present and any row under it carries a
    numeric value, the audit fails - the pattern that would let a gated number
    slip onto the publish-safe side of the site.
    """
    problems: List[str] = []
    if not blocked_fields:
        return problems
    import re

    for header in blocked_fields:
        if header.lower() not in html.lower():
            continue
        for match in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", html, re.S | re.I):
            row = match.group(1)
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S | re.I)
            for cell in cells:
                text = re.sub(r"<[^>]+>", "", cell).strip()
                if not text:
                    continue
                if _NUMERIC_ONLY.match(text) and "GATED" not in text.upper():
                    problems.append(
                        f"{header}: a numeric value ({text[:32]!r}) sits under a bet-gated heading on "
                        "a projection page; move it behind the gate or blank it"
                    )
    return problems


_NUMERIC_ONLY = re.compile(r"^[+-]?\d+(?:[.,]\d+)?%?$")


def surface_summary() -> Dict[str, object]:
    """Counts for the overview page: how many fields sit on each surface."""
    projection = [k for k, v in FIELD_SURFACES.items() if v == PROJECTION]
    bet = [k for k, v in FIELD_SURFACES.items() if v == BET]
    return {
        "projection_fields": len(projection),
        "bet_fields": len(bet),
        "bet_fields_blocked": len(bet),
        "rule": "a field is declared on exactly one surface; an undeclared field fails the build",
    }
