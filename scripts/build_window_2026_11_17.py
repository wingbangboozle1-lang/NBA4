#!/usr/bin/env python3
"""Generate the 2026-11-17 rolling-window snapshot files from verbatim raw extracts.

Task BM (session ``arena/4326c586-nba4``, tenth daily refresh cycle). Inputs are
the two verbatim extractions committed under ``data/snapshots/raw/``:

* ``injury-2026-11-17T1030am-et.pipes`` - the 11/17/26 10:30 AM ET injury report,
  seven pipe-separated cells per row exactly as the PDF text printed them;
* ``schedule-2026-11-17-window-rows-253-273.txt`` - official schedule rows 253-273.

Outputs (never hand-edited; re-run this script instead):

* ``data/snapshots/slate-2026-11-17.json`` - the 21 games tipping 11/17-11/19;
* ``data/snapshots/injuries-2026-11-17-1030am.json`` - the 10:30 AM rows in the
  site's injury-table schema, with every lost or inferred cell flagged.

Rules (carried from ``data/snapshots/README.md``):

* a blank cell stays blank in the row; the document's own cells are never replaced;
* a blank game date or tip time may be filled from the official schedule row whose
  AWAY@HOME code matches, and the row then cites both documents (``schedule_assisted``);
* a row whose matchup cell is lost is attached to a game only by its printed block
  position and is flagged ``matchup_by_position``;
* a row with no team and no matchup is kept unattributed, never attached;
* a printed tip time that disagrees with the schedule's ET tip is kept as printed
  and flagged ``tip_disagreement`` (both values are published);
* ``NOT YET SUBMITTED`` is a reporting state, not a player status.

Run: ``python3 scripts/build_window_2026_11_17.py`` (stdlib only).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
RAW = SNAP / "raw"

PIPES = RAW / "injury-2026-11-17T1030am-et.pipes"
SCHEDULE_RAW = RAW / "schedule-2026-11-17-window-rows-253-273.txt"
SLATE_OUT = SNAP / "slate-2026-11-17.json"
INJ_OUT = SNAP / "injuries-2026-11-17-1030am.json"

SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf"

WINDOW_DATES = ("11/17/2026", "11/18/2026", "11/19/2026")

TEAM_ABBR = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL",
    "LA Lakers": "LAL", "Memphis Grizzlies": "MEM", "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX", "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}
NOT_YET = "NOT YET SUBMITTED"

# The schedule PDF prints city names (and "LA Clippers"/"LA Lakers"), not nicknames.
SCHEDULE_NAME = {
    "Atlanta": "Atlanta Hawks", "Boston": "Boston Celtics", "Brooklyn": "Brooklyn Nets",
    "Charlotte": "Charlotte Hornets", "Chicago": "Chicago Bulls", "Cleveland": "Cleveland Cavaliers",
    "Dallas": "Dallas Mavericks", "Denver": "Denver Nuggets", "Detroit": "Detroit Pistons",
    "Golden State": "Golden State Warriors", "Houston": "Houston Rockets", "Indiana": "Indiana Pacers",
    "LA Clippers": "LA Clippers", "LA Lakers": "Los Angeles Lakers", "Memphis": "Memphis Grizzlies",
    "Miami": "Miami Heat", "Milwaukee": "Milwaukee Bucks", "Minnesota": "Minnesota Timberwolves",
    "New Orleans": "New Orleans Pelicans", "New York": "New York Knicks",
    "Oklahoma City": "Oklahoma City Thunder", "Orlando": "Orlando Magic", "Philadelphia": "Philadelphia 76ers",
    "Phoenix": "Phoenix Suns", "Portland": "Portland Trail Blazers", "Sacramento": "Sacramento Kings",
    "San Antonio": "San Antonio Spurs", "Toronto": "Toronto Raptors", "Utah": "Utah Jazz",
    "Washington": "Washington Wizards",
}


def schedule_rows() -> list[dict]:
    """Parse the verbatim schedule rows. Printed order: TEAM 1 then TEAM 2; the token
    'at' in the TEAM 2 column means TEAM 1 is away (the printed order is kept otherwise)."""
    out = []
    for line in SCHEDULE_RAW.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        c = line.split("|")
        row, day, date, t1, t2, local, et = c[0], c[1], c[2], c[3], c[4], c[5], c[6]
        if t2 == "at":
            away, home = t1, c[5]
            basis = "printed 'at' token"
            tip_local, tip_et = c[6], c[7]
        else:
            away, home = t1, t2
            basis = "printed order (first cell = away); corroborated below by the injury-report code where one exists"
            tip_local, tip_et = local, et
        mm, dd, yy = date.split("/")
        out.append({
            "row": int(row), "date": f"20{yy}-{mm}-{dd}", "weekday": day,
            "date_printed": date, "away": away, "home": home,
            "tip_et_col1": tip_local, "tip_et_col2": tip_et, "basis": basis,
            "code": f"{TEAM_ABBR[SCHEDULE_NAME[away]]}@{TEAM_ABBR[SCHEDULE_NAME[home]]}",
        })
    return out


def et_24h(printed: str) -> str | None:
    """'10:30 (ET)' or '7:30 PM' -> 'HH:MM' 24h. The report prints evening times
    without AM/PM; every game in this window tips in the evening, so hours below 12
    are read as PM. Returns None when the cell is blank."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*(AM|PM)?", printed)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == "PM" and h < 12:
        h += 12
    elif ap is None and h < 12:
        h += 12
    return f"{h:02d}:{mi:02d}"


