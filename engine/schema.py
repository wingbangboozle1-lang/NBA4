"""Record schemas for the authorized-inputs ledger and forecast ledgers.

Every record that enters the pipeline must carry provenance: an official
source URL, the time the source states/updates the fact (source_time) and
the time we observed it (observed_at). Records failing validation are
rejected - the pipeline never invents values to fill gaps.

Timezone-aware datetimes are required everywhere (ISO-8601 with offset).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


class SchemaError(ValueError):
    """Raised when a record does not satisfy the provenance rules."""


def _parse_time(value: str, field_name: str, record_id: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"{record_id}: {field_name} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise SchemaError(f"{record_id}: {field_name} must include a UTC offset: {value!r}")
    return parsed.astimezone(timezone.utc)


def _require_https(url: str, field_name: str, record_id: str) -> str:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise SchemaError(f"{record_id}: {field_name} must be an https:// official source URL: {url!r}")
    return url


@dataclass(frozen=True)
class Provenance:
    """Source citation attached to every observation."""

    source_url: str
    source_time: str  # when the source states the fact
    observed_at: str  # when we saw it

    def validated(self, record_id: str) -> "Provenance":
        _require_https(self.source_url, "source_url", record_id)
        _parse_time(self.source_time, "source_time", record_id)
        _parse_time(self.observed_at, "observed_at", record_id)
        return self

    @property
    def observed_dt(self) -> datetime:
        return _parse_time(self.observed_at, "observed_at", "provenance")

    @property
    def source_dt(self) -> datetime:
        return _parse_time(self.source_time, "source_time", "provenance")


@dataclass(frozen=True)
class TeamGame:
    """One team's line in one completed game (authorized data only)."""

    record_id: str
    game_id: str
    game_date: str  # ISO-8601 tip time with offset
    team: str
    opponent: str
    is_home: bool
    points: float
    opp_points: float
    possessions: Optional[float] = None  # if the licensed feed supplies it
    provenance: Provenance = field(default_factory=lambda: Provenance("", "", ""))

    def validate(self) -> "TeamGame":
        _parse_time(self.game_date, "game_date", self.record_id)
        if not self.team or not self.opponent:
            raise SchemaError(f"{self.record_id}: team/opponent required")
        if self.points < 0 or self.opp_points < 0:
            raise SchemaError(f"{self.record_id}: negative points")
        self.provenance.validated(self.record_id)
        return self


@dataclass(frozen=True)
class PlayerGame:
    """One player's minutes/production line in one completed game."""

    record_id: str
    game_id: str
    game_date: str
    player: str
    team: str
    minutes: float
    points: float
    rebounds: float = 0.0
    assists: float = 0.0
    provenance: Provenance = field(default_factory=lambda: Provenance("", "", ""))

    def validate(self) -> "PlayerGame":
        _parse_time(self.game_date, "game_date", self.record_id)
        if self.minutes < 0 or self.minutes > 53:  # regulation + 2 OTs ceiling
            raise SchemaError(f"{self.record_id}: minutes out of range: {self.minutes}")
        self.provenance.validated(self.record_id)
        return self


VALID_STATUSES = ("Out", "Doubtful", "Questionable", "Probable", "Available")


@dataclass(frozen=True)
class InjuryObservation:
    """One player's reported participation status at one point in time."""

    record_id: str
    report_time: str  # timestamp the report itself carries
    game_id: str
    team: str
    player: str
    status: str
    reason: str
    provenance: Provenance = field(default_factory=lambda: Provenance("", "", ""))

    def validate(self) -> "InjuryObservation":
        _parse_time(self.report_time, "report_time", self.record_id)
        if self.status not in VALID_STATUSES:
            raise SchemaError(
                f"{self.record_id}: status {self.status!r} not in {VALID_STATUSES}"
            )
        self.provenance.validated(self.record_id)
        return self


@dataclass(frozen=True)
class SlateGame:
    """One upcoming game on the slate (from an authorized schedule feed)."""

    record_id: str
    game_id: str
    tip_time: str  # ISO-8601 with offset
    home_team: str
    away_team: str
    provenance: Provenance = field(default_factory=lambda: Provenance("", "", ""))

    def validate(self) -> "SlateGame":
        _parse_time(self.tip_time, "tip_time", self.record_id)
        if not self.home_team or not self.away_team:
            raise SchemaError(f"{self.record_id}: home_team/away_team required")
        self.provenance.validated(self.record_id)
        return self


@dataclass(frozen=True)
class MarketQuote:
    """A licensed market quote kept strictly separate from model output."""

    record_id: str
    game_id: str
    market: str  # e.g. "spread", "total", "player_points"
    side: str
    line: Optional[float]
    price: Optional[float]
    quoted_at: str
    settlement_rule: str
    provenance: Provenance = field(default_factory=lambda: Provenance("", "", ""))

    def validate(self) -> "MarketQuote":
        _parse_time(self.quoted_at, "quoted_at", self.record_id)
        if not self.market or not self.settlement_rule:
            raise SchemaError(f"{self.record_id}: market and settlement_rule required")
        self.provenance.validated(self.record_id)
        return self


@dataclass(frozen=True)
class PickRecord:
    """An immutable forecast record.

    status is always one of:
      * "NO PICK" - output suppressed (gates failed, inputs missing, or
        unresolved availability). reason_codes explain why.
      * "SHADOW"  - forecast recorded for the no-bet shadow ledger (G11).
      * "ELIGIBLE" - only when every gate has passed on frozen data; this
        engine never sets ELIGIBLE from synthetic or unverified inputs.
    """

    pick_id: str
    issued_at: str
    model_version: str
    code_version: str
    market: str
    selection: str
    originated_line: Optional[float]
    forecast_probability: Optional[float]
    fair_price: Optional[float]
    benchmark_quote_id: Optional[str]
    horizon_end: str
    status: str
    reason_codes: tuple
    input_snapshot: tuple  # ledger record ids used
    verification: str = "unverified"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["reason_codes"] = list(self.reason_codes)
        d["input_snapshot"] = list(self.input_snapshot)
        return d


STATUS_NO_PICK = "NO PICK"
STATUS_SHADOW = "SHADOW"
STATUS_ELIGIBLE = "ELIGIBLE"

ALLOWED_PICK_STATUSES = (STATUS_NO_PICK, STATUS_SHADOW, STATUS_ELIGIBLE)
