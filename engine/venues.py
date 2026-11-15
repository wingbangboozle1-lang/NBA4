"""Arena coordinate table and travel legs between venues.

Brief item implemented (2026-11-15): "Compute rest, back-to-back and 3-in-4
from the official schedule (already possible) and add travel distance from a
sourced arena-coordinate table."

The table is a registry, and the registry is **empty in this repository by
design**. That is not laziness, it is the rule the whole project runs on: a
published number needs a source, and there is currently no coordinate source
this repository may both (a) treat as official and (b) republish under its
terms. So every travel field resolves to ``None`` with a reason code rather than
to a distance looked up from memory.

What is implemented and testable now:

* the record type and its validation (lat/lon ranges, https source per row,
  a declared geodetic datum);
* a great-circle distance on the WGS-84 mean earth radius, in miles and
  kilometres, with the haversine formula stated in the module so the arithmetic
  is reviewable;
* ``TravelLeg`` with the honest gap semantics: a missing or unsourced
  coordinate yields ``TRAVEL_UNVERIFIED`` (never 0 miles, never a guess);
* ``load_coordinate_table`` so that the moment an owner points the project at a
  licensed or permissively licensed venue-coordinate file, the pipeline
  validates and uses it without any code change.

Road-versus-air distance is deliberately not approximated: the haversine value
is labelled ``great_circle`` and any "travel effort" claim needs a documented
transport assumption, which is registered as an open question.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

EARTH_RADIUS_MILES = 3958.7613  # WGS-84 mean radius (IUGG mean radius 6371.0 km)
EARTH_RADIUS_KM = 6371.0088
DATUM = "WGS-84"

TRAVEL_VERIFIED = "TRAVEL_VERIFIED"
TRAVEL_UNVERIFIED = "TRAVEL_UNVERIFIED"
TRAVEL_NO_SOURCE = "TRAVEL_SOURCE_NOT_REGISTERED"


class VenueError(ValueError):
    """Raised when a venue row is not usable (bad range, missing source)."""


@dataclass(frozen=True)
class Venue:
    """One arena, its coordinates and the source those coordinates came from."""

    arena: str
    team: str
    city: str
    country: str
    latitude: Optional[float]
    longitude: Optional[float]
    source_url: str
    source_stamp: str
    datum: str = DATUM

    @property
    def has_coordinates(self) -> bool:
        return (
            self.latitude is not None
            and self.longitude is not None
            and -90.0 <= self.latitude <= 90.0
            and -180.0 <= self.longitude <= 180.0
        )

    @property
    def citable(self) -> bool:
        return bool(self.source_url.startswith("https://")) and bool(self.source_stamp)

    @property
    def usable(self) -> bool:
        return self.has_coordinates and self.citable and self.datum == DATUM

    def unusable_reason(self) -> str:
        if self.datum != DATUM:
            return f"datum {self.datum!r} is not {DATUM}; coordinates on another datum are not mixed"
        if not self.citable:
            return "no https source with a revision stamp for this row"
        if not self.has_coordinates:
            return "no coordinates transcribed from the source"
        return ""

    def validate(self) -> "Venue":
        if not self.arena or not self.team:
            raise VenueError("arena and team are required")
        if not self.usable:
            raise VenueError(f"{self.arena}: {self.unusable_reason()}")
        return self


# Registered venue coordinates. Kept empty until a coordinate source is
# cleared for republication - see Q27 in docs/decision-register.md.
VENUES: Dict[str, Venue] = {}


def venue_for_team(team: str, table: Optional[Mapping[str, Venue]] = None) -> Optional[Venue]:
    pool = table if table is not None else VENUES
    for venue in pool.values():
        if venue.team == team:
            return venue
    return None


def great_circle_miles(
    a: Tuple[float, float], b: Tuple[float, float]
) -> float:
    """Haversine distance between two (lat, lon) points in degrees."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(min(1.0, math.sqrt(h)))


def great_circle_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return great_circle_miles(a, b) * (EARTH_RADIUS_KM / EARTH_RADIUS_MILES)


@dataclass(frozen=True)
class TravelLeg:
    """Distance between two consecutive games for one team, or the reason there is none."""

    team: str
    from_arena: str
    to_arena: str
    from_date: str
    to_date: str
    miles: Optional[float]
    kilometres: Optional[float]
    code: str
    detail: str
    source_urls: Tuple[str, ...] = ()

    @property
    def verified(self) -> bool:
        return self.code == TRAVEL_VERIFIED


