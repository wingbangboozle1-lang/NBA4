"""Validation metrics and leakage controls.

The functions here implement the metrics named in ``docs/validation-plan.md``:

* proper scoring rules for probability forecasts (Brier score, log loss),
* reliability bins and interval coverage,
* chronological walk-forward splits,
* net return computed from an explicit settlement rule,
* a mechanical leakage check (a forecast may not use a record that was
  observed at or after the forecast timestamp).

None of these functions proves that a strategy has skill. They measure
predictive quality against declared baselines and quantify uncertainty; the
decision rules live in ``engine.leaderboard`` and in the validation plan.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Sequence

from .contracts import Forecast, GameEvent

__all__ = [
    "brier_score",
    "log_loss",
    "reliability_table",
    "expected_calibration_error",
    "coverage",
    "walk_forward_splits",
    "net_return",
    "leakage_violations",
    "ValidationSummary",
]


@dataclass(frozen=True)
class ValidationSummary:
    """A bundle of validation outputs for one strategy version."""

    strategy_id: str
    model_version: str
    sample_size: int
    brier_score: float
    log_loss: float
    expected_calibration_error: float
    net_units: float
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "strategy_id": self.strategy_id,
            "model_version": self.model_version,
            "sample_size": self.sample_size,
            "brier_score": self.brier_score,
            "log_loss": self.log_loss,
            "expected_calibration_error": self.expected_calibration_error,
            "net_units": self.net_units,
            "notes": self.notes,
        }


def brier_score(probabilities: Sequence[float], outcomes: Sequence[bool]) -> float:
    """Mean squared error of probabilistic forecasts (lower is better).

    A lower Brier score alone does **not** prove calibration: scikit-learn's
    calibration guide notes that the score mixes calibration, resolution and
    the randomness of the data. Use it together with the reliability table.
    """
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length")
    if not probabilities:
        raise ValueError("no observations")
    total = 0.0
    for p, y in zip(probabilities, outcomes):
        target = 1.0 if y else 0.0
        total += (p - target) ** 2
    return total / len(probabilities)


def log_loss(probabilities: Sequence[float], outcomes: Sequence[bool], eps: float = 1e-15) -> float:
    """Mean negative log likelihood of probabilistic forecasts."""
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length")
    if not probabilities:
        raise ValueError("no observations")
    total = 0.0
    for p, y in zip(probabilities, outcomes):
        target = 1.0 if y else 0.0
        q = min(max(p, eps), 1 - eps)
        total += -(target * math.log(q) + (1 - target) * math.log(1 - q))
    return total / len(probabilities)


def reliability_table(
    probabilities: Sequence[float],
    outcomes: Sequence[bool],
    bins: int = 10,
) -> list[dict[str, float | int]]:
    """Reliability diagram data: per-bin mean forecast and observed frequency."""
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length")
    if bins <= 0:
        raise ValueError("bins must be positive")
    buckets: list[list[tuple[float, bool]]] = [[] for _ in range(bins)]
    for p, y in zip(probabilities, outcomes):
        index = min(bins - 1, max(0, int(p * bins)))
        buckets[index].append((p, y))
    table: list[dict[str, float | int]] = []
    for index, bucket in enumerate(buckets):
        if not bucket:
            continue
        table.append(
            {
                "bin_lower": index / bins,
                "bin_upper": (index + 1) / bins,
                "count": len(bucket),
                "mean_forecast": sum(p for p, _ in bucket) / len(bucket),
                "observed_frequency": sum(1 for _, y in bucket if y) / len(bucket),
            }
        )
    return table


def expected_calibration_error(
    probabilities: Sequence[float],
    outcomes: Sequence[bool],
    bins: int = 10,
) -> float:
    """Weighted mean gap between forecast and observed frequency across bins."""
    table = reliability_table(probabilities, outcomes, bins=bins)
    if not table:
        return float("nan")
    total = sum(row["count"] for row in table)
    if total == 0:
        return float("nan")
    return sum(
        row["count"] * abs(row["mean_forecast"] - row["observed_frequency"]) for row in table
    ) / total


def coverage(
    forecasts: Sequence[float],
    intervals: Sequence[tuple[float, float]],
    observed: Sequence[float],
) -> float:
    """Share of observations that fall inside their predicted interval."""
    if not (len(forecasts) == len(intervals) == len(observed)):
        raise ValueError("forecasts, intervals and observed must have the same length")
    if not forecasts:
        raise ValueError("no observations")
    hits = 0
    for (low, high), value in zip(intervals, observed):
        if low <= value <= high:
            hits += 1
    return hits / len(forecasts)


def walk_forward_splits(
    events: Sequence[GameEvent],
    train_days: int,
    test_days: int,
    embargo_days: int = 0,
) -> list[tuple[list[GameEvent], list[GameEvent]]]:
    """Chronological train/test splits over time.

    Each split trains on everything strictly before the test window and tests on
    the next window. ``embargo_days`` can be used to leave a gap between train
    and test so that features which need time to mature cannot leak across the
    boundary.

    The returned order is chronological, which is the property the validation
    plan requires: a model is never evaluated on the past after being trained
    on the future.
    """
    if train_days <= 0 or test_days <= 0:
        raise ValueError("train_days and test_days must be positive")
    ordered = sorted(events, key=lambda e: e.tipoff_utc)
    if not ordered:
        return []
    start = ordered[0].tipoff_utc.astimezone(timezone.utc)
    end = ordered[-1].tipoff_utc.astimezone(timezone.utc)
    splits: list[tuple[list[GameEvent], list[GameEvent]]] = []
    cursor = start
    while True:
        train_end = cursor + timedelta(days=train_days)
        test_end = train_end + timedelta(days=embargo_days) + timedelta(days=test_days)
        if test_end > end:
            break
        train = [
            e
            for e in ordered
            if e.tipoff_utc < train_end - timedelta(days=embargo_days)
        ]
        test = [e for e in ordered if train_end <= e.tipoff_utc < test_end]
        if train and test:
            splits.append((train, test))
        cursor = cursor + timedelta(days=test_days)
    return splits


def net_return(
    picks: Iterable[dict[str, float]],
    stake: float = 1.0,
) -> float:
    """Net units returned from settled picks.

    Each pick dict must contain ``won`` (1.0/0.0) and ``net_return`` (the
    profit per unit staked after the market's payout and fee rules, which the
    caller must apply when it builds the record). Pushes are represented as a
    ``net_return`` of 0.0 and are not counted as wins.
    """
    total = 0.0
    count = 0
    for pick in picks:
        if "net_return" not in pick:
            raise ValueError("each pick needs a net_return value")
        total += float(pick["net_return"])
        count += 1
    if count == 0:
        return 0.0
    return total * stake


def leakage_violations(
    forecast: Forecast,
    input_records: Sequence[object],
) -> list[str]:
    """Return descriptions of any input that post-dates the forecast."""
    violations: list[str] = []
    emitted = forecast.emitted_at.astimezone(timezone.utc)
    for record in input_records:
        provenance = getattr(record, "provenance", None)
        if provenance is None:
            violations.append(f"record {record!r} has no provenance")
            continue
        observed = provenance.observed_at.astimezone(timezone.utc)
        if observed >= emitted:
            violations.append(
                f"{getattr(record, 'event_id', 'record')} observed at "
                f"{observed.isoformat()} is not before forecast at {emitted.isoformat()}"
            )
    return violations


def summarise(
    strategy_id: str,
    model_version: str,
    probabilities: Sequence[float],
    outcomes: Sequence[bool],
    settled: Iterable[dict[str, float]] = (),
    bins: int = 10,
    notes: str = "",
) -> ValidationSummary:
    """Bundle the standard metrics for one strategy version."""
    return ValidationSummary(
        strategy_id=strategy_id,
        model_version=model_version,
        sample_size=len(probabilities),
        brier_score=brier_score(probabilities, outcomes),
        log_loss=log_loss(probabilities, outcomes),
        expected_calibration_error=expected_calibration_error(probabilities, outcomes, bins=bins),
        net_units=net_return(settled),
        notes=notes,
    )
