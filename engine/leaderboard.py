"""Gate-aware leaderboard.

The leaderboard is a *gate*, not a prize for the largest unadjusted backtest.
An entry is ranked only when every required gate has passed on a frozen
strategy version. When no entry passes, the leaderboard is empty - that is the
intended behaviour, not an error.

Scoring weights, minimum sample sizes, stake policy and reward amounts are
policy inputs. They are supplied by the caller and must be fixed before the
holdout is opened; this module never invents them and it refuses to rank
without them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

__all__ = ["GateOutcome", "LeaderboardEntry", "LeaderboardPolicy", "evaluate_gates", "rank"]


@dataclass(frozen=True)
class GateOutcome:
    """The outcome of one promotion gate."""

    gate_id: str
    passed: bool
    status: str
    detail: str = ""
    source_url: str = ""

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "gate_id": self.gate_id,
            "passed": self.passed,
            "status": self.status,
            "detail": self.detail,
            "source_url": self.source_url,
        }


@dataclass(frozen=True)
class LeaderboardEntry:
    """One candidate strategy version and its measured results."""

    strategy_id: str
    model_version: str
    market: str
    sample_size: int
    test_window: str
    brier_score: float
    log_loss: float
    expected_calibration_error: float
    net_units: float
    net_units_per_bet: float
    max_drawdown_units: float
    baseline_comparison: str
    correlation_check: str
    gates: tuple[GateOutcome, ...] = field(default_factory=tuple)

    def eligible(self) -> bool:
        """True only when every declared gate passed."""
        return bool(self.gates) and all(gate.passed for gate in self.gates)

    def failed_gates(self) -> list[str]:
        return [gate.gate_id for gate in self.gates if not gate.passed]


@dataclass(frozen=True)
class LeaderboardPolicy:
    """Declared ranking policy. Every weight must be supplied explicitly.

    ``tie_breaker`` is required as a policy declaration but is not yet applied
    by :func:`rank`; see IR-09 on the Flagged for Review page.
    """

    metric_weights: Mapping[str, float]
    minimum_sample_size: int
    required_gate_ids: tuple[str, ...]
    tie_breaker: str

    def __post_init__(self) -> None:
        if not self.metric_weights:
            raise ValueError("metric_weights must be supplied")
        if self.minimum_sample_size <= 0:
            raise ValueError("minimum_sample_size must be positive")
        if not self.required_gate_ids:
            raise ValueError("required_gate_ids must be supplied")
        if not self.tie_breaker:
            raise ValueError("tie_breaker must be declared")


def evaluate_gates(
    entry: LeaderboardEntry,
    policy: LeaderboardPolicy,
) -> tuple[GateOutcome, ...]:
    """Evaluate the required gates for one entry.

    A gate that the entry does not report is *not* silently treated as passed:
    it is recorded as failed with status ``not reported``.
    """
    outcomes: list[GateOutcome] = []
    reported = {gate.gate_id: gate for gate in entry.gates}
    for gate_id in policy.required_gate_ids:
        gate = reported.get(gate_id)
        if gate is None:
            outcomes.append(
                GateOutcome(
                    gate_id=gate_id,
                    passed=False,
                    status="not reported",
                    detail="the candidate does not report this gate",
                )
            )
        else:
            outcomes.append(gate)
    if entry.sample_size < policy.minimum_sample_size:
        outcomes.append(
            GateOutcome(
                gate_id="G-SAMPLE",
                passed=False,
                status="below minimum sample",
                detail=(
                    f"sample size {entry.sample_size} is below the declared minimum "
                    f"{policy.minimum_sample_size}"
                ),
            )
        )
    return tuple(outcomes)


def _score(entry: LeaderboardEntry, policy: LeaderboardPolicy) -> float:
    """Weighted composite score. Weights are supplied by the policy."""
    values = {
        "brier_score": -entry.brier_score,
        "log_loss": -entry.log_loss,
        "calibration_error": -entry.expected_calibration_error,
        "net_units_per_bet": entry.net_units_per_bet,
        "max_drawdown_units": -entry.max_drawdown_units,
    }
    total_weight = 0.0
    score = 0.0
    for metric, weight in policy.metric_weights.items():
        if metric not in values:
            raise ValueError(f"unknown leaderboard metric: {metric!r}")
        score += weight * values[metric]
        total_weight += weight
    if total_weight == 0:
        raise ValueError("metric weights must not sum to zero")
    return score / total_weight


def rank(
    entries: Sequence[LeaderboardEntry],
    policy: LeaderboardPolicy,
) -> list[dict[str, object]]:
    """Rank eligible entries using the current deterministic fallback.

    Returns an empty list when no entry passes every gate. Rows contain the
    stored score, sample/window and other explicit entry fields; uncertainty
    intervals and preregistration timestamps are not part of the schema. The
    declared ``policy.tie_breaker`` is not applied yet: equal scores sort by
    strategy ID then model version. This is a known mismatch, not an approved
    tie policy (IR-09 on the Flagged for Review page).
    """
    eligible: list[tuple[float, LeaderboardEntry]] = []
    for entry in entries:
        outcomes = evaluate_gates(entry, policy)
        if all(gate.passed for gate in outcomes) and entry.sample_size >= policy.minimum_sample_size:
            eligible.append((_score(entry, policy), entry))
    eligible.sort(key=lambda item: (-item[0], item[1].strategy_id, item[1].model_version))
    rows: list[dict[str, object]] = []
    for position, (score, entry) in enumerate(eligible, start=1):
        rows.append(
            {
                "rank": position,
                "strategy_id": entry.strategy_id,
                "model_version": entry.model_version,
                "market": entry.market,
                "sample_size": entry.sample_size,
                "test_window": entry.test_window,
                "score": score,
                "brier_score": entry.brier_score,
                "log_loss": entry.log_loss,
                "expected_calibration_error": entry.expected_calibration_error,
                "net_units": entry.net_units,
                "net_units_per_bet": entry.net_units_per_bet,
                "max_drawdown_units": entry.max_drawdown_units,
                "baseline_comparison": entry.baseline_comparison,
                "correlation_check": entry.correlation_check,
            }
        )
    return rows