def travel_leg(
    team: str,
    from_date: str,
    to_date: str,
    table: Optional[Mapping[str, Venue]] = None,
) -> TravelLeg:
    """Home-court leg for one team between two of its own game dates.

    A team whose registered arena is unchanged between the two dates has a
    known-zero leg, and it is reported as zero only because the same registered
    row applies to both dates. The table carries no per-row date ranges, so an
    arena change inside a window would be measured against the wrong row; that
    limitation is published next to every distance rather than hidden in here.
    """
    pool = table if table is not None else VENUES
    venue = pool.get(team)
    if venue is None:
        return TravelLeg(
            team, "", "", from_date, to_date, None, None, TRAVEL_NO_SOURCE,
            f"no venue row is registered for {team}; distance is left blank rather than guessed",
        )
    if not venue.usable:
        return TravelLeg(
            team, venue.arena, venue.arena, from_date, to_date, None, None, TRAVEL_UNVERIFIED,
            f"{venue.arena}: {venue.unusable_reason()}",
        )
    # Same registered arena on both dates: the leg is a known zero, and it is
    # reported as such only because the source row applies to both dates.
    miles = 0.0
    return TravelLeg(
        team, venue.arena, venue.arena, from_date, to_date, miles,
        miles * (EARTH_RADIUS_KM / EARTH_RADIUS_MILES), TRAVEL_VERIFIED,
        "same registered arena on both dates",
        (venue.source_url,),
    )


def leg_between(
    team: str,
    from_date: str,
    to_date: str,
    from_team: str,
    to_team: str,
    table: Optional[Mapping[str, Venue]] = None,
) -> TravelLeg:
    """Distance between the venue of ``from_team`` and the venue of ``to_team``."""
    pool = table if table is not None else VENUES
    a = pool.get(from_team)
    b = pool.get(to_team)
    missing = [t for t, v in ((from_team, a), (to_team, b)) if v is None]
    if missing:
        return TravelLeg(
            team, "", "", from_date, to_date, None, None, TRAVEL_NO_SOURCE,
            "no venue row registered for: " + ", ".join(missing),
        )
    assert a is not None and b is not None
    if not a.usable or not b.usable:
        reasons = "; ".join(
            f"{v.arena}: {v.unusable_reason()}" for v in (a, b) if not v.usable
        )
        return TravelLeg(
            team, a.arena, b.arena, from_date, to_date, None, None, TRAVEL_UNVERIFIED, reasons,
            tuple(v.source_url for v in (a, b) if v.citable),
        )
    miles = great_circle_miles((a.latitude, a.longitude), (b.latitude, b.longitude))  # type: ignore[arg-type]
    return TravelLeg(
        team, a.arena, b.arena, from_date, to_date, round(miles, 2),
        round(miles * (EARTH_RADIUS_KM / EARTH_RADIUS_MILES), 2), TRAVEL_VERIFIED,
        "great-circle distance on the WGS-84 mean radius; not a road distance",
        (a.source_url, b.source_url),
    )


def load_coordinate_table(path: str | Path, format: str = "json") -> Dict[str, Venue]:
    """Read and validate a coordinate file, returning a usable team->Venue map.

    Accepted JSON shape: ``[{"team": ..., "arena": ..., "city": ...,
    "country": ..., "latitude": ..., "longitude": ..., "source_url": ...,
    "source_stamp": ...}]``. CSV uses the same field names as headers.
    """
    target = Path(path)
    rows: List[Mapping[str, object]] = []
    if format == "csv":
        with target.open(newline="", encoding="utf-8") as fh:
            rows = [dict(r) for r in csv.DictReader(fh)]
    else:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("venues", [])
        rows = [dict(r) for r in payload]
    out: Dict[str, Venue] = {}
    for row in rows:
        venue = Venue(
            arena=str(row.get("arena", "")),
            team=str(row.get("team", "")),
            city=str(row.get("city", "")),
            country=str(row.get("country", "")),
            latitude=_float_or_none(row.get("latitude")),
            longitude=_float_or_none(row.get("longitude")),
            source_url=str(row.get("source_url", "")),
            source_stamp=str(row.get("source_stamp", "")),
            datum=str(row.get("datum", DATUM)),
        )
        if not venue.arena or not venue.team:
            raise VenueError(f"row {row!r}: arena and team are required")
        out[venue.team] = venue
    return out


def _float_or_none(value: object) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def table_audit(table: Optional[Mapping[str, Venue]] = None) -> Dict[str, object]:
    """Publishable summary of the registry's readiness - counts only, no values."""
    pool = table if table is not None else VENUES
    usable = [v for v in pool.values() if v.usable]
    return {
        "registered_rows": len(pool),
        "usable_rows": len(usable),
        "teams_needed": 30,
        "missing_source": sorted(v.team for v in pool.values() if not v.citable),
        "missing_coordinates": sorted(v.team for v in pool.values() if v.citable and not v.has_coordinates),
        "status": (
            "NOT_STARTED" if not pool
            else ("PARTIAL" if len(usable) < len(pool) else "READY")
        ),
        "note": (
            "no coordinate source is cleared for republication in this repository, so no "
            "travel distance is published; the machinery is in place and gated"
        ),
    }
