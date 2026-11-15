#!/usr/bin/env python3
"""Compute rest, back-to-back, 3-in-4 and travel for the 11/14 slate window.

Inputs, all committed and all sourced:

  * ``data/snapshots/schedule-load-2026-11-14.json`` -- rows 211-259 of the
    official 2026-27 schedule-by-date PDF (11/10/2026 - 11/18/2026), which
    supplies the look-back window needed for rest and the look-forward window
    needed for 3-in-4.
  * ``data/snapshots/matchup-basis-2026-11-10-to-13.json`` -- the away/home
    basis recovered from the 05:00 PM injury reports of 11/10-11/13, whose
    MATCHUP column prints ``AWAY@HOME`` for the following night's games.
  * ``data/arenas/arenas.json`` -- the sourced, two-source-corroborated venue
    coordinate table.

The away/home basis is only asserted where the schedule PDF prints an "at"
token or where an official injury report prints a matchup code for the same
game.  Every other row keeps its date-derived fields and leaves travel blank,
because travel needs the venue and the venue needs the basis.  This script
does not infer the basis from the printed order.

Usage::

    python3 scripts/build_load_snapshot.py          # write the snapshot
    python3 scripts/build_load_snapshot.py --check  # verify the committed file
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.travel import compute_load, load_arenas  # noqa: E402

SCHEDULE = ROOT / "data" / "snapshots" / "schedule-load-2026-11-14.json"
BASIS = ROOT / "data" / "snapshots" / "matchup-basis-2026-11-10-to-13.json"
ARENAS = ROOT / "data" / "arenas" / "arenas.json"
OUT = ROOT / "data" / "snapshots" / "load-2026-11-14.json"

SLATE_DATE = "2026-11-14"
"""The slate day whose games the three-day window covers."""

EASTERN = timezone(timedelta(hours=-5))
"""November is EST, so tip times printed in ET are UTC-5."""


class ScheduleRow:
    """One row of the official schedule-by-date, in the engine's game shape.

    ``home_team``/``away_team`` stay ``None`` when the document does not
    assert the basis.  ``teams`` carries both names regardless, which lets the
    loader compute date-derived fields for those rows.
    """

    def __init__(self, row: dict):
        self.row = row["row"]
        self.game_id = f"nba-2026-11-{row['date'][3:5]}-r{row['row']}"
        self.home_team = row.get("home_team")
        self.away_team = row.get("away_team")
        self.basis = row.get("away_home_basis", "")
        teams = [t for t in (row.get("team_1"), row.get("team_2")) if t]
        self.teams = tuple(teams)
        self.tip_time = self._tip(row)

    @staticmethod
    def _tip(row: dict) -> str:
        month, day, year = (int(p) for p in row["date"].split("/"))
        clock, meridiem = row["tip_et"].split()
        hour, minute = (int(p) for p in clock.split(":"))
        if meridiem == "PM" and hour != 12:
            hour += 12
        elif meridiem == "AM" and hour == 12:
            hour = 0
        return datetime(2000 + year, month, day, hour, minute, tzinfo=EASTERN).isoformat()


def _apply_basis(schedule: dict) -> tuple[list[dict], list[dict]]:
    """Attach the recovered away/home basis to the schedule rows.

    Rows the schedule already fixes keep what they have; the recovered basis
    only fills rows the schedule left open.  Returns the merged rows and the
    list of rows still without a basis.
    """
    basis = json.loads(BASIS.read_text(encoding="utf-8"))
    recovered = {a["row"]: a for a in basis["asserted"]}

    merged = []
    still_open = []
    for row in schedule["games"]:
        row = dict(row)
        claim = recovered.get(row["row"])
        if claim and not (row.get("away_team") and row.get("home_team")):
            row["away_team"] = claim["away_team"]
            row["home_team"] = claim["home_team"]
            row["away_home_basis"] = "injury_report_matchup"
            row["matchup_basis_source_url"] = claim["source_url"]
        elif claim:
            row.setdefault("matchup_basis_source_url", claim["source_url"])
        if not (row.get("away_team") and row.get("home_team")):
            still_open.append(row)
        merged.append(row)
    return merged, still_open


def build() -> dict:
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    arenas = load_arenas(ARENAS)
    merged, still_open = _apply_basis(schedule)
    rows = [ScheduleRow(r) for r in merged]
    load = compute_load(rows, arenas)

    out_rows = []
    for key in sorted(load, key=lambda k: (load[k].tip_time, load[k].team)):
        item = load[key]
        source = next(r for r in rows if r.game_id == item.game_id)
        out_rows.append(
            {
                "team": item.team,
                "game_id": item.game_id,
                "tip_time": item.tip_time,
                "opponent": next((t for t in source.teams if t != item.team), None),
                "venue_team": source.home_team,
                "venue_confirmed": item.venue_confirmed,
                "away_home_basis": source.basis,
                "rest_days": None if item.rest_days is None else round(item.rest_days, 4),
                "is_back_to_back": item.is_back_to_back,
                "is_three_in_four": item.is_three_in_four,
                "games_in_next_four_days": item.games_in_next_four_days,
                "previous_venue": item.previous_venue,
                "travel_miles": None if item.travel_miles is None else round(item.travel_miles, 1),
                "notes": list(item.notes),
            }
        )

    dated = [r for r in out_rows if r["rest_days"] is not None]
    travel = [r for r in out_rows if r["travel_miles"] is not None]
    unbased = [r for r in out_rows if not r["venue_confirmed"]]

    return {
        "snapshot_id": "load-2026-11-14",
        "kind": "rest_back_to_back_three_in_four_and_travel",
        "as_of_utc": "2026-11-14T23:59:00Z",
        "slate_date": SLATE_DATE,
        # Provenance keys the site gate requires on every published snapshot.
        "source_url": schedule["source_url"],
        "source_document_header": schedule["source_document_header"],
        "fetched_at_utc": schedule["fetched_at_utc"],
        "extraction_tool": (
            "python3 scripts/build_load_snapshot.py -- computed by engine.travel.compute_load "
            "from the official schedule rows and the sourced arena table"
        ),
        "source_schedule_snapshot": "data/snapshots/schedule-load-2026-11-14.json",
        "source_schedule_url": schedule["source_url"],
        "source_matchup_basis_snapshot": "data/snapshots/matchup-basis-2026-11-10-to-13.json",
        "source_matchup_basis_urls": json.loads(BASIS.read_text(encoding="utf-8"))["sources"],
        "source_arena_table": "data/arenas/arenas.json",
        "source_arena_table_as_of_utc": "2026-11-15T03:40:00Z",
        "method": {
            "rest_days": (
                "elapsed time between the tip of the team's previous game in the window and this "
                "one, in days; blank for a team's first game in the window"
            ),
            "is_back_to_back": "rest_days < 1.0",
            "games_in_next_four_days": (
                "games by the same team with tips in [this tip, this tip + 4 days]"
            ),
            "is_three_in_four": "games_in_next_four_days >= 3",
            "travel_miles": (
                "great-circle distance from the venue of the team's previous game to the venue of "
                "this one; blank when either venue is not asserted by the source"
            ),
            "away_home_basis": (
                "asserted only where the schedule PDF prints an 'at' token, or where an official "
                "05:00 PM injury report prints a matchup code (AWAY@HOME) for the same game. The "
                "printed order is never used to infer the basis."
            ),
        },
        "coverage": {
            "rows": len(out_rows),
            "teams": len({r["team"] for r in out_rows}),
            "rows_with_rest": len(dated),
            "rows_with_travel": len(travel),
            "rows_without_asserted_venue": len(unbased),
            "back_to_back_rows": sum(1 for r in out_rows if r["is_back_to_back"]),
            "three_in_four_rows": sum(1 for r in out_rows if r["is_three_in_four"]),
            "schedule_rows_without_basis": [
                {"row": r["row"], "date": r["date"],
                 "teams": [r["team_1"], r["team_2"]]}
                for r in still_open
            ],
            "travel_note": (
                "A row still has no travel value when the schedule row printed no venue, no official "
                "injury report had yet asserted one, or the team's previous game falls outside the "
                "look-back window. Those cases are named per row in 'notes'."
            ),
        },
        "load": out_rows,
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
        print(f"{OUT.name}: up to date ({len(payload['load'])} rows)")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    cov = payload["coverage"]
    print(f"wrote {OUT}")
    print(
        f"  {cov['rows']} team-game rows across {cov['teams']} teams; "
        f"{cov['rows_with_rest']} with rest, {cov['rows_with_travel']} with travel, "
        f"{cov['rows_without_asserted_venue']} without an asserted venue"
    )
    print(
        f"  {cov['back_to_back_rows']} back-to-back rows, "
        f"{cov['three_in_four_rows']} three-in-four rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
