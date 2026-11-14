"""The daily slate pipeline: horizon, freshness, gates, ledger.

The pipeline is designed so that a run needs **no manual input**:

1. Read the authorised inputs (schedule, injuries, results, quotes) that the
   adapters placed in the run directory.
2. Select the slate: every event whose tip-off lies inside the declared
   horizon (default 72 hours) in the declared timezone.
3. Check freshness: any input older than the declared tolerance is stale, and
   a stale input suppresses the affected output instead of being silently used.
4. Run each enabled strategy to produce immutable forecasts.
5. Convert forecasts into pick/no-bet decisions. A pick is emitted only when
   every gate passed, the market is specified and a licensed benchmark quote
   exists; otherwise a ``no_bet`` pick with reason codes is written.
6. Append the run to an append-only ledger (JSON Lines) and write a run report.

The pipeline never contacts the network and never writes to the published
site. Publishing is a separate, explicit step.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Sequence

from .contracts import (
    Forecast,
    GameEvent,
    InjuryRecord,
    MarketQuote,
    Pick,
    RightsError,
    canonical_json,
    require_allowed_use,
    snapshot_hash,
)

__all__ = [
    "HORIZON_HOURS",
    "RunConfig",
    "RunReport",
    "select_slate",
    "stale_records",
    "run_pipeline",
    "write_ledger",
    "append_ledger",
]

HORIZON_HOURS = 72
"""Maximum forecast horizon in hours (the requested three-day maximum)."""

REASON_CODES = {
    "RIGHTS_NOT_CLEARED": "an input record is not cleared for the intended use",
    "STALE_DATA": "an input is older than the declared freshness tolerance",
    "GATE_FAILED": "a promotion gate did not pass",
    "NO_MARKET_SPEC": "the market/settlement rule is not specified",
    "NO_BENCHMARK_QUOTE": "no licensed benchmark quote is available",
    "UNRESOLVED_INJURY": "the availability of a relevant player is unresolved",
    "BELOW_MINIMUM_SAMPLE": "the strategy has not accumulated the declared sample",
}


@dataclass(frozen=True)
class RunConfig:
    """Declared configuration for one pipeline run."""

    run_id: str
    now_utc: datetime
    horizon_hours: int = HORIZON_HOURS
    timezone_name: str = "UTC"
    max_input_age_minutes: int = 90
    model_version: str = ""
    market_specified: bool = False
    minimum_sample_size: int = 0

    def __post_init__(self) -> None:
        if self.horizon_hours <= 0 or self.horizon_hours > HORIZON_HOURS:
            raise ValueError(
                f"horizon must be within 1..{HORIZON_HOURS} hours (the requested maximum is three days)"
            )
        if self.max_input_age_minutes <= 0:
            raise ValueError("max_input_age_minutes must be positive")
        if not self.run_id:
            raise ValueError("run_id is required")
        if self.now_utc.tzinfo is None:
            raise ValueError("now_utc must be timezone aware")


@dataclass
class RunReport:
    """Everything a reviewer needs to audit one pipeline run."""

    run_id: str
    started_at: datetime
    finished_at: datetime
    horizon_start: datetime
    horizon_end: datetime
    timezone_name: str
    slate_event_ids: list[str] = field(default_factory=list)
    stale_inputs: list[str] = field(default_factory=list)
    suppressed: list[dict[str, object]] = field(default_factory=list)
    forecasts: list[dict[str, object]] = field(default_factory=list)
    picks: list[dict[str, object]] = field(default_factory=list)
    input_snapshot_hash: str = ""
    rights_cleared: bool = False
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "horizon_start": self.horizon_start.isoformat(),
            "horizon_end": self.horizon_end.isoformat(),
            "timezone_name": self.timezone_name,
            "slate_event_ids": self.slate_event_ids,
            "stale_inputs": self.stale_inputs,
            "suppressed": self.suppressed,
            "forecasts": self.forecasts,
            "picks": self.picks,
            "input_snapshot_hash": self.input_snapshot_hash,
            "rights_cleared": self.rights_cleared,
            "notes": self.notes,
        }


def select_slate(
    events: Sequence[GameEvent],
    now_utc: datetime,
    horizon_hours: int = HORIZON_HOURS,
) -> list[GameEvent]:
    """Events whose tip-off falls inside [now, now + horizon].

    The horizon is a hard filter: a game beyond it is never forecast, and a
    game already started is never forecast again.
    """
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone aware")
    end = now_utc + timedelta(hours=horizon_hours)
    return [
        event
        for event in sorted(events, key=lambda e: e.tipoff_utc)
        if now_utc <= event.tipoff_utc.astimezone(timezone.utc) <= end
    ]


def stale_records(
    records: Iterable[object],
    now_utc: datetime,
    max_age_minutes: int,
) -> list[str]:
    """Descriptions of records that are older than the freshness tolerance."""
    stale: list[str] = []
    for record in records:
        provenance = getattr(record, "provenance", None)
        if provenance is None:
            stale.append(f"{record!r}: missing provenance")
            continue
        age = now_utc - provenance.observed_at.astimezone(timezone.utc)
        if age > timedelta(minutes=max_age_minutes):
            stale.append(
                f"{getattr(record, 'event_id', 'record')}: observed "
                f"{provenance.observed_at.isoformat()} "
                f"({int(age.total_seconds() // 60)} min old)"
            )
    return stale


def _rights_cleared(records: Iterable[object]) -> tuple[bool, str | None]:
    for record in records:
        try:
            require_allowed_use(record)
        except RightsError as exc:
            return False, str(exc)
    return True, None


def run_pipeline(
    config: RunConfig,
    events: Sequence[GameEvent],
    injuries: Sequence[InjuryRecord] = (),
    quotes: Sequence[MarketQuote] = (),
    strategy: Callable[[RunConfig, Sequence[GameEvent], Sequence[InjuryRecord]], Sequence[Forecast]]
    | None = None,
) -> RunReport:
    """Execute one pipeline run and return an auditable report.

    ``strategy`` is supplied by the caller; the pipeline owns the horizon,
    freshness, rights and pick-decision logic, not the modelling.
    """
    started = config.now_utc.astimezone(timezone.utc)
    report = RunReport(
        run_id=config.run_id,
        started_at=started,
        finished_at=started,
        horizon_start=started,
        horizon_end=started + timedelta(hours=config.horizon_hours),
        timezone_name=config.timezone_name,
    )

    slate = select_slate(events, started, config.horizon_hours)
    report.slate_event_ids = [event.event_id for event in slate]

    inputs = list(events) + list(injuries) + list(quotes)
    report.input_snapshot_hash = snapshot_hash(
        {
            "events": [event.provenance.as_dict() for event in events],
            "injuries": [record.provenance.as_dict() for record in injuries],
            "quotes": [quote.provenance.as_dict() for quote in quotes],
            "config": {
                "run_id": config.run_id,
                "now_utc": config.now_utc.isoformat(),
                "horizon_hours": config.horizon_hours,
                "timezone_name": config.timezone_name,
                "max_input_age_minutes": config.max_input_age_minutes,
                "model_version": config.model_version,
            },
        }
    )

    cleared, rights_error = _rights_cleared(inputs)
    report.rights_cleared = cleared
    if rights_error:
        report.notes.append(f"rights: {rights_error}")
        report.suppressed.append(
            {
                "scope": "run",
                "reason_code": "RIGHTS_NOT_CLEARED",
                "detail": rights_error,
            }
        )
        report.finished_at = started
        return report

    stale = stale_records(inputs, started, config.max_input_age_minutes)
    report.stale_inputs = stale
    if stale:
        report.suppressed.append(
            {
                "scope": "run",
                "reason_code": "STALE_DATA",
                "detail": "; ".join(stale),
            }
        )
        report.finished_at = started
        return report

    if strategy is None:
        report.notes.append("no strategy supplied: no forecast was produced")
        report.finished_at = started
        return report

    slate_injuries = [record for record in injuries if record.event_id in report.slate_event_ids]
    forecasts = list(strategy(config, slate, slate_injuries))
    report.forecasts = [
        {
            "forecast_id": forecast.forecast_id,
            "event_id": forecast.event_id,
            "market_type": forecast.market_type.value,
            "side": forecast.side,
            "line": forecast.line,
            "probability": forecast.probability,
            "model_version": forecast.model_version,
            "emitted_at": forecast.emitted_at.isoformat(),
            "input_snapshot_hash": forecast.input_snapshot_hash,
        }
        for forecast in forecasts
    ]

    quote_index: dict[tuple[str, str], list[MarketQuote]] = {}
    for quote in quotes:
        quote_index.setdefault((quote.event_id, quote.market_type.value), []).append(quote)

    for forecast in forecasts:
        pick = _decide(config, forecast, quote_index, started)
        report.picks.append(
            {
                "pick_id": pick.pick_id,
                "forecast_id": pick.forecast_id,
                "event_id": pick.event_id,
                "decision": pick.decision,
                "stake_fraction": pick.stake_fraction,
                "edge": pick.edge,
                "reason_codes": list(pick.reason_codes),
                "model_version": pick.model_version,
                "emitted_at": pick.emitted_at.isoformat() if pick.emitted_at else None,
            }
        )
        if pick.decision == "no_bet":
            report.suppressed.append(
                {
                    "scope": forecast.forecast_id,
                    "reason_code": pick.reason_codes[0] if pick.reason_codes else "GATE_FAILED",
                    "detail": REASON_CODES.get(
                        pick.reason_codes[0] if pick.reason_codes else "", "gate failed"
                    ),
                }
            )

    report.finished_at = started
    return report


def _decide(
    config: RunConfig,
    forecast: Forecast,
    quote_index: dict[tuple[str, str], list[MarketQuote]],
    now_utc: datetime,
) -> Pick:
    """Turn a forecast into a pick or a documented no-bet decision."""
    reason_codes: list[str] = []
    if not config.market_specified:
        reason_codes.append("NO_MARKET_SPEC")
    if not quote_index.get((forecast.event_id, forecast.market_type.value)):
        reason_codes.append("NO_BENCHMARK_QUOTE")

    edge: float | None = None
    matching = quote_index.get((forecast.event_id, forecast.market_type.value), [])
    if matching:
        best = max(matching, key=lambda q: q.provenance.observed_at)
        edge = forecast.probability * best.price_decimal - 1.0

    if reason_codes:
        return Pick(
            pick_id=f"{forecast.forecast_id}-nobet",
            forecast_id=forecast.forecast_id,
            event_id=forecast.event_id,
            decision="no_bet",
            stake_fraction=0.0,
            edge=edge,
            reason_codes=tuple(reason_codes),
            model_version=forecast.model_version,
            emitted_at=now_utc,
        )
    return Pick(
        pick_id=f"{forecast.forecast_id}-bet",
        forecast_id=forecast.forecast_id,
        event_id=forecast.event_id,
        decision="bet",
        stake_fraction=0.0,  # stake policy is a separate, declared decision
        edge=edge,
        reason_codes=("GATES_PASSED",),
        model_version=forecast.model_version,
        emitted_at=now_utc,
    )


def write_ledger(path: str, payload: object) -> str:
    """Write a ledger file atomically, returning its SHA-256 digest."""
    data = canonical_json(payload) + "\n"
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(data)
    os.replace(tmp, path)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def append_ledger(path: str, payload: object) -> str:
    """Append one record to an append-only JSON Lines ledger."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    line = canonical_json(payload) + "\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line)
    return hashlib.sha256(line.encode("utf-8")).hexdigest()
