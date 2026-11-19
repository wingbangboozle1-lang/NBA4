"""Task BR (session arena/639c095c-nba4): transcribe the 11/19 01:45 AM ET injury
report from its verbatim raw extraction into a dated snapshot.

Reads ONLY data/snapshots/raw/injury-2026-11-19T0145am-et.txt (printed lines).
Writes data/snapshots/injuries-2026-11-19-0145am.json and the newest pointer.
Blank printed cells stay blank. Nothing is inferred from memory or other reports.
Run: python3 scripts/_gen_2026_11_19_injury.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/snapshots/raw/injury-2026-11-19T0145am-et.txt"
OUT = ROOT / "data/snapshots/injuries-2026-11-19-0145am.json"
PTR = ROOT / "data/snapshots/injuries-newest-pointer-2026-11-19.json"
FETCHED = "2026-11-19T06:58:12Z"  # sandbox clock at the first shell call after the PDF fetch
MATCHUP = re.compile(r"^[A-Z]{2,4}@[A-Z]{2,4}$")
# Official 2026-27 schedule PDF (cdn.nba.com, header "AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE"),
# read by fetch_page chunks 1-2 in session BR. GAME number = printed "GAME" column; ET = printed "ET" column.
SCHED = {"GSW@MEM": (270, "2026-11-19", "8:00 PM"), "POR@MIL": (271, "2026-11-19", "8:00 PM"),
         "NYK@MIN": (272, "2026-11-19", "8:00 PM"), "LAC@SAS": (273, "2026-11-19", "8:00 PM"),
         "CHA@ATL": (43, "2026-11-20", "7:00 PM"), "ORL@BKN": (44, "2026-11-20", "7:30 PM"),
         "IND@CLE": (45, "2026-11-20", "7:30 PM"), "TOR@DET": (46, "2026-11-20", "7:30 PM"),
         "WAS@CHI": (47, "2026-11-20", "8:00 PM"), "NOP@OKC": (48, "2026-11-20", "8:00 PM"),
         "PHX@UTA": (49, "2026-11-20", "9:30 PM"), "HOU@DEN": (50, "2026-11-20", "10:00 PM"),
         "SAC@LAL": (51, "2026-11-20", "10:00 PM")}
SCHED_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
DOC_ORDER_FLAG = ("team and reporting-state cells printed on a page-break row with no matchup cell; "
                  "attached to the preceding game block by document order and not asserted to belong to it")
NO_STATUS_FLAG = ("page-break row printed with matchup and team only; the status and reason cells are not printed "
                  "and are left blank, not inferred")
ORPHAN_FLAG = ("orphan fragment on a continuation page: no date, time, matchup or team cell printed; "
               "kept as printed, not assigned to a game or a team, no reason inferred")

games = {}          # matchup -> dict
order = []
unattributed = []
current = None

def ensure(matchup):
    if matchup not in games:
        games[matchup] = {"matchup": matchup, "game_date": "", "game_date_printed": "", "time_printed": "",
                          "rows": []}
        order.append(matchup)
    return games[matchup]

for line in RAW.read_text(encoding="utf-8").splitlines():
    if not line.startswith("|") or line.startswith("| Game Date") or line.startswith("| ---"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 7:
        date, time, matchup, team, player, status, reason = cells
        flag, unv = "", False
        if matchup:
            current = matchup
            g = ensure(matchup)
            if date:
                mm, dd, yy = date.split("/")
                g["game_date_printed"], g["game_date"] = date, f"{yy}-{mm}-{dd}"
            if time:
                g["time_printed"] = time
        else:
            flag, unv = DOC_ORDER_FLAG, True
            if not team:
                unattributed.append({"team": "", "player": player, "status": status, "reason": reason,
                                     "unverified": True, "flag": ORPHAN_FLAG})
                continue
        target = ensure(current) if current else None
        target["rows"].append({"team": team, "player": player, "status": status, "reason": reason,
                               "unverified": unv, "flag": flag})
    elif len(cells) == 3 and MATCHUP.match(cells[1]):
        time, matchup, team = cells
        current = matchup
        g = ensure(matchup)
        if time:
            g["time_printed"] = time
        g["rows"].append({"team": team, "player": "", "status": "", "reason": "",
                          "unverified": True, "flag": NO_STATUS_FLAG})
    elif len(cells) == 3 and not cells[0]:
        _, team, reason = cells
        if not current:
            raise SystemExit("row before any matchup: " + line)
        games[current]["rows"].append({"team": team, "player": "", "status": "", "reason": reason,
                                       "unverified": True, "flag": DOC_ORDER_FLAG})
    else:
        raise SystemExit("unexpected printed line: " + line)


def clock_minutes(text):
    """Minutes after midnight. The report prints times such as '08:00 (ET)' with no AM/PM; every printed
    tip in this report is an evening tip (07:00-10:00), so an hour below 12 is read as PM. The reading is
    recorded in extraction_notes and is only used for the agreement check."""
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", text.replace(" (ET)", "").strip(), re.I)
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h < 12:
        h += 12
    elif ap == "" and h < 12:
        h += 12
    elif ap == "AM" and h == 12:
        h = 0
    return h * 60 + mi

# Schedule-context fill: only where the report prints no date or no time, and only from the official schedule.
for m, g in games.items():
    sched = SCHED.get(m)
    g["game_date_source"] = "report" if g["game_date_printed"] else ""
    if sched is None:
        if not g["game_date_printed"]:
            g["game_date_source"] = "not printed; not inferred"
        continue
    row, sdate, stip = sched
    g["schedule_row"], g["tip_et_from_schedule"] = row, stip
    if not g["game_date_printed"]:
        g["game_date"] = sdate
        g["game_date_source"] = "schedule-context (both documents cited)"
    if g["time_printed"] and clock_minutes(g["time_printed"]) != clock_minutes(stip):
        g["tip_disagreement"] = f"report {g['time_printed']} vs schedule {stip}"
    else:
        g["tip_disagreement"] = None

game_list = []
for m in order:
    g = games[m]
    entry = {"matchup": m, "game_date": g["game_date"], "game_date_printed": g["game_date_printed"],
             "game_date_source": g["game_date_source"], "tip_et_from_report": g["time_printed"],
             "tip_et_from_schedule": g.get("tip_et_from_schedule", ""),
             "tip_disagreement": g.get("tip_disagreement"), "rows": g["rows"]}
    if "schedule_row" in g:
        entry["schedule_row"] = g["schedule_row"]
    game_list.append(entry)

row_count = sum(len(g["rows"]) for g in game_list) + len(unattributed)
doc = {
    "snapshot_id": "injuries-2026-11-19-0145am",
    "kind": "official_injury_report_rows",
    "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf",
    "source_document": "Injury Report: 11/19/26 01:45 AM",
    "source_document_header": "Injury Report: 11/19/26 01:45 AM",
    "source_index_url": "https://official.nba.com/nba-injury-report-2026-27-season/",
    "secondary_source_url": SCHED_URL,
    "raw_extraction": "data/snapshots/raw/injury-2026-11-19T0145am-et.txt",
    "revision_et_label": "11/19/26 01:45 AM",
    "revision_utc": "2026-11-19T06:45:00Z",
    "fetched_at_utc": FETCHED,
    "extraction_tool": "fetch_page (PDF text extraction to markdown tables, single chunk, hasMore=false)",
    "fetch_time_note": "The fetch tool does not return its own timestamp. fetched_at_utc is the sandbox clock at the first shell call after the PDF fetch; the fetch itself happened no later than that.",
    "index_listing_checked": "The November 19 entries of the official injury-report index, read 2026-11-19 (session BR). The index lists 11/19 reports from 12:00 a.m. to 1:45 a.m. ET; 1:45 a.m. ET was the newest listed at the check. Later revisions are not in this file and supersede it.",
    "newest_report_listed_at_check": {"label": "11/19 01:45 AM ET report",
                                      "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf",
                                      "checked_at_utc": FETCHED},
    "superseded_snapshot_chain": [],
    "supersession_note": "This is one dated revision of the 11/19 slate. The league publishes revisions continually; any later revision supersedes this file.",
    "extraction_notes": [
        "Rows are transcribed from the printed text in raw/injury-2026-11-19T0145am-et.txt by scripts/_gen_2026_11_19_injury.py; blank cells stay blank.",
        "The NYK@MIN block prints four Minnesota Timberwolves rows and no New York Knicks row (neither an injury row nor a NOT YET SUBMITTED row). The absence is not interpreted.",
        "Where the report prints no game date or tip time (POR@MIL on page 2; TOR@DET, WAS@CHI, SAC@LAL on page 3; and the NOP@OKC, PHX@UTA and HOU@DEN dates), the date and ET tip are taken from the official schedule PDF GAME row cited in schedule_row (schedule-context, both documents cited). Printed tip times are compared with the schedule; see tip_disagreement.",
        "Two page-2 rows (Kuminga, Jonathan and Pullin, Zyon) print a status and reason but no date, time, matchup or team. They are kept in unattributed_rows as printed and are not assigned to any team or game.",
        "Page-3 rows for TOR@DET, NOP@OKC, WAS@CHI, PHX@UTA, HOU@DEN and SAC@LAL print a matchup and team but the status cell of the printed team row is absent. Those status cells are left blank; the reporting state is not inferred.",
        "The page-3 matchups have no printed date; the official schedule lists each one as a 11/20 game (GAME 43-51), so the schedule date is used. Repository copies (rest-window-2026-11-17.json) end at row 273 and were not used for these games.",
        "The report prints tip times without AM/PM (for example '08:00 (ET)'). Every printed tip in this report is an evening tip per the schedule, so the agreement check reads them as PM; tip_disagreement records any mismatch and none was found.",
        "The reporting-state rows (NOT YET SUBMITTED) are a reporting state, not a status, probability or pick.",
        "No availability probability, minute estimate or production impact is stored here or derived from these rows.",
    ],
    "matchups_not_in_snapshot": [],
    "schedule_read": {"source_url": SCHED_URL, "read_by": "fetch_page chunks 1-2 (GAME 161-311 printed rows)", "rows_used": "GAME 43-51 and 270-273", "fetched_at_utc": FETCHED},
    "row_count": row_count,
    "games_counted": len(game_list),
    "games": game_list,
    "unattributed_rows": unattributed,
}
OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

ptr = {
    "snapshot_id": "injuries-newest-pointer-2026-11-19",
    "kind": "official_injury_report_index_pointer",
    "source_url": "https://official.nba.com/nba-injury-report-2026-27-season/",
    "source_document_header": "NBA Injury Report: 2026-27 Season | NBA Official",
    "fetched_at_utc": FETCHED,
    "extraction_tool": "fetch_page (web page extraction)",
    "purpose": "Metadata only: the 11/19 01:45 AM ET report was the newest 11/19 entry listed on the official index at the check time. Its rows are transcribed in injuries-2026-11-19-0145am.json.",
    "source_index_url": "https://official.nba.com/nba-injury-report-2026-27-season/",
    "newest_listed_label": "11/19 01:45 AM ET",
    "newest_listed_pdf": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf",
    "index_entries_seen_nov_19": ["12:00 a.m ET", "12:15 a.m ET", "12:30 a.m ET", "12:45 a.m ET",
                                  "1:00 a.m ET", "1:15 a.m ET", "1:30 a.m ET", "1:45 a.m ET"],
    "note": "The index page as fetched lists 11/19 entries only through 1:45 a.m. ET; the 11/20 and later entries were not on that page. A later 11/19 revision may already exist.",
}
PTR.write_text(json.dumps(ptr, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("games", len(game_list), "rows", row_count, "unattributed", len(unattributed))
