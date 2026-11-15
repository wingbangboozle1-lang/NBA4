"""Open Location Code (plus code) decoding for arena coordinates.

Some venues do not publish a map coordinate anywhere on their own site, and the
U.S. Census geocoder has no address range for a handful of them (TD Garden,
Madison Square Garden, Scotiabank Arena, Chase Center, Rocket Arena, the
Smoothie King Center, the Frost Bank Center and the State Farm Arena).  Google
Maps publishes a *plus code* for each of those venues on its place listing,
and a plus code is a deterministic, publicly documented encoding of a point on
the Earth's surface.

This module implements the Open Location Code reference algorithm:

  * the code alphabet is base 20 ("23456789CFGHJMPQRVWX"),
  * digits alternate between latitude and longitude,
  * the leading pair selects a 20 deg x 20 deg cell and every further pair
    divides the cell by 20 in each dimension,
  * a *short* code omits its leading digits, so the missing prefix is
    recovered from a reference location by picking the candidate cell whose
    centre lies closest to that reference.

Nothing here is a guess: `decode_short_code` returns the centre of the exact
cell that Google published, and the recovery step is validated against
independent coordinates in `tests/test_engine_ext.py`.
"""

from __future__ import annotations

import itertools
import math

ALPHABET = "23456789CFGHJMPQRVWX"
LAT_MAX = 90.0
LON_MAX = 180.0
EARTH_RADIUS_KM = 6371.0088


class PlusCodeError(ValueError):
    """Raised when a plus code cannot be interpreted."""


def _digits(code: str) -> str:
    return code.replace("+", "").replace(" ", "").replace(",", "").upper()


def decode_cell(code: str, digits: int = 10):
    """Decode a full plus code into its bounding cell.

    Returns ``(lat_lo, lat_hi, lon_lo, lon_hi)``.
    """
    s = _digits(code)[:digits]
    if not s:
        raise PlusCodeError("empty plus code")
    for ch in s:
        if ch not in ALPHABET:
            raise PlusCodeError(f"invalid plus-code character {ch!r}")

    lat_lo, lat_hi = -LAT_MAX, LAT_MAX
    lon_lo, lon_hi = -LON_MAX, LON_MAX
    lat_place, lon_place = 400.0, 400.0
    for i, ch in enumerate(s):
        value = ALPHABET.index(ch)
        if i % 2 == 0:  # latitude digit
            lat_place /= 20.0
            step = min(lat_place, lat_hi - lat_lo)
            lat_lo += value * step
            lat_hi = lat_lo + step
            lat_place = step
        else:  # longitude digit
            lon_place /= 20.0
            step = min(lon_place, lon_hi - lon_lo)
            lon_lo += value * step
            lon_hi = lon_lo + step
            lon_place = step
    return lat_lo, lat_hi, lon_lo, lon_hi


def decode_short_code(short_code: str, ref_lat: float, ref_lon: float):
    """Decode a short plus code using a reference location.

    The returned mapping contains the recovered full code, the centre of the
    decoded cell and the distance (metres) from the reference to that centre.
    The reference only selects *which* candidate cell applies; the precision
    of the answer comes from the published code itself.
    """
    s = _digits(short_code)
    missing = 10 - len(s)
    if missing <= 0 or missing % 2 != 0:
        raise PlusCodeError(f"not a recoverable short code: {short_code!r}")

    best = None
    for combo in itertools.product(range(20), repeat=missing):
        digits = "".join(ALPHABET[c] for c in combo) + s
        lat_lo, lat_hi, lon_lo, lon_hi = decode_cell(digits, 10)
        lat = (lat_lo + lat_hi) / 2.0
        lon = (lon_lo + lon_hi) / 2.0
        dist = haversine_km(ref_lat, ref_lon, lat, lon)
        if best is None or dist < best["distance_km"]:
            best = {
                "short_code": short_code,
                "full_code": digits[:8] + "+" + digits[8:],
                "latitude": lat,
                "longitude": lon,
                "cell": (lat_lo, lat_hi, lon_lo, lon_hi),
                "distance_km": dist,
                "reference_latitude": ref_lat,
                "reference_longitude": ref_lon,
            }
    return best


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in kilometres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))
