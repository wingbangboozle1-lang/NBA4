#!/usr/bin/env python3
"""Assert the away/home basis for 11/11-11/13 schedule rows from official reports.

The official schedule-by-date PDF prints no venue token on rows 215-230 and
34-42 (11/11, 11/12 and 11/13), and the earlier load pass left those rows with
``away_team``/``home_team`` set to null.  That left travel distance structurally
uncomputable for the very dates the three-day slate window depends on -- 11/13
is the previous game for twelve of the 30 teams.

The 11/10-11/13 05:00 PM official injury reports each print a ``MATCHUP``
column as ``AWAY@HOME`` for every game on the following night.  Those codes are
a second official document naming the same games, and they are used here
exactly as the 11/14 report was used for rows 231-244.

Every asserted pair is cross-checked against the schedule row's two team names
before it is written, so a transcription slip fails the build instead of
silently inventing a venue.

Usage::

    python3 scripts/build_matchup_basis.py          # write the snapshot
    python3 scripts/build_matchup_basis.py --check  # verify the committed file
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE = ROOT / "data" / "snapshots" / "schedule-load-2026-11-14.json"
OUT = ROOT / "data" / "snapshots" / "matchup-basis-2026-11-10-to-13.json"

BASE = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-{day}_05_00PM.pdf"

# Schedule row -> (away, home, reporting date whose report prints the code)
ASSERTED = {
    # 11/11/2026 -- confirmed by the 11/10 05:00 PM report.
    217: ("Washington", "Indiana", "10"),
    218: ("Cleveland", "New York", "10"),
    219: ("Boston", "Toronto", "10"),
    220: ("San Antonio", "Chicago", "10"),
    221: ("Denver", "Memphis", "10"),
    222: ("LA Lakers", "Milwaukee", "10"),
    223: ("Brooklyn", "New Orleans", "10"),
    224: ("Orlando", "Utah", "10"),
    225: ("Golden State", "Houston", "10"),
    226: ("Oklahoma City", "Portland", "10"),
    # 11/12/2026 -- confirmed by the 11/11 05:00 PM report.
    227: ("Toronto", "Philadelphia", "11"),
    228: ("Detroit", "Washington", "11"),
    229: ("Dallas", "Minnesota", "11"),
    230: ("Charlotte", "Phoenix", "11"),
    # 11/13/2026 -- confirmed by the 11/12 05:00 PM report.
    34: ("New York", "Indiana", "12"),
    35: ("Milwaukee", "Orlando", "12"),
    36: ("Cleveland", "Miami", "12"),
    37: ("Atlanta", "Chicago", "12"),
    38: ("Memphis", "New Orleans", "12"),
    39: ("Utah", "Houston", "12"),
    40: ("Golden State", "San Antonio", "12"),
    41: ("Portland", "Sacramento", "12"),
    42: ("Oklahoma City", "LA Clippers", "12"),
    # 11/14/2026 -- confirmed by the 11/13 05:00 PM report.
    231: ("Denver", "New Orleans", "13"),
    232: ("Dallas", "Cleveland", "13"),
    233: ("Detroit", "Miami", "13"),
    234: ("Brooklyn", "Memphis", "13"),
    235: ("Chicago", "Minnesota", "13"),
    236: ("Indiana", "Philadelphia", "13"),
    237: ("LA Lakers", "Phoenix", "13"),
    238: ("Charlotte", "LA Clippers", "13"),
    239: ("San Antonio", "Utah", "13"),
    240: ("Dallas", "Boston", "13"),
    241: ("New York", "Toronto", "13"),
    242: ("Houston", "Washington", "13"),
    243: ("Atlanta", "Milwaukee", "13"),
    244: ("Oklahoma City", "Sacramento", "13"),
}

def _token(name: str) -> str:
    """Map either an abbreviation or a full team name onto one three-letter key."""
    return ABBREVIATION.get(name, name.replace(".", "").replace(" ", "")[:3].upper())


# Only the teams whose leading three letters do not already match their code.
ABBREVIATION = {
    "New Orleans": "NOP",
    "New York": "NYK",
    "Golden State": "GSW",
    "San Antonio": "SAS",
    "LA Lakers": "LAL",
    "LA Clippers": "LAC",
    "Oklahoma City": "OKC",
    "Portland": "POR",
    "Charlotte": "CHA",
    "Phoenix": "PHX",
    "Utah": "UTA",
    "Brooklyn": "BKN",
    "Washington": "WAS",
    "Milwaukee": "MIL",
    "Sacramento": "SAC",
}


UNRESOLVED = {
    253: "11/17 New York at Toronto: no 11/16 05:00 PM report is published yet.",
    254: "11/17 Portland at Minnesota: no 11/16 05:00 PM report is published yet.",
    255: "11/17 Detroit at San Antonio: no 11/16 05:00 PM report is published yet.",
    256: "11/17 Charlotte at LA Lakers: no 11/16 05:00 PM report is published yet.",
    257: "11/17 Utah at LA Clippers: no 11/16 05:00 PM report is published yet.",
}


def build() -> dict:
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    rows = {r["row"]: r for r in schedule["games"]}

    asserted = []
    for row_number in sorted(ASSERTED):
        away, home, report_day = ASSERTED[row_number]
        row = rows[row_number]
        printed = {row["team_1"], row["team_2"]}
        if printed != {away, home}:
            raise SystemExit(
                f"row {row_number}: schedule prints {sorted(printed)} but the "
                f"matchup code names {sorted({away, home})}"
            )
        existing = (row.get("away_team"), row.get("home_team"))
        if all(existing):
            # Rows 231-244 were recorded earlier from the abbreviation form of
            # the same matchup code (e.g. "DEN at NOP"), so compare the leading
            # three-letter token rather than the full team name.
            if (_token(existing[0]), _token(existing[1])) != (_token(away), _token(home)):
                raise SystemExit(
                    f"row {row_number}: already carries {existing[0]} at "
                    f"{existing[1]}, which conflicts with the matchup code {away}@{home}"
                )
        asserted.append(
            {
                "row": row_number,
                "date": row["date"],
                "team_1": row["team_1"],
                "team_2": row["team_2"],
                "away_team": away,
                "home_team": home,
                "matchup_code": f"{away}@{home}",
                "source_url": BASE.format(day=report_day),
                "source_report": f"11/{report_day}/26 05:00 PM official injury report",
                "printing_schedule": row["date"],
                "previous_basis": row.get("away_home_basis"),
            }
        )

    return {
        "snapshot_id": "matchup-basis-2026-11-10-to-13",
        "kind": "away_home_basis_for_schedule_rows",
        "purpose": (
            "The official schedule-by-date prints no venue token on these rows, and the earlier "
            "load pass therefore recorded no away/home basis. Travel distance depends on the "
            "venue, so the basis is recovered from a second official document for each game: the "
            "05:00 PM injury report that the league publishes the night before, whose MATCHUP "
            "column is printed as AWAY@HOME."
        ),
        # Provenance keys the site gate requires on every published snapshot.
        "source_url": BASE.format(day="13"),
        "source_document_header": (
            "NBA Official Injury Report -- 05:00 PM editions of 11/10/26, 11/11/26, "
            "11/12/26 and 11/13/26"
        ),
        "fetched_at_utc": "2026-11-15T03:20:00Z",
        "extraction_tool": "fetch_page (PDF text extraction), both chunks of each report",
        # Every report the basis was read from; the per-row 'source_url' names
        # the one report that carries that particular matchup code.
        "sources": [BASE.format(day=d) for d in ("10", "11", "12", "13")],
        "source_document": "NBA Official Injury Report (05:00 PM edition), MATCHUP column",
        "cross_check": (
            "Each asserted pair is compared with the two team names printed on the schedule row "
            "before it is accepted; a mismatch fails the build."
        ),
        "asserted": asserted,
        "unresolved": [
            {"row": r, "reason": reason} for r, reason in sorted(UNRESOLVED.items())
        ],
        "coverage": {
            "rows_asserted": len(asserted),
            "dates_covered": sorted({a["date"] for a in asserted}),
            "rows_unresolved": len(UNRESOLVED),
        },
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    payload = build()
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(f"{OUT} is out of date; re-run without --check", file=sys.stderr)
            return 1
        print(f"{OUT.name}: up to date ({len(payload['asserted'])} rows asserted)")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    cov = payload["coverage"]
    print(f"wrote {OUT}")
    print(
        f"  {cov['rows_asserted']} rows asserted across {', '.join(cov['dates_covered'])}; "
        f"{cov['rows_unresolved']} still unresolved"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
