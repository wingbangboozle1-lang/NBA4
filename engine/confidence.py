"""Two independent estimators, disagreement as the headline, blend as footnote.

Brief items implemented (2026-11-15):

* "Keep two independent estimators and publish their disagreement as the
  primary confidence signal, rather than a single blended rating."
* "Stop publishing a single blended rating as the headline; publish the
  disagreement between the two estimators as the headline and the blend
  underneath."
* "Pin home-court advantage to the measured home-win rate instead of fitting it
  freely."

Why disagreement rather than a blend: blending two correlated views of the same
data hides the fact that they agree only because they use the same inputs, and
a single number publishes no information about model uncertainty. The
difference between two structurally different estimators *is* an uncertainty
signal, and it is the one the site puts in the headline. The blend is still
computed - it is useful as a secondary estimate - but it is labelled secondary
and the module refuses to let it be labelled a headline.

Independence is a *claim about inputs*, so ``independence_audit`` checks it
mechanically: two estimators that consume any shared input field are not
independent, and their disagreement is reported as ``NOT_INDEPENDENT`` and is
never published as a confidence signal.

Home-court advantage is derived, not fitted: ``home_court_points`` converts a
measured home-win rate into a points value through the normal quantile at the
home margin's standard deviation. The caller must supply both; there is no
default HCA constant anywhere in this repository, because an assumed constant is
exactly the free parameter the brief wants pinned.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional, Sequence, Set, Tuple

from .distributions import normal_quantile

SURFACE_HEADLINE = "headline"
SURFACE_FOOTNOTE = "footnote"


class EstimatorError(ValueError):
    """Raised when an estimator is fed inputs it is not allowed to consume."""


@dataclass(frozen=True)
class EstimatorOutput:
    """One estimator's view of one game. No blending happens inside it."""

    estimator_id: str
    kind: str                      # "ratings" | "possession-efficiency" | ...
    game_id: str
    spread_points: Optional[float]   # home minus away, negative = home favoured
    total_points: Optional[float]
    home_win_probability: Optional[float]
    inputs_used: Tuple[str, ...]     # field names, for the independence audit
    version: str
    fitted: bool = False             # True only after authorised out-of-sample fitting

    def validate(self) -> "EstimatorOutput":
        if not self.estimator_id:
            raise EstimatorError("estimator_id required")
        if self.home_win_probability is not None and not 0.0 < self.home_win_probability < 1.0:
            raise EstimatorError(
                f"{self.estimator_id}: home_win_probability must lie strictly between 0 and 1"
            )
        if self.spread_points is None and self.total_points is None and self.home_win_probability is None:
            raise EstimatorError(
                f"{self.estimator_id}: an estimator that produced nothing must not be published"
            )
        return self


@dataclass(frozen=True)
class Disagreement:
    """The headline confidence signal."""

    game_id: str
    estimator_a: str
    estimator_b: str
    spread_gap_points: Optional[float]
    total_gap_points: Optional[float]
    win_prob_gap: Optional[float]
    log_odds_gap: Optional[float]
    band: str                        # AGREEMENT | MODEST_GAP | MATERIAL_GAP | SPLIT | UNBANDED
    independent: bool
    note: str

    @property
    def headline(self) -> str:
        if not self.independent:
            return "DISAGREEMENT NOT PUBLISHABLE (estimators share inputs)"
        return f"{self.band}: {self._fmt()}"

    def _fmt(self) -> str:
        bits = []
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


def disagreement(
    a: EstimatorOutput,
    b: EstimatorOutput,
    bands: Sequence[float],
) -> Disagreement:
    """Absolute gap between the two estimators, banded by a declared policy.

    ``bands`` is the pair of point thresholds ``(small, large)`` the owner
    registers; nothing is assumed. A band of ``None`` means "not registered",
    and the result is reported as ``UNBANDED`` so it cannot be read as
    reassurance.
    """
    a.validate()
    b.validate()
    if a.estimator_id == b.estimator_id:
        raise EstimatorError("an estimator cannot be compared with itself")
    if a.game_id != b.game_id:
        raise EstimatorError("disagreement is defined per game only")
    gap_spread = _gap(a.spread_points, b.spread_points)
    gap_total = _gap(a.total_points, b.total_points)
    gap_prob = _gap(a.home_win_probability, b.home_win_probability)
    gap_logodds = None
    if a.home_win_probability is not None and b.home_win_probability is not None:
        gap_logodds = abs(log_odds(a.home_win_probability) - log_odds(b.home_win_probability))
    band = "UNBANDED"
    if bands is not None and len(bands) == 2 and all(isinstance(x, (int, float)) for x in bands):
        small, large = bands
        magnitude = max(
            (v for v in (gap_spread, gap_total) if v is not None),
            default=None,
        )
        # SPLIT is a statement about direction, not size: one estimator favours
        # the home team and the other favours the visitor. A small gap that
        # straddles zero is a split, and a large gap of one sign is not.
        straddles_zero = (
            a.spread_points is not None
            and b.spread_points is not None
            and (a.spread_points < 0.0 < b.spread_points or b.spread_points < 0.0 < a.spread_points)
        )
        if magnitude is None:
            band = "NOT_COMPARABLE"
        elif straddles_zero:
            band = "SPLIT"
        elif magnitude <= small:
            band = "AGREEMENT"
        elif magnitude <= large:
            band = "MODEST_GAP"
        else:
            band = "MATERIAL_GAP"
    shared = set(a.inputs_used) & set(b.inputs_used)
    return Disagreement(
        game_id=a.game_id,
        estimator_a=a.estimator_id,
        estimator_b=b.estimator_id,
        spread_gap_points=gap_spread,
        total_gap_points=gap_total,
        win_prob_gap=gap_prob,
        log_odds_gap=gap_logodds,
        band=band,
        independent=not shared,
        note=(
            "shared input fields: " + ", ".join(sorted(shared))
            if shared
            else "no shared input fields; disagreement is publishable as the confidence signal"
        ),
    )


