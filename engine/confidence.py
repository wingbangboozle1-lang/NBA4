"""Disagreement banding, independence proof and the headline/footnote discipline.

Brief items implemented (2026-11-15):

* "Keep two independent estimators and publish their disagreement as the
  primary confidence signal, rather than a single blended rating."
* "Stop publishing a single blended rating as the headline; publish the
  disagreement between the two estimators as the headline and the blend
  underneath."
* "Pin home-court advantage to the measured home-win rate instead of fitting it
  freely."

Division of labour inside the engine, so nothing is implemented twice:

* ``engine/estimators.py`` (added by session ``arena/37a389fa-nba4``, task AN)
  is the **estimator layer**: it computes the two margins and the raw absolute
  disagreement from an authorized ledger, and ``engine/ratings.py`` owns the
  measured-home-win-rate to points mapping.
* this module is the **reporting and policy layer**: it turns a raw gap into a
  banded, auditable headline, proves (or disproves) that the two estimators are
  structurally independent, keeps the blend labelled as a footnote, and audits
  that a home-court value in use is pinned to a measured rate rather than to a
  coefficient somebody typed in.

Why banding rather than a bare number: a gap of 1.4 points means nothing without
a registered band, and an unregistered band must not read as reassurance, so
``UNBANDED`` is a distinct state from ``AGREEMENT``.

Why independence is *checked*: blending or comparing two views that consume the
same input field understates disagreement, and the site would be publishing a
confidence signal that is an artefact of shared inputs. ``independence_audit``
makes the claim mechanical, and ``Disagreement.independent`` is False whenever
any input field is shared.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SURFACE_HEADLINE = "headline"
SURFACE_FOOTNOTE = "footnote"

BAND_AGREEMENT = "AGREEMENT"
BAND_MODEST = "MODEST_GAP"
BAND_MATERIAL = "MATERIAL_GAP"
BAND_SPLIT = "SPLIT"
BAND_UNBANDED = "UNBANDED"
BAND_NOT_COMPARABLE = "NOT_COMPARABLE"


class ConfidenceError(ValueError):
    """Raised when a caller tries to publish a confidence claim it has not earned."""


@dataclass(frozen=True)
class EstimatorOutput:
    """One estimator's view of one game, as it reaches the reporting layer.

    The numbers are expected to come from ``engine/estimators.py``; this record
    exists so the reporting layer can band, label and audit them without
    re-deriving anything, and so a hand-built record in a test is clearly marked
    as ``fitted=False``.
    """

    estimator_id: str
    kind: str                            # "matchup-ppp" | "point-differential" | ...
    game_id: str
    spread_points: Optional[float]       # home minus away; negative = home favoured
    total_points: Optional[float]
    home_win_probability: Optional[float]
    inputs_used: Tuple[str, ...]         # field names, for the independence audit
    version: str
    fitted: bool = False                 # True only after authorized out-of-sample fitting
    source_url: str = ""

    def validate(self) -> "EstimatorOutput":
        if not self.estimator_id:
            raise ConfidenceError("estimator_id required")
        if self.estimator_id == "unknown":
            raise ConfidenceError("an estimator must be identified by id and version for the ledger to bind to")
        if self.home_win_probability is not None and not 0.0 < self.home_win_probability < 1.0:
            raise ConfidenceError(
                f"{self.estimator_id}: home_win_probability must lie strictly between 0 and 1"
            )
        if self.spread_points is None and self.total_points is None and self.home_win_probability is None:
            raise ConfidenceError(
                f"{self.estimator_id}: an estimator that produced nothing must not be published"
            )
        if self.source_url and not self.source_url.startswith("https://"):
            raise ConfidenceError(f"{self.estimator_id}: source_url must be https://")
        return self


@dataclass(frozen=True)
class Disagreement:
    """The headline confidence signal: a banded gap, with its independence proof."""

    game_id: str
    estimator_a: str
    estimator_b: str
    spread_gap_points: Optional[float]
    total_gap_points: Optional[float]
    win_prob_gap: Optional[float]
    log_odds_gap: Optional[float]
    band: str
    independent: bool
    note: str

    @property
    def headline(self) -> str:
        if not self.independent:
            return "DISAGREEMENT NOT PUBLISHABLE (estimators share inputs)"
        return f"{self.band}: {self._fmt()}"

    def _fmt(self) -> str:
        bits: List[str] = []
        if self.spread_gap_points is not None:
            bits.append(f"spread gap {self.spread_gap_points:+.2f} pts")
        if self.total_gap_points is not None:
            bits.append(f"total gap {self.total_gap_points:+.2f} pts")
        if self.win_prob_gap is not None:
            bits.append(f"win-prob gap {self.win_prob_gap:.3f}")
        return "; ".join(bits) if bits else "no comparable output"


def log_odds(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError("p must lie strictly between 0 and 1")
    return math.log(p / (1.0 - p))


def band_gap(magnitude: Optional[float], bands: Optional[Sequence[float]], straddles_zero: bool = False) -> str:
    """Map a gap magnitude onto the registered band policy.

    ``bands`` is the pair ``(small, large)`` in points that the owner registers
    before any season starts. ``None``, a malformed pair, or a non-positive
    threshold all resolve to ``UNBANDED`` rather than to a permissive default.
    """
    if bands is None or len(bands) != 2 or not all(isinstance(x, (int, float)) for x in bands):
        return BAND_UNBANDED
    small, large = float(bands[0]), float(bands[1])
    if small <= 0 or large <= small:
        return BAND_UNBANDED
    if magnitude is None:
        return BAND_NOT_COMPARABLE
    if straddles_zero:
        return BAND_SPLIT
    if magnitude <= small:
        return BAND_AGREEMENT
    if magnitude <= large:
        return BAND_MODEST
    return BAND_MATERIAL


def _gap(x: Optional[float], y: Optional[float]) -> Optional[float]:
    if x is None or y is None:
        return None
    return abs(x - y)


def straddles_zero(a: Optional[float], b: Optional[float]) -> bool:
    """True when one estimator favours each side, i.e. the gap is directional."""
    if a is None or b is None:
        return False
    return a < 0.0 < b or b < 0.0 < a


def disagreement(
    a: EstimatorOutput,
    b: EstimatorOutput,
    bands: Optional[Sequence[float]] = None,
) -> Disagreement:
    """Absolute gap between two structurally different estimators, banded."""
    a.validate()
    b.validate()
    if a.estimator_id == b.estimator_id and a.version == b.version:
        raise ConfidenceError("an estimator cannot be compared with itself")
    if a.game_id != b.game_id:
        raise ConfidenceError("disagreement is defined per game only")
    gap_spread = _gap(a.spread_points, b.spread_points)
    gap_total = _gap(a.total_points, b.total_points)
    gap_prob = _gap(a.home_win_probability, b.home_win_probability)
    gap_log_odds = None
    if a.home_win_probability is not None and b.home_win_probability is not None:
        gap_log_odds = abs(log_odds(a.home_win_probability) - log_odds(b.home_win_probability))
    magnitude = max((v for v in (gap_spread, gap_total) if v is not None), default=None)
    band = band_gap(magnitude, bands, straddles_zero(a.spread_points, b.spread_points))
    shared = set(a.inputs_used) & set(b.inputs_used)
    return Disagreement(
        game_id=a.game_id,
        estimator_a=a.estimator_id,
        estimator_b=b.estimator_id,
        spread_gap_points=gap_spread,
        total_gap_points=gap_total,
        win_prob_gap=gap_prob,
        log_odds_gap=gap_log_odds,
        band=band,
        independent=not shared,
        note=(
            "shared input fields: " + ", ".join(sorted(shared))
            + " - the gap below understates true model uncertainty"
            if shared
            else "no shared input fields; the gap is publishable as the confidence signal"
        ),
    )


@dataclass(frozen=True)
class Blend:
    """The secondary number. ``headline_allowed`` is permanently False."""

    game_id: str
    spread_points: Optional[float]
    total_points: Optional[float]
    home_win_probability: Optional[float]
    weights: Tuple[float, float]
    label: str = "SECONDARY - arithmetic mean of the two estimators; not a rating, not a probability"
    headline_allowed: bool = False


def blend(
    a: EstimatorOutput,
    b: EstimatorOutput,
    weights: Optional[Sequence[float]] = None,
) -> Blend:
    """Blend for the footnote only. Nothing here may promote it to a headline."""
    if weights is None:
        w = (0.5, 0.5)
    else:
        if len(weights) != 2:
            raise ConfidenceError("weights must be a two-element sequence")
        if any(x < 0 for x in weights) or abs(sum(weights) - 1.0) > 1e-9:
            raise ConfidenceError("weights must be non-negative and sum to 1")
        w = (float(weights[0]), float(weights[1]))
    return Blend(
        game_id=a.game_id,
        spread_points=_weighted(a.spread_points, b.spread_points, w),
        total_points=_weighted(a.total_points, b.total_points, w),
        home_win_probability=_weighted(a.home_win_probability, b.home_win_probability, w),
        weights=w,
    )


def _weighted(x: Optional[float], y: Optional[float], w: Tuple[float, float]) -> Optional[float]:
    if x is None or y is None:
        return None
    return w[0] * x + w[1] * y


# --- independence -----------------------------------------------------------

def independence_audit(
    fields_by_estimator: Mapping[str, Iterable[str]],
    disjoint_pairs: Sequence[Tuple[str, str]],
) -> Dict[str, object]:
    """Report which declared estimator pairs actually consume disjoint fields."""
    rows = {name: {f for f in fields if f} for name, fields in fields_by_estimator.items()}
    pairs: List[Dict[str, object]] = []
    all_independent = True
    for left, right in disjoint_pairs:
        shared = rows.get(left, set()) & rows.get(right, set())
        all_independent = all_independent and not shared
        pairs.append(
            {
                "left": left,
                "right": right,
                "independent": not shared,
                "shared_fields": ", ".join(sorted(shared)) or "none",
            }
        )
    return {"pairs": pairs, "all_independent": all_independent}


# --- the estimator layer's record, banded ----------------------------------

def from_comparison(comparison: object) -> Tuple[EstimatorOutput, EstimatorOutput]:
    """Convert an ``engine.estimators.EstimatorComparison`` into two records.

    Only the public attributes of that dataclass are read, so the two modules
    stay independently testable. ``inputs_used`` is left as the estimator
    description because the comparison record does not carry the field list; the
    caller should supply it through ``band_their_comparison(..., inputs_a=...)``
    for the independence claim to mean anything.
    """
    game = f"{getattr(comparison, 'away_team', '?')}@{getattr(comparison, 'home_team', '?')}"
    a = EstimatorOutput(
        estimator_id="estimator-A-matchup-ppp", kind="matchup-ppp", game_id=game,
        spread_points=getattr(comparison, "estimator_a_matchup_ppp", None), total_points=None,
        home_win_probability=None, inputs_used=("possessions", "offensive-ppp", "defensive-ppp"),
        version=getattr(comparison, "version", "unversioned"),
    )
    b = EstimatorOutput(
        estimator_id="estimator-B-point-differential", kind="point-differential", game_id=game,
        spread_points=getattr(comparison, "estimator_b_point_differential", None), total_points=None,
        home_win_probability=None,
        inputs_used=("point-differential-mean", "measured-home-win-rate"),
        version=getattr(comparison, "version", "unversioned"),
    )
    return a, b


def band_their_comparison(comparison: object, bands: Optional[Sequence[float]] = None) -> Dict[str, object]:
    """Band the raw disagreement the estimator layer already computed."""
    raw = getattr(comparison, "disagreement_points", None)
    blended = getattr(comparison, "blended_margin_secondary", None)
    a, b = from_comparison(comparison)
    band = band_gap(raw, bands, straddles_zero(a.spread_points, b.spread_points))
    return {
        "game_id": a.game_id,
        "disagreement_points": raw,
        "band": band,
        "headline_surface": SURFACE_HEADLINE,
        "blend_secondary": blended,
        "footnote_surface": SURFACE_FOOTNOTE,
        "blend_label": "SECONDARY - arithmetic mean; never published as the headline",
        "publishable": raw is not None,
        "note": (
            "the estimator layer blanks its output when inputs are missing, so a blank here is a "
            "data gap, not agreement"
            if raw is None
            else "band is a policy threshold on the gap, not a probability"
        ),
    }


# --- home-court pin audit ---------------------------------------------------

def home_court_pin_audit(
    measured_home_win_rate: Optional[float],
    home_games_used: Optional[int],
    margin_sd: Optional[float],
    value_in_use_points: Optional[float],
    source_url: str,
    sd_is_fitted: bool = False,
) -> Dict[str, object]:
    """Check that a home-court value is pinned to a measurement, not fitted freely.

    The conversion itself lives in ``engine/ratings.home_advantage_from_win_rate``
    (owned by the estimator layer); this function re-derives it and refuses the
    pin when any of these hold:

    * no measured rate, or a rate of exactly 0 or 1 (an unclipped extreme is
      unmeasurable, not an infinite advantage);
    * zero home games behind the rate;
    * no https source for the win totals;
    * the value in use does not match the recomputed pin (a hand-entered
      coefficient would show up here);
    * the margin SD is an unfitted engineering default - reported as a
      limitation, not as a failure, because the repo documents it as UNFITTED.
    """
    from .ratings import home_advantage_from_win_rate  # estimator layer owns the mapping

    problems: List[str] = []
    if measured_home_win_rate is None:
        problems.append("no measured home-win rate: home-court advantage may not be assumed")
    elif not 0.0 < float(measured_home_win_rate) < 1.0:
        problems.append("measured home-win rate is 0 or 1: the point equivalent is infinite, not extreme")
    if not home_games_used or home_games_used <= 0:
        problems.append("no home games counted behind the rate")
    if margin_sd is None or margin_sd <= 0:
        problems.append("margin SD must be declared")
    if not source_url.startswith("https://"):
        problems.append("the win totals need an https official source")
    expected: Optional[float] = None
    if not problems:
        try:
            expected = home_advantage_from_win_rate(float(measured_home_win_rate), float(margin_sd))
        except ValueError as exc:
            problems.append(f"pin cannot be derived: {exc}")
    if expected is not None and value_in_use_points is None:
        problems.append("no home-court value is in use, so there is nothing to pin")
    divergence = None
    if expected is not None and value_in_use_points is not None:
        divergence = abs(float(value_in_use_points) - expected)
        if divergence > 1e-6:
            problems.append(
                f"value in use ({float(value_in_use_points):+.4f}) does not equal the pinned value "
                f"({expected:+.4f}): a free-fitted home-court coefficient is not allowed"
            )
    return {
        "pinned": not problems,
        "expected_points": expected,
        "divergence_points": divergence,
        "codes": tuple(problems) if problems else ("PINNED_TO_MEASURED_RATE",),
        "sd_is_fitted": bool(sd_is_fitted),
        "limitation": (
            "the margin SD is an UNFITTED engineering default in this repository, so the point "
            "equivalent is a deterministic parameterisation, not a measured causal effect"
            if not sd_is_fitted
            else "margin SD declared as fitted; the fit window and its source must be registered "
                 "before this value is published"
        ),
        "mapping_owner": "engine/ratings.py::home_advantage_from_win_rate",
    }


# --- the row the site publishes --------------------------------------------

def summarise_pair(
    a: EstimatorOutput,
    b: EstimatorOutput,
    bands: Optional[Sequence[float]] = None,
    weights: Optional[Sequence[float]] = None,
) -> Dict[str, object]:
    """Headline first, blend underneath - the order is the point."""
    disp = disagreement(a, b, bands)
    mixed = blend(a, b, weights)
    return {
        "game_id": a.game_id,
        "headline_surface": SURFACE_HEADLINE,
        "headline": disp.headline,
        "band": disp.band,
        "independent": disp.independent,
        "spread_gap_points": disp.spread_gap_points,
        "total_gap_points": disp.total_gap_points,
        "win_prob_gap": disp.win_prob_gap,
        "log_odds_gap": disp.log_odds_gap,
        "footnote_surface": SURFACE_FOOTNOTE,
        "blend_spread_points": mixed.spread_points,
        "blend_total_points": mixed.total_points,
        "blend_home_win_probability": mixed.home_win_probability,
        "blend_label": mixed.label,
        "blend_headline_allowed": mixed.headline_allowed,
        "note": disp.note,
    }