def sched_et_24h(text: str) -> str:
    return et_24h(text) or ""


def parse_pipes() -> list[dict]:
    rows = []
    for line in PIPES.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "|" not in line or line.startswith("fields:"):
            continue
        cells = line.split("|")
        if len(cells) != 7:
            raise SystemExit(f"refusing: row does not carry seven cells: {line!r}")
        rows.append({"date": cells[0], "time": cells[1], "matchup": cells[2],
                     "team": cells[3], "player": cells[4], "status": cells[5], "reason": cells[6]})
    return rows


def main() -> int:
    sched = schedule_rows()
    by_code = {}
    for g in sched:
        by_code.setdefault(g["code"], []).append(g)
    for code, gs in by_code.items():
        if len(gs) > 1:
            raise SystemExit(f"refusing: schedule code {code} repeats inside the window")

    rows = parse_pipes()
    # Which games does the report print? Group in printed order.
    games: dict[str, dict] = {}
    order: list[str] = []
    current_code = None
    unattributed: list[dict] = []
    for r in rows:
        if r["matchup"]:
            current_code = r["matchup"]
            code, by_pos = r["matchup"], False
        elif current_code and r["team"]:
            # Matchup lost at a page break: attach by printed block position only when the
            # team plays in the block's game (checked against the schedule, not inferred).
            code, by_pos = current_code, True
            if TEAM_ABBR.get(r["team"]) not in code.split("@"):
                unattributed.append({**r, "reason_unattributed": "team not in the block's matchup"})
                continue
        else:
            unattributed.append({**r, "reason_unattributed": "team and matchup cells both lost"})
            continue
        if code not in games:
            games[code] = {"matchup": code, "game_date": "", "tip_et_from_report": "",
                           "rows": []}
            order.append(code)
        g = games[code]
        if r["date"] and not g["game_date"]:
            mo, d, y = r["date"].split("/")
            g["game_date"] = f"{y}-{mo}-{d}"
        if r["time"] and not g["tip_et_from_report"]:
            g["tip_et_from_report"] = r["time"]
        row = {"team": r["team"], "player": r["player"], "status": r["status"], "reason": r["reason"]}
        flags = []
        if by_pos:
            flags.append("matchup_by_position")
        if not r["date"]:
            flags.append("date_cell_lost")
        if not r["time"]:
            flags.append("time_cell_lost")
        if not r["team"]:
            flags.append("team_cell_lost")
        if r["status"] == "" and r["player"]:
            flags.append("status_cell_lost")
        row["flags"] = flags
        row["unverified"] = bool(flags)
        g["rows"].append(row)

    # Schedule corroboration for every printed game code.
    out_games = []
    for code in order:
        g = games[code]
        if code not in by_code:
            g["schedule_row"] = None
            g["tip_et_from_schedule"] = ""
            g["tip_disagreement"] = "matchup not in the 11/17-11/19 schedule window"
        else:
            s = by_code[code][0]
            g["schedule_row"] = s["row"]
            g["tip_et_from_schedule"] = s["tip_et_col2"]
            if not g["game_date"]:
                g["game_date"] = s["date"]
                g["date_source"] = "schedule-assisted (schedule row %d)" % s["row"]
            else:
                g["date_source"] = "printed"
            printed = et_24h(g["tip_et_from_report"]) if g["tip_et_from_report"] else None
            sched_tip = et_24h(s["tip_et_col2"])
            if printed is None:
                g["tip_disagreement"] = None
                g["tip_note"] = ("report time cell lost at a page break; the official schedule prints "
                                 f"{s['tip_et_col2']} ET for row {s['row']}; no conflict is asserted")
            elif printed != sched_tip:
                g["tip_disagreement"] = (f"report prints {g['tip_et_from_report']} but the official "
                                         f"schedule row {s['row']} prints {s['tip_et_col2']} ET; both kept as printed")
            else:
                g["tip_disagreement"] = None
        g["cells_source"] = "report"
        out_games.append(g)

    slate_games = []
    for s in sched:
        if s["date"] not in ("2026-11-17", "2026-11-18", "2026-11-19"):
            raise SystemExit("refusing: window row outside 11/17-11/19")
        inj_game = games.get(s["code"])
        code_printed = bool(inj_game)
        disagree = None
        if inj_game and inj_game.get("tip_disagreement"):
            disagree = inj_game["tip_disagreement"]
        slate_games.append({
            "row": s["row"], "date": s["date"], "weekday": s["weekday"],
            "away": s["away"], "home": s["home"],
            "tip_et_col1": s["tip_et_col1"], "tip_et_col2": s["tip_et_col2"],
            "code": s["code"],
            "code_source": "injury report 11/17 10:30 AM" if code_printed else "schedule PDF only (report prints no code for this game)",
            "games_page_slug": None,
            "games_page_game_id": None,
            "games_page_tip_et": None,
            "games_page_url": None,
            "games_page_note": "games-page corroboration was not re-fetched in this cycle (BM); no value recorded",
            "order_corroborated_by": [
                "schedule PDF printed order (first cell = away, per the injury-report code where one exists)"
            ] + (["injury report matchup code AWAY@HOME (11/17 10:30 AM report)"] if code_printed else []),
            "tip_disagreement": disagree,
            "basis": s["basis"],
            "at_token_printed": s["basis"].startswith("printed 'at'"),
        })
    slate = {
        "snapshot_id": "slate-2026-11-17",
        "kind": "official_schedule_rows",
        "source_url": SCHEDULE_URL,
        "source_document": "2026-27 NBA Regular Season Schedule By Date",
        "source_document_header": "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE",
        "source_rows": "253-273",
        "window": {"dates": list(WINDOW_DATES), "first_row": 253, "last_row": 273, "games": len(slate_games)},
        "fetched_at_utc": "2026-11-17T15:44:00Z",
        "extraction_tool": "fetch_page (PDF text extraction, chunk 3 of 13); transcribed to raw/schedule-2026-11-17-window-rows-253-273.txt",
        "corroborating_urls": {"injury_index": INDEX_URL, "injury_report_pdf": REPORT_URL},
        "games": slate_games,
        "extraction_notes": [
            "Rows 253-273 are the games whose date is 11/17, 11/18 or 11/19 in the schedule PDF; the schedule prints no broadcast or tip change for them other than the cells shown.",
            "Games-page corroboration (nba.com/game pages) was NOT re-fetched in this cycle; the games_page_* fields are null by design, not missing data.",
            "Tip disagreements between the 10:30 AM report and the schedule are kept as printed (see tip_disagreement).",
        ],
    }
    injuries = {
        "snapshot_id": "injuries-2026-11-17-1030am",
        "kind": "official_injury_report_rows",
        "source_url": REPORT_URL,
        "source_document": "Injury Report: 11/17/26 10:30 AM",
        "source_document_header": "Injury Report: 11/17/26 10:30 AM",
        "source_index_url": INDEX_URL,
        "secondary_source_url": SCHEDULE_URL,
        "revision_et_label": "11/17/26 10:30 AM",
        "revision_utc": "2026-11-17T15:30:00Z",
        "fetched_at_utc": "2026-11-17T15:44:00Z",
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables, single chunk); transcribed to raw/injury-2026-11-17T1030am-et.pipes",
        "row_count": sum(len(g["rows"]) for g in out_games),
        "unattributed_row_count": len(unattributed),
        "games": out_games,
        "unattributed_rows": unattributed,
        "extraction_notes": [
            "Verbatim extraction of the report named in source_url. Blank cells stay blank; nothing is filled from memory or another report.",
            "Rows flagged matchup_by_position are attached to a game only by their printed block position and carry unverified=true.",
            "Rows in unattributed_rows print a status or player but neither a team nor a matchup cell; they are published unattributed.",
            "Game-date cells lost at page breaks are filled from the official schedule (date_source says so); the row then cites both documents.",
            "Tip disagreements are kept as printed and flagged in tip_disagreement; neither value is chosen.",
            "NOT YET SUBMITTED is a reporting state, not a status.",
        ],
        "superseded_snapshot": "injuries-2026-11-16-1000am.json (the 11/16 10:00 AM report; superseded by this file, not deleted)",
        "index_listing_checked": "Index read at about 15:42Z on 2026-11-17 (10:42 a.m. ET): the 11/17 entries listed run from 12:00 a.m. through 10:30 a.m. ET; the 10:30 a.m. ET report is the newest listed at that time.",
    }
    SLATE_OUT.write_text(json.dumps(slate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    INJ_OUT.write_text(json.dumps(injuries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n_rows = sum(len(g["rows"]) for g in out_games)
    print(f"wrote {SLATE_OUT.name}: {len(slate_games)} games; wrote {INJ_OUT.name}: {len(out_games)} games, "
          f"{n_rows} rows, {len(unattributed)} unattributed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