def _gap(x: Optional[float], y: Optional[float]) -> Optional[float]:
    if x is None or y is None:
        return None
    return abs(x - y)


@dataclass(frozen=True)
class Blend:
    """The secondary number, explicitly not a headline."""

    game_id: str
    spread_points: Optional[float]
    total_points: Optional[float]
    home_win_probability: Optional[float]
    weights: Tuple[float, float]
    label: str = "SECONDARY - equal-weight blend of the two estimators; not a rating"
    headline_allowed: bool = False


def blend(
    a: EstimatorOutput,
    b: EstimatorOutput,
    weights: Optional[Sequence[float]] = None,
) -> Blend:
    """Blend for the footnote. ``headline_allowed`` is permanently False here."""
    if weights is None:
        w = (0.5, 0.5)
    else:
        if len(weights) != 2:
            raise EstimatorError("weights must be a two-element sequence")
        if any(w < 0 for w in weights) or abs(sum(weights) - 1.0) > 1e-9:
            raise EstimatorError("weights must be non-negative and sum to 1")
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
    out: Dict[str, object] = {"pairs": [], "all_independent": True}
    pairs: List[Dict[str, object]] = []
    for left, right in disjoint_pairs:
        shared = rows.get(left, set()) & rows.get(right, set())
        pairs.append(
            {
                "left": left,
                "right": right,
                "independent": not shared,
                "shared_fields": ", ".join(sorted(shared)) or "none",
            }
        )
        if shared:
            out["all_independent"] = False
    out["pairs"] = pairs
    return out


# --- home-court advantage ---------------------------------------------------

@dataclass(frozen=True)
class HomeCourtAdvantage:
    """HCA derived from a measured home-win rate, never fitted to the slate."""

    home_win_rate: float
    home_margin_sd: float
    points_per_100_possessions: Optional[float]
    value_points: float
    basis: str
    source_url: str

    @property
    def label(self) -> str:
        return (
            f"pinned to the measured home-win rate {self.home_win_rate:.4f} "
            f"(z={_z(self.home_win_rate):.3f}) scaled by the home-margin SD "
            f"{self.home_margin_sd:.2f}"
        )


def _z(rate: float) -> float:
    return normal_quantile(rate)


def home_court_points(
    home_win_rate: Optional[float],
    home_margin_sd: Optional[float],
    source_url: str,
    season: str,
    league_average_total: Optional[float] = None,
) -> HomeCourtAdvantage:
    """Convert a measured home-win rate into a points value.

    ``value = Phi^-1(home_win_rate) * home_margin_sd``. Refusing to run without
    a measured rate (rather than assuming the customary 2.5-3.5 point range) is
    the point of this function: a free parameter must stay free of assumptions.
    """
    if home_win_rate is None or not 0.0 < home_win_rate < 1.0:
        raise EstimatorError(
            "home-win rate is required and must lie strictly between 0 and 1; "
            "home-court advantage is pinned to a measured rate, never assumed"
        )
    if home_margin_sd is None or home_margin_sd <= 0:
        raise EstimatorError("home-margin standard deviation is required and must be positive")
    if not source_url.startswith("https://"):
        raise EstimatorError("the measured rate needs an https official source URL")
    if league_average_total is not None:
        if league_average_total <= 0:
            raise EstimatorError("league_average_total must be positive when supplied")
    value = normal_quantile(home_win_rate) * float(home_margin_sd)
    return HomeCourtAdvantage(
        home_win_rate=float(home_win_rate),
        home_margin_sd=float(home_margin_sd),
        points_per_100_possessions=league_average_total,
        value_points=value,
        basis=f"measured home-win rate over {season}; normal-quantile scaling",
        source_url=source_url,
    )


def summarise_pair(
    a: EstimatorOutput,
    b: EstimatorOutput,
    bands: Sequence[float],
    weights: Optional[Sequence[float]] = None,
) -> Dict[str, object]:
    """The row the model page publishes: headline gap, footnote blend."""
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
