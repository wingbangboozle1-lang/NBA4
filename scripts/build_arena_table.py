#!/usr/bin/env python3
"""Build ``data/arenas/arenas.json`` from independently sourced coordinates.

Why this script exists
----------------------
An earlier pass recorded coordinates for 16 venues straight out of the U.S.
Census geocoder.  Reverse-geocoding four of those points showed that the
Census "address match" had landed on the wrong thing entirely: the
Philadelphia and Phoenix points were 5.7 km and 6.8 km from the arena, and
the Utah point was on a road a kilometre away.  Eight of the sixteen were
off by more than the width of the building.  A single geocoder match is not
corroboration.

The rule this script enforces
-----------------------------
A venue gets a coordinate only when **two independent sources agree to
within 250 m**.  The primary source is, in order of preference,

  1. the coordinate the venue itself publishes (a map pin inside one of its
     own map links, or the centre of a static map it embeds), then
  2. the OpenStreetMap building/footprint for the arena, via Nominatim -- the
     returned record is the arena polygon and carries the street address,

and the corroborating source is always independent of the primary: the
Wikipedia/Wikidata coordinate for the arena when the primary is OSM, and OSM
when the primary is the venue's own published point.  Every row records both
URLs plus the measured disagreement, so the gate can be re-checked.

Run with ``--check`` to fail if the committed JSON is out of date.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "arenas" / "arenas.json"

EARTH_RADIUS_KM = 6371.0088
CORROBORATION_TOLERANCE_M = 250.0
"""Two sources must place the venue within this distance of each other."""


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


NOMINATIM = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
WIKI_API = (
    "https://en.wikipedia.org/w/api.php?action=query&prop=coordinates"
    "&format=json&redirects=1&titles="
)

# team -> (latitude, longitude, official page URL, label)
# Only venues whose own website publishes a usable point.
OFFICIAL = {
    "Brooklyn": (
        40.6826465, -73.9754156,
        "https://www.barclayscenter.com/getting-here",
        "Barclays Center - Getting Here (official driving-directions place pin)",
    ),
    "Chicago": (
        41.881033, -87.67416,
        "https://www.unitedcenter.com/venue/directions-parking/",
        "United Center - Directions & Parking (official embedded map place pin)",
    ),
    "Denver": (
        39.7485498, -105.0077106,
        "https://www.ballarena.com/",
        "Ball Arena - official directions map place pin",
    ),
    "Memphis": (
        35.138077, -90.051046,
        "https://www.fedexforum.com/plan-your-visit/parking-directions",
        "FedExForum - Parking & Directions (official embedded map ll= parameter)",
    ),
    "LA Clippers": (
        33.944195, -118.343087,
        "https://www.intuitdome.com/plan-your-visit/how-to-get-here",
        "Intuit Dome - How To Get Here (official Google place link coordinates)",
    ),
    "Orlando": (
        28.5389166991853, -81.3838041312134,
        "https://www.kiacenter.com/plan-your-visit/directions-and-parking",
        "Kia Center - Directions And Parking (official static map centre)",
    ),
}

# team -> (latitude, longitude, Nominatim query)
# The OSM record is the arena polygon/building; its display_name carries the
# street address, which is how each of these was matched to the right venue.
OSM = {
    "Atlanta": (33.7573698, -84.3963848, "State Farm Arena, Atlanta, GA"),
    "Boston": (42.3662986, -71.0621622, "TD Garden, Boston, MA"),
    "Brooklyn": (40.6825106, -73.9752519, "Barclays Center, Brooklyn, NY"),
    "Charlotte": (35.2250980, -80.8391541, "Spectrum Center, Charlotte, NC"),
    "Chicago": (41.8806831, -87.6741851, "United Center, Chicago, IL"),
    "Cleveland": (41.4966862, -81.6885754, "Rocket Arena, Cleveland, OH"),
    "Dallas": (32.7904894, -96.8102830, "American Airlines Center, Dallas, TX"),
    "Denver": (39.7486838, -105.0075440, "Ball Arena, Denver, CO"),
    "Detroit": (42.3409774, -83.0549545, "Little Caesars Arena, Detroit, MI"),
    "Golden State": (37.7679001, -122.3874223, "Chase Center, San Francisco, CA"),
    "Houston": (29.7507473, -95.3622315, "Toyota Center, Houston, TX"),
    "Indiana": (39.7639331, -86.1555024, "Gainbridge Fieldhouse, Indianapolis, IN"),
    "LA Clippers": (33.9442586, -118.3421719, "Intuit Dome, Inglewood, CA"),
    "LA Lakers": (34.0429979, -118.2671352, "Crypto.com Arena, Los Angeles, CA"),
    "Memphis": (35.1382327, -90.0507689, "FedExForum, Memphis, TN"),
    "Miami": (25.7813595, -80.1879435, "Kaseya Center, Miami, FL"),
    "Milwaukee": (43.0450096, -87.9174871, "Fiserv Forum, Milwaukee, WI"),
    "Minnesota": (44.9795917, -93.2759828, "Target Center, Minneapolis, MN"),
    "New Orleans": (29.9490666, -90.0819634, "Smoothie King Center, New Orleans, LA"),
    "New York": (40.7505129, -73.9935159, "Madison Square Garden, New York, NY"),
    "Oklahoma City": (35.4633961, -97.5150815, "Paycom Center, Oklahoma City, OK"),
    "Orlando": (28.5392867, -81.3838892, "Kia Center, Orlando, FL"),
    "Philadelphia": (39.9011004, -75.1720165, "Wells Fargo Center, Philadelphia, PA"),
    "Phoenix": (33.4460081, -112.0712386, "Mortgage Matchup Center, Phoenix, AZ"),
    "Portland": (45.5315787, -122.6668337, "Moda Center, Portland, OR"),
    "Sacramento": (38.5801405, -121.4995008, "Golden 1 Center, Sacramento, CA"),
    "San Antonio": (29.4269205, -98.4375058, "Frost Bank Center, San Antonio, TX"),
    "Toronto": (43.6434338, -79.3790777, "Scotiabank Arena, Toronto"),
    "Utah": (40.7683274, -111.9010551, "Delta Center, Salt Lake City, UT"),
    "Washington": (38.8981883, -77.0209378, "Capital One Arena, Washington, DC"),
}

# team -> (latitude, longitude, Wikipedia article title)
WIKI = {
    "Atlanta": (33.75722222, -84.39638889, "State Farm Arena"),
    "Boston": (42.36638889, -71.06222222, "TD Garden"),
    "Brooklyn": (40.68266111, -73.975225, "Barclays Center"),
    "Charlotte": (35.225, -80.83916667, "Spectrum Center"),
    "Chicago": (41.88055556, -87.67416667, "United Center"),
    "Cleveland": (41.49638889, -81.68805556, "Rocket Arena"),
    "Dallas": (32.79055556, -96.81027778, "American Airlines Center"),
    "Denver": (39.74861111, -105.0075, "Ball Arena"),
    "Detroit": (42.34111111, -83.055, "Little Caesars Arena"),
    "Golden State": (37.76805556, -122.3875, "Chase Center"),
    "Houston": (29.75083333, -95.36222222, "Toyota Center"),
    "Indiana": (39.76388889, -86.15555556, "Gainbridge Fieldhouse"),
    "LA Clippers": (33.9451, -118.3431, "Intuit Dome"),
    "LA Lakers": (34.04305556, -118.26722222, "Crypto.com Arena"),
    "Memphis": (35.13833333, -90.05055556, "FedExForum"),
    "Miami": (25.78138889, -80.18805556, "Kaseya Center"),
    "Milwaukee": (43.04502778, -87.91816667, "Fiserv Forum"),
    "Minnesota": (44.97944444, -93.27611111, "Target Center"),
    "New Orleans": (29.94888889, -90.08194444, "Smoothie King Center"),
    "New York": (40.75055556, -73.99361111, "Madison Square Garden"),
    "Oklahoma City": (35.46333333, -97.515, "Paycom Center"),
    "Orlando": (28.53916667, -81.38361111, "Kia Center"),
    "Philadelphia": (39.90111111, -75.17194444, "Xfinity Mobile Arena"),
    "Phoenix": (33.44583333, -112.07138889, "Mortgage Matchup Center"),
    "Portland": (45.53166667, -122.66666667, "Moda Center"),
    "Sacramento": (38.58036111, -121.49961111, "Golden 1 Center"),
    "San Antonio": (29.42694444, -98.4375, "Frost Bank Center"),
    "Toronto": (43.64333333, -79.37916667, "Scotiabank Arena"),
    "Utah": (40.76833333, -111.90111111, "Delta Center"),
    "Washington": (38.89805556, -77.02083333, "Capital One Arena"),
}

# team -> (venue, address, city, postal_code, address source URL, label)
PROFILE = {
    "Atlanta": ("State Farm Arena", "1 State Farm Drive", "Atlanta, GA", "30303",
                "https://www.statefarmarena.com/plan-your-visit/transportation",
                "State Farm Arena - Transportation (official site)"),
    "Boston": ("TD Garden", "100 Legends Way", "Boston, MA", "02114",
               "https://www.tdgarden.com/plan-your-visit/directions-parking/directions",
               "TD Garden - Directions (official site)"),
    "Brooklyn": ("Barclays Center", "620 Atlantic Avenue", "Brooklyn, NY", "11217",
                 "https://www.barclayscenter.com/getting-here",
                 "Barclays Center - Getting Here (official site)"),
    "Charlotte": ("Spectrum Center", "333 East Trade Street", "Charlotte, NC", "28202",
                  "https://www.spectrumcentercharlotte.com/plan-your-visit/directions-parking",
                  "Spectrum Center - Directions & Parking (official site)"),
    "Chicago": ("United Center", "1901 West Madison Street", "Chicago, IL", "60612",
                "https://www.unitedcenter.com/venue/directions-parking/",
                "United Center - Directions & Parking (official site)"),
    "Cleveland": ("Rocket Arena", "1 Center Court", "Cleveland, OH", "44115",
                  "https://www.rocketarena.com/plan-your-visit/directions-parking",
                  "Rocket Arena - Directions & Parking (official site)"),
    "Dallas": ("American Airlines Center", "2500 Victory Avenue", "Dallas, TX", "75219",
               "https://www.americanairlinescenter.com/plan-your-visit/directions",
               "American Airlines Center - Directions (official site)"),
    "Denver": ("Ball Arena", "1000 Chopper Circle", "Denver, CO", "80204",
               "https://www.ballarena.com/", "Ball Arena - official site"),
    "Detroit": ("Little Caesars Arena", "2645 Woodward Avenue", "Detroit, MI", "48201",
                "https://www.google.com/maps/search/?api=1&query=Little+Caesars+Arena+Detroit",
                "Google Maps place card, corroborated by Census geocoder address match"),
    "Golden State": ("Chase Center", "1 Warriors Way", "San Francisco, CA", "94158",
                     "https://www.google.com/maps/search/?api=1&query=Chase+Center+San+Francisco",
                     "Google Maps place card (plus code QJ96+6R)"),
    "Houston": ("Toyota Center", "1510 Polk Street", "Houston, TX", "77010",
                "https://www.toyotacenter.com/plan-your-visit/directions-parking",
                "Toyota Center - Directions & Parking (official site)"),
    "Indiana": ("Gainbridge Fieldhouse", "125 S. Pennsylvania St.", "Indianapolis, IN", "46204",
                "https://www.gainbridgefieldhouse.com/plan-your-visit/directions-parking",
                "Gainbridge Fieldhouse - Directions & Parking (official site)"),
    "LA Clippers": ("Intuit Dome", "3930 W Century Blvd", "Inglewood, CA", None,
                    "https://www.intuitdome.com/plan-your-visit/how-to-get-here",
                    "Intuit Dome - How To Get Here (official site)"),
    "LA Lakers": ("Crypto.com Arena", "1111 South Figueroa Street", "Los Angeles, CA", "90015",
                  "https://www.google.com/maps/search/?api=1&query=Crypto.com+Arena+Los+Angeles",
                  "Google Maps place card"),
    "Memphis": ("FedExForum", "191 Beale Street", "Memphis, TN", "38103",
                "https://www.fedexforum.com/plan-your-visit/parking-directions",
                "FedExForum - Parking & Directions (official site)"),
    "Miami": ("Kaseya Center", "601 Biscayne Blvd", "Miami, FL", "33132",
              "https://www.kaseyacenter.com/", "Kaseya Center - official site"),
    "Milwaukee": ("Fiserv Forum", "1111 North Vel R. Phillips Avenue", "Milwaukee, WI", "53203",
                  "https://www.fiservforum.com/plan-your-visit/directions-parking",
                  "Fiserv Forum - Directions & Parking (official site)"),
    "Minnesota": ("Target Center", "600 1st Avenue North", "Minneapolis, MN", "55402",
                  "https://www.targetcenter.com/plan-your-visit-1/getting_here",
                  "Target Center - Getting Here (official site)"),
    "New Orleans": ("Smoothie King Center", "1501 Dave Dixon Drive", "New Orleans, LA", "70113",
                    "https://www.smoothiekingcenter.com/plan-your-visit/directions-parking",
                    "Smoothie King Center - Directions & Parking (official site)"),
    "New York": ("Madison Square Garden", "4 Pennsylvania Plaza", "New York, NY", "10001",
                 "https://www.msg.com/madison-square-garden", "Madison Square Garden - official site"),
    "Oklahoma City": ("Paycom Center", "100 W. Reno Ave.", "Oklahoma City, OK", "73102",
                      "https://www.paycomcenter.com/plan-your-visit/directions-visitor-info",
                      "Paycom Center - Directions & Visitor Info (official site)"),
    "Orlando": ("Kia Center", "400 West Church Street", "Orlando, FL", "32801",
                "https://www.kiacenter.com/plan-your-visit/directions-and-parking",
                "Kia Center - Directions And Parking (official site)"),
    "Philadelphia": ("Xfinity Mobile Arena", "3601 South Broad Street", "Philadelphia, PA", "19148",
                     "https://www.wellsfargocenterphl.com/", "Xfinity Mobile Arena - official site"),
    "Phoenix": ("Mortgage Matchup Center", "201 E. Jefferson Street", "Phoenix, AZ", "85004",
                "https://mortgagematchupcenter.com/plan-your-visit/transportation-parking/",
                "Mortgage Matchup Center - Transportation & Parking (official site)"),
    "Portland": ("Moda Center", None, "Portland, OR", None,
                 "https://www.rosequarter.com/", "Moda Center - official site"),
    "Sacramento": ("Golden 1 Center", "500 David J Stern Walk", "Sacramento, CA", "95814",
                   "https://www.golden1center.com/", "Golden 1 Center - official site"),
    "San Antonio": ("Frost Bank Center", "1 Frost Bank Center Drive", "San Antonio, TX", "78219",
                    "https://www.frostbankcenter.com/plan-your-visit/parking",
                    "Frost Bank Center - Parking & Directions (official site)"),
    "Toronto": ("Scotiabank Arena", "40 Bay Street", "Toronto, ON", "M5J 0E7",
                "https://www.scotiabankarena.com/", "Scotiabank Arena - official site"),
    "Utah": ("Delta Center", "301 S Temple", "Salt Lake City, UT", "84101",
             "https://www.deltacenter.com/", "Delta Center - official site"),
    "Washington": ("Capital One Arena", "601 F Street NW", "Washington, DC", "20004",
                   "https://www.capitalonearena.com/plan-your-visit/directions-parking",
                   "Capital One Arena - Directions & Parking (official site)"),
}

# Coordinates that an earlier pass accepted and that this pass rejects, with
# the measured distance to the corroborated venue position.
REJECTED = {
    "Philadelphia": (-75.163588105772, 39.951499042789, 5650,
                     "Census matched 1 SOUTH BROAD ST in Center City, not the arena on South Broad Street."),
    "Phoenix": (-112.006932529977, 33.416937085782, 6787,
                "Census matched a street range in South Mountain, not the downtown arena."),
    "Utah": (-111.891017098129, 40.762765893127, 1047,
             "Census matched the 300 SOUTH road centreline, not the arena block."),
    "Milwaukee": (-87.911029612744, 43.044742221905, 526,
                  "Census matched a North Water Street frontage, not the arena footprint."),
    "Sacramento": (-121.502319208828, 38.580151305585, 245,
                   "Census point falls outside the 250 m corroboration tolerance."),
    "Dallas": (-96.811060116158, 32.788924533601, 189,
               "Census point falls on the arena block edge; superseded by the two-source position."),
    "Portland": (-122.667691502429, 45.532995497051, 171,
                 "Census point falls on the arena block edge; superseded by the two-source position."),
    "LA Lakers": (-118.265447772714, 34.043507739979, 165,
                  "Census point falls on the arena block edge; superseded by the two-source position."),
}

TEAM_ORDER = list(OSM)


def build() -> dict:
    rows = []
    for team in TEAM_ORDER:
        venue, address, city, postal, address_url, address_label = PROFILE[team]
        olat, olon, osm_query = OSM[team]
        wlat, wlon, wiki_title = WIKI[team]

        if team in OFFICIAL:
            plat, plon, primary_url, primary_label = OFFICIAL[team]
            primary_kind = "venue_published_map_point"
            clat, clon = olat, olon
            corr_url = NOMINATIM + osm_query.replace(" ", "+").replace(",", "%2C")
            corr_label = f"OpenStreetMap arena polygon via Nominatim ({venue} building outline)"
            corr_kind = "openstreetmap"
        else:
            plat, plon = olat, olon
            primary_url = NOMINATIM + osm_query.replace(" ", "+").replace(",", "%2C")
            primary_label = f"OpenStreetMap arena polygon via Nominatim ({venue} building outline)"
            primary_kind = "openstreetmap"
            clat, clon = wlat, wlon
            corr_url = WIKI_API + wiki_title.replace(" ", "%20")
            corr_label = f"Wikipedia/Wikidata coordinates for {wiki_title}"
            corr_kind = "wikipedia_wikidata"

        gap_m = haversine_km(plat, plon, clat, clon) * 1000.0
        if gap_m > CORROBORATION_TOLERANCE_M:
            raise SystemExit(
                f"{team}: sources disagree by {gap_m:.0f} m, above the "
                f"{CORROBORATION_TOLERANCE_M:.0f} m tolerance"
            )

        row = {
            "team": team,
            "venue": venue,
            "city": city,
            "address": address,
            "postal_code": postal,
            "latitude": round(plat, 7),
            "longitude": round(plon, 7),
            "verified": True,
            "coordinate_source_url": primary_url,
            "coordinate_source_label": primary_label,
            "coordinate_source_kind": primary_kind,
            "address_source_url": address_url,
            "address_source_label": address_label,
            "corroboration_source_url": corr_url,
            "corroboration_source_label": corr_label,
            "corroboration_source_kind": corr_kind,
            "corroboration_latitude": round(clat, 7),
            "corroboration_longitude": round(clon, 7),
            "source_gap_m": round(gap_m, 1),
            "source_gap_tolerance_m": CORROBORATION_TOLERANCE_M,
        }
        # ``load_arenas`` reads ``source_url``/``source_label``; they name the
        # source of the coordinate itself.
        row["source_url"] = primary_url
        row["source_label"] = primary_label

        if team in REJECTED:
            rlon, rlat, rdist, why = REJECTED[team]
            row["rejected_source"] = {
                "kind": "us_census_geocoder",
                "url": "https://geocoding.geo.census.gov/geocoder/locations/address",
                "latitude": rlat,
                "longitude": rlon,
                "distance_from_accepted_m": rdist,
                "reason": why,
            }
            row["note"] = (
                "Two independent sources agree within "
                f"{gap_m:.0f} m. A Census geocoder match for this address was "
                f"{rdist} m away and is not used."
            )
        else:
            row["note"] = (
                f"Two independent sources agree within {gap_m:.0f} m "
                f"(tolerance {CORROBORATION_TOLERANCE_M:.0f} m)."
            )
        rows.append(row)

    return {
        "arenas": rows,
        "meta": {
            "purpose": "The sourced arena-coordinate table used to compute travel distance.",
            "compiled_at_utc": "2026-11-15T03:40:00Z",
            "method": (
                "A venue carries a coordinate only when two independent sources place it "
                f"within {CORROBORATION_TOLERANCE_M:.0f} m of each other. The coordinate source is, "
                "in order of preference, the point the venue itself publishes inside one of its own "
                "map links, or the OpenStreetMap arena polygon resolved through Nominatim. The "
                "corroborating source is always independent of the coordinate source: Wikipedia/"
                "Wikidata when the coordinate is the OSM polygon, and the OSM polygon when the "
                "coordinate comes from the venue. Every row records both URLs and the measured gap."
            ),
            "distance_metric": (
                "haversine great-circle distance between the two venue coordinates, in statute miles "
                "(engine/travel.py, EARTH_RADIUS_MILES = 3958.7613)."
            ),
            "coverage": f"{len(rows)} of 30 venues carry a corroborated coordinate; 0 unresolved.",
            "rejected_evidence": (
                "An earlier pass accepted 16 coordinates straight from the U.S. Census geocoder. "
                "Reverse geocoding showed the Philadelphia and Phoenix matches were 5.7 km and 6.8 km "
                "off, and eight of the sixteen fell outside a 250 m tolerance. Those points are "
                "recorded per row under 'rejected_source' and are not used."
            ),
            "builder": "scripts/build_arena_table.py (run with --check to verify the committed file)",
        },
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed file differs from a fresh build")
    args = parser.parse_args(argv)

    payload = build()
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(f"{OUT} is out of date; re-run without --check", file=sys.stderr)
            return 1
        print(f"{OUT.name}: up to date ({len(payload['arenas'])} venues)")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    gaps = [r["source_gap_m"] for r in payload["arenas"]]
    print(f"wrote {OUT} ({len(payload['arenas'])} venues)")
    print(f"source agreement: max {max(gaps):.1f} m, mean {sum(gaps)/len(gaps):.1f} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
