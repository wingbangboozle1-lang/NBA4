"""Data contracts for the NBA4 reference engine.

Every record carries provenance and an explicit permission flag. The engine
refuses to build a forecast or a pick from a record that is not permitted for
the intended use, and it refuses records that lack timestamps.

Schema shapes follow the fields that the official NBA injury report publishes
(Game Date, Game Time, Matchup, Team, Player Name, Current Status, Reason) and
the league's reporting policy; see ``docs/source-verification.md`` for the
verified source links.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

__all__ = [
    "RightsError",
    "ContractError",
    "Provenance",
    "Status",
    "MarketType",
    "GameEvent",
    "InjuryRecord",
    "PlayerGameStat",
    "MarketQuote",
    "Forecast",
    "Pick",
    "canonical_json",
    "snapshot_hash",
    "require_allowed_use",
    "require_timestamp_order",
]


class ContractError(ValueError):
    """Raised when a record does not satisfy the data contract."""


class RightsError(ContractError):
    """Raised when a record may not be used for the requested purpose."""


def _utc(value: datetime) -> datetime:
    """Return an aware UTC datetime; naive datetimes are rejected."""
    if value.tzinfo is None:
        raise ContractError("timestamps must be timezone aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Provenance:
    """Where a record came from and when it was true.

    ``allowed_use`` is *not* a legal determination; it is the contract field an
    operator sets after confirming the licence/permission terms for the
    specific use (for example: historical storage, model features, public
    display). The engine only enforces the flag; it cannot verify a contract.
    """

    source_id: str
    source_name: str
    source_url: str
    source_timestamp: datetime
    observed_at: datetime
    version: str
    allowed_use: bool = False
    allowed_use_note: str = ""

    def __post_init__(self) -> None:
        if not self.source_id or not self.source_name:
            raise ContractError("provenance requires source_id and source_name")
        if not self.source_url.startswith("https://"):
            raise ContractError("provenance requires an https source_url")
        if not self.version:
            raise ContractError("provenance requires a version")
        source_ts = _utc(self.source_timestamp)
        observed = _utc(self.observed_at)
        if observed < source_ts:
            raise ContractError(
                "observed_at precedes source_timestamp: a record cannot be ingested "
                "before its source published it"
            )

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_timestamp"] = self.source_timestamp.isoformat()
        data["observed_at"] = self.observed_at.isoformat()
        return data


class Status(str, Enum):
    """Injury statuses as published in the official NBA injury report."""

    AVAILABLE = "Available"
    QUESTIONABLE = "Questionable"
    DOUBTFUL = "Doubtful"
    PROBABLE = "Probable"
    OUT = "Out"
    NOT_WITH_TEAM = "Not With Team"
    UNKNOWN = "Unknown"


class MarketType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    PLAYER_PROP = "player_prop"
    PROP_COMBO = "prop_combo"
    PARLAY = "parlay"


def _coerce_market_type(value: "MarketType | str") -> MarketType:
    """Accept either the enum or its string value and return the enum."""
    if isinstance(value, MarketType):
        return value
    try:
        return MarketType(value)
    except ValueError as exc:
        raise ContractError(f"unknown market type: {value!r}") from exc


@dataclass(frozen=True)
class GameEvent:
    """A scheduled game, as published by an authorised schedule feed."""

    event_id: str
    tipoff_utc: datetime
    home_team_id: str
    away_team_id: str
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ContractError("event_id is required")
        _utc(self.tipoff_utc)


@dataclass(frozen=True)
class InjuryRecord:
    """One reported injury/participation status entry."""

    event_id: str
    player_id: str
    status: Status
    reason: str
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.event_id or not self.player_id:
            raise ContractError("event_id and player_id are required")
        if not isinstance(self.status, Status):
            raise ContractError("status must be a Status value")


@dataclass(frozen=True)
class PlayerGameStat:
    """A single player-game line from an authorised results feed."""

    event_id: str
    player_id: str
    team_id: str
    minutes: float
    points: float
    rebounds: float
    assists: float
    provenance: Provenance

    def __post_init__(self) -> None:
        if self.minutes < 0:
            raise ContractError("minutes cannot be negative")
        if min(self.points, self.rebounds, self.assists) < 0:
            raise ContractError("stat counts cannot be negative")


@dataclass(frozen=True)
class MarketQuote:
    """A market quote (line + price) from a licensed benchmark feed.

    Quotes are stored separately from model output so that an originated line is
    never derived from a market price.
    """

    market_id: str
    event_id: str
    market_type: MarketType
    side: str
    line: float | None
    price_decimal: float
    quote_timestamp: datetime
    provider_id: str
    provenance: Provenance

    def __post_init__(self) -> None:
        if self.price_decimal <= 1.0:
            raise ContractError("decimal price must be greater than 1.0")
        market_type = _coerce_market_type(self.market_type)
        object.__setattr__(self, "market_type", market_type)
        if market_type in (MarketType.SPREAD, MarketType.TOTAL) and self.line is None:
            raise ContractError("spread and total quotes require a line")
        _utc(self.quote_timestamp)


@dataclass(frozen=True)
class Forecast:
    """An immutable, model-originated forecast record."""

    forecast_id: str
    event_id: str
    market_type: MarketType
    side: str
    model_version: str
    emitted_at: datetime
    line: float | None
    probability: float
    input_snapshot_hash: str
    provenance: Provenance
    notes: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ContractError("probability must be within [0, 1]")
        if not self.input_snapshot_hash:
            raise ContractError("input_snapshot_hash is required for reproducibility")
        object.__setattr__(self, "market_type", _coerce_market_type(self.market_type))
        _utc(self.emitted_at)


@dataclass(frozen=True)
class Pick:
    """A bet/no-bet decision attached to a forecast.

    ``decision`` is ``"no_bet"`` unless every gate in the validation plan
    passed and a licensed benchmark quote exists. ``reason_codes`` explains
    every outcome, including the suppression cases.
    """

    pick_id: str
    forecast_id: str
    event_id: str
    decision: str
    stake_fraction: float
    edge: float | None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    model_version: str = ""
    emitted_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.decision not in ("bet", "no_bet"):
            raise ContractError("decision must be 'bet' or 'no_bet'")
        if self.decision == "bet" and not self.reason_codes:
            raise ContractError("a bet pick must carry reason codes")
        if not 0.0 <= self.stake_fraction <= 1.0:
            raise ContractError("stake_fraction must be within [0, 1]")


def canonical_json(payload: Any) -> str:
    """Canonical JSON used for hashing (sorted keys, no insignificant space)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def snapshot_hash(payload: Mapping[str, Any]) -> str:
    """SHA-256 hash of an input snapshot, used to bind a forecast to its inputs."""
    return hashlib.sha256(canonical_json(dict(payload)).encode("utf-8")).hexdigest()


def require_allowed_use(record: Any, purpose: str = "betting model input") -> None:
    """Raise :class:`RightsError` unless the record's permission flag is set."""
    provenance = getattr(record, "provenance", None)
    if provenance is None:
        raise RightsError(f"{record!r} has no provenance and cannot be used")
    if not provenance.allowed_use:
        raise RightsError(
            f"source {provenance.source_id!r} is not cleared for {purpose}; "
            "obtain written permission or a licensed contract first"
        )


def require_timestamp_order(forecast: Forecast, records: list[Any]) -> None:
    """Ensure every input was observed strictly before the forecast was emitted.

    This is the mechanical leakage check for the validation plan: a forecast may
    not use a record that was observed at or after the forecast timestamp.
    """
    emitted = _utc(forecast.emitted_at)
    for record in records:
        observed = _utc(record.provenance.observed_at)
        if observed >= emitted:
            raise ContractError(
                f"leakage: input {getattr(record, 'event_id', record)} was observed at "
                f"{observed.isoformat()} which is not before the forecast at "
                f"{emitted.isoformat()}"
            )
