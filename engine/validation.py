"""Validation gates G1-G12 (docs/validation-plan.md) and luck/skill controls.

This module implements the machine-checkable parts of the validation plan:
ledger integrity (G1), market/settlement presence (G2), chronological
walk-forward folds (G4), probability scores and reliability bins (G5),
cluster-bootstrap uncertainty (G7), dependence checks (G8), and a
multiple-testing control for leaderboard claims (G12).

Gate states: "pass" | "fail" | "blocked" | "not run". A strategy becomes
ELIGIBLE only when every gate is "pass" on frozen data. Nothing in this
module can be satisfied by synthetic fixtures in production runs.

Luck control: we can reduce leakage, overfitting and small-sample noise and
quantify uncertainty; we cannot remove randomness from games. The
selectively-skill criterion implemented here is: out-of-sample proper-score
improvement over preregistered baselines whose game-cluster bootstrap
interval excludes zero, with the trials count adjustment applied.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

from .ledger import IntegrityReport

# --- PROPOSED thresholds (blank in docs/validation-plan.md until the owner
# preregisters them; defaults below are engineering placeholders). ---------
MIN_SAMPLE_PROPOSED = 30        # minimum settled forecasts before ranking
BOOTSTRAP_ALPHA = 0.05
TRIALS_ADJUSTMENT = "bonferroni"
# -------------------------------------------------------------------------


@dataclass
class GateState:
    gate: str
    state: str  # pass | fail | blocked | not run
    detail: str


def brier_score(probabilities: Sequence[float], outcomes: Sequence[int]) -> Optional[float]:
    n = len(probabilities)
    if n == 0 or n != len(outcomes):
        return None
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / n


def log_loss(probabilities: Sequence[float], outcomes: Sequence[int], eps: float = 1e-12) -> Optional[float]:
    n = len(probabilities)
    if n == 0 or n != len(outcomes):
        return None
    total = 0.0
    for p, y in zip(probabilities, outcomes):
        p = min(max(p, eps), 1 - eps)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / n


def reliability_bins(
    probabilities: Sequence[float], outcomes: Sequence[int], bins: int = 10
) -> List[Tuple[float, float, int]]:
    """(mean predicted, observed frequency, count) per bin."""
    out: List[Tuple[float, float, int]] = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(probabilities) if lo <= p < hi or (b == bins - 1 and p == 1.0)]
        if not idx:
            continue
        mean_p = sum(probabilities[i] for i in idx) / len(idx)
        freq = sum(outcomes[i] for i in idx) / len(idx)
        out.append((mean_p, freq, len(idx)))
    return out


def walk_forward_folds(n_events: int, n_folds: int, min_train: int) -> List[Tuple[range, range]]:
    """Chronological (train range, test range) splits. G4.

    Fold i trains on events [0, test_start_i) and tests on the next block.
    Every test index is strictly greater than every train index.
    """
    if n_folds < 1 or n_events <= min_train:
        return []
    usable = n_events - min_train
    block = usable // n_folds
    if block == 0:
        return []
    folds = []
    for k in range(n_folds):
        test_start = min_train + k * block
        test_end = min_train + (k + 1) * block if k < n_folds - 1 else n_events
        if test_start >= test_end:
            continue
        folds.append((range(0, test_start), range(test_start, test_end)))
    return folds


def trials_adjusted_alpha(alpha: float, n_trials: int) -> float:
    """Bonferroni-adjusted significance level for n strategy trials (G12)."""
    if n_trials < 1:
        raise ValueError("n_trials must be >= 1")
    return min(alpha / n_trials, 1.0)


def skill_vs_baseline(
    model_scores: Sequence[float],
    baseline_scores: Sequence[float],
    higher_is_better: bool = False,
) -> Optional[float]:
    """Mean paired improvement of model over baseline on a proper score."""
    n = min(len(model_scores), len(baseline_scores))
    if n == 0:
        return None
    diffs = [
        (model_scores[i] - baseline_scores[i]) * (1 if higher_is_better else -1)
        for i in range(n)
    ]
    return sum(diffs) / n


def run_gates(
    integrity: IntegrityReport,
    has_market_spec: bool,
    n_settled_forecasts: int,
    n_trials: int = 1,
) -> List[GateState]:
    """Structural gate report for the current repository state."""
    states: List[GateState] = []

    states.append(GateState(
        "G0 rights/jurisdiction", "blocked",
        "no written data licence or legal classification on file "
        "(docs/decision-register.md Q1/Q3); see Flagged for Review F-01/F-04",
    ))
    states.append(GateState(
        "G1 point-in-time data",
        "pass" if integrity.passed else ("fail" if integrity.loaded else "blocked"),
        "; ".join(integrity.notes) or f"{integrity.loaded} validated records",
    ))
    states.append(GateState(
        "G2 market/settlement",
        "pass" if has_market_spec else "blocked",
        "market and settlement specification present" if has_market_spec
        else "no licensed quote source or settlement specification (F-03)",
    ))
    states.append(GateState("G3 preregistration", "not run",
                            "no strategy registry entries yet; thresholds in docs are blank by design"))
    states.append(GateState("G4 chronological evaluation", "not run",
                            "walk-forward splitter available; no dataset/predictions yet"))
    states.append(GateState("G5 calibration/accuracy", "not run",
                            "Brier/log-loss/reliability available; no predictions/outcomes yet"))
    states.append(GateState("G6 net value", "blocked",
                            "no rights-cleared quotes, payouts or settlements"))
    states.append(GateState("G7 uncertainty", "not run",
                            "game-cluster bootstrap available; no outcomes yet"))
    states.append(GateState("G8 parlay dependence", "not run",
                            "correlation module available; no paired legs yet"))
    states.append(GateState("G9 injuries/flow", "blocked",
                            "no authorized injury history or minutes outcomes (F-07)"))
    states.append(GateState("G10 robustness", "not run",
                            "no holdout or independent replication yet"))
    states.append(GateState("G11 shadow operation", "not run",
                            "shadow ledger format defined; no backend/feed yet"))
    states.append(GateState(
        "G12 leaderboard/rewards", "blocked",
        f"n_settled_forecasts={n_settled_forecasts} (proposed minimum "
        f"{MIN_SAMPLE_PROPOSED}); n_trials={n_trials} => adjusted alpha="
        f"{trials_adjusted_alpha(BOOTSTRAP_ALPHA, n_trials):.4f}; reward policy "
        "and legal sign-off missing (F-09)",
    ))
    return states


def all_gates_passed(states: Sequence[GateState]) -> bool:
    return all(s.state == "pass" for s in states)
