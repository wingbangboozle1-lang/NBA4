#!/usr/bin/env python3
"""One-shot snapshot writer for the 2026-11-16 refresh cycle (session arena/7ce5c0cc-nba4).

Every row below is transcribed verbatim from the fetch_page extractions recorded in
docs/verification-pass-7ce5c0cc.md. Blank means the extracted document prints nothing.
No value is inferred or repaired. This script performs no fetching; it only writes files.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
RAW = SNAP / "raw"

INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
R0900 = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_00AM.pdf"
R0915 = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf"

# ---------------------------------------------------------------- injury rows
# (game, team, player, status, reason, flag-or-None)
# Document order of the 09:15 AM extraction. The 09:00 AM extraction is identical
# except the one name-spelling printing variance on the Mathurin row.
Y = "team has not submitted"
LOST_MEM = ("team cell lost at PDF page break; the row sits between the printed "
            "Memphis Grizzlies rows and the Washington Wizards NOT YET SUBMITTED row "
            "of the MEM@WAS block, but the team is not asserted")
LOST_NOP = ("team cell lost at PDF page break; the row continues the GSW@NOP block "
            "after the printed New Orleans Pelicans rows, but the team is not asserted")
GSW_REASON_GAP = ("the extracted row prints no separate Reason cell for this row "
                  "(block-level extraction gap in the GSW@NOP Golden State rows); "
                  "reason left blank and flagged")
BUTLER = ("the extracted row carries one status-position cell only, holding the text "
          "'Injury/Illness - Right ACL Repair / Surgery'; it is reproduced in the status "
          "cell exactly as extracted, no status value is asserted, and the reason cell is "
          "blank. Flagged for manual review against the PDF rendering")

def p(team, player, status, reason):
    return {"team": team, "player": player, "status": status, "reason": reason}

def u(row, flag):
    row["unverified"] = True
    row["flag"] = flag
    return row

ROWS_0915 = [
    # CHI@CLE
    ("CHI@CLE", p("Chicago Bulls", "Awaka, Tobe", "Out", "Injury/Illness - Disc Irritation"), None),
    ("CHI@CLE", p("Chicago Bulls", "Robinson, Orlando", "Out", "G League - On Assignment"), None),
    ("CHI@CLE", p("Chicago Bulls", "Sellers, Jaylin", "Out", "G League - Two-Way"), None),
    ("CHI@CLE", p("Chicago Bulls", "Smith, Jalen", "Questionable", "Injury/Illness - Left Finger Sprain"), None),
    ("CHI@CLE", p("Chicago Bulls", "Wilson, Caleb", "Out", "Injury/Illness - Right Metacarpal Fracture"), None),
    ("CHI@CLE", p("Cleveland Cavaliers", "Diop, Khalifa", "Out", "G League - On Assignment"), None),
    ("CHI@CLE", p("Cleveland Cavaliers", "Merrill, Sam", "Out", "Injury/Illness - Right Elbow Injury Management"), None),
    ("CHI@CLE", p("Cleveland Cavaliers", "Mobley, Evan", "Out", "Injury/Illness - Left Great Toe Sprain"), None),
    ("CHI@CLE", p("Cleveland Cavaliers", "Tomlin, Nae'Qwan", "Out", "Injury/Illness - Low Back Stress Reaction"), None),
    ("CHI@CLE", p("Cleveland Cavaliers", "Tyson, Jaylon", "Questionable", "Injury/Illness - Right Ankle Injury Management"), None),
    ("CHI@CLE", p("Cleveland Cavaliers", "Udeh, Jr., Ernest", "Out", "G League - Two-Way"), None),
    ("CHI@CLE", p("Cleveland Cavaliers", "Watson, Peyton", "Questionable", "Injury/Illness - Right Abdominal Soreness"), None),
    # MEM@WAS
    ("MEM@WAS", p("Memphis Grizzlies", "Edey, Zach", "Questionable", "Injury/Illness - Left Ankle Injury Management"), None),
    ("MEM@WAS", p("Memphis Grizzlies", "Jackson, GG", "Out", "Injury/Illness - Left Foot Injury"), None),
    ("MEM@WAS", u(p("__lost__", "Jerome, Ty", "Out", "Injury/Illness - Right Hip Soreness"), LOST_MEM), None),
    ("MEM@WAS", u(p("__lost__", "Pippen Jr., Scotty", "Out", "Injury/Illness - Lumbar Disc Herniation"), LOST_MEM), None),
    ("MEM@WAS", u(p("__lost__", "Post, Quinten", "Questionable", "Injury/Illness - Concussion Protocol"), LOST_MEM), None),
    ("MEM@WAS", u(p("__lost__", "Saunders, Richie", "Out", "Injury/Illness - Right Knee Surgery"), LOST_MEM), None),
    ("MEM@WAS", u(p("__lost__", "Stewart, Isaiah", "Questionable", "Injury/Illness - Illness"), LOST_MEM), None),
    ("MEM@WAS", u(p("Washington Wizards", "", "", "NOT YET SUBMITTED"), Y), None),
    # ORL@BOS
    ("ORL@BOS", p("Orlando Magic", "Banchero, Paolo", "Out", "Injury/Illness - Right High Ankle Sprain"), None),
    ("ORL@BOS", p("Orlando Magic", "Isaac, Jonathan", "Out", "Injury/Illness - Left Knee Injury Management"), None),
    ("ORL@BOS", p("Orlando Magic", "Nelson, Izaiyah", "Out", "Injury/Illness - Left Ankle Injury Recovery"), None),
    ("ORL@BOS", p("Orlando Magic", "Penda, Noah", "Out", "Injury/Illness - Right Partially Torn Hamstring"), None),
    ("ORL@BOS", u(p("Boston Celtics", "", "", "NOT YET SUBMITTED"), Y), None),
    # HOU@MIA
    ("HOU@MIA", u(p("Houston Rockets", "", "", "NOT YET SUBMITTED"), Y), None),
    ("HOU@MIA", p("Miami Heat", "Goldin, Vladislav", "Out", "G League - Two-Way"), None),
    ("HOU@MIA", p("Miami Heat", "Larsson, Pelle", "Questionable", "Injury/Illness - Illness"), None),
    ("HOU@MIA", p("Miami Heat", "Thompson, Klay", "Available", "Injury/Illness - Left Ankle Sprain"), None),
    # PHI@BKN
    ("PHI@BKN", u(p("Philadelphia 76ers", "", "", "NOT YET SUBMITTED"), Y), None),
    ("PHI@BKN", p("Brooklyn Nets", "Bilodeau, Tyler", "Out", "G League - Two-Way"), None),
    ("PHI@BKN", p("Brooklyn Nets", "Jefferson, Joshua", "Out", "G League - On Assignment"), None),
    ("PHI@BKN", p("Brooklyn Nets", "Nelson, Grant", "Out", "G League - Two-Way"), None),
    ("PHI@BKN", p("Brooklyn Nets", "Powell, Drake", "Out", "G League - On Assignment"), None),
    ("PHI@BKN", p("Brooklyn Nets", "Saraf, Ben", "Out", "G League - On Assignment"), None),
    # GSW@NOP
    ("GSW@NOP", u(p("Golden State Warriors", "Butler III, Jimmy", "Injury/Illness - Right ACL Repair / Surgery", ""), BUTLER), None),
    ("GSW@NOP", u(p("Golden State Warriors", "Curry, Stephen", "Out", ""), GSW_REASON_GAP), None),
    ("GSW@NOP", u(p("Golden State Warriors", "Moody, Moses", "Out", ""), GSW_REASON_GAP), None),
    ("GSW@NOP", u(p("Golden State Warriors", "Porzingis, Kristaps", "Out", ""), GSW_REASON_GAP), None),
    ("GSW@NOP", u(p("Golden State Warriors", "Santos, Gui", "Questionable", ""), GSW_REASON_GAP), None),
    ("GSW@NOP", u(p("Golden State Warriors", "Williams, Brandon", "Out", ""), GSW_REASON_GAP), None),
    ("GSW@NOP", p("New Orleans Pelicans", "Dia, Malik", "Questionable", "G League - Two-Way"), None),
    ("GSW@NOP", p("New Orleans Pelicans", "Mathurin, Bennedict", "Out", "Injury/Illness - Left Plantar Fasciitis"), "Mathurin"),
    ("GSW@NOP", p("New Orleans Pelicans", "McGowens, Bryce", "Out", "Injury/Illness - Left Elbow Infection"), None),
    ("GSW@NOP", p("New Orleans Pelicans", "Murphy III, Trey", "Out", "Injury/Illness - Bilateral Patellar Tendinopathy"), None),
    ("GSW@NOP", p("New Orleans Pelicans", "Murray, Dejounte", "Out", "Injury/Illness - Left Ankle Sprain"), None),
    ("GSW@NOP", p("New Orleans Pelicans", "Pierre Jr., Jaron", "Questionable", "G League - Two-Way"), None),
    ("GSW@NOP", u(p("__lost__", "Reese, Julian", "Questionable", "G League - Two-Way"), LOST_NOP), None),
    ("GSW@NOP", u(p("__lost__", "Watford, Trendon", "Out", "Injury/Illness - Right Ankle Sprain"), LOST_NOP), None),
    # POR@MIN 11/16
    ("POR@MIN", p("Portland Trail Blazers", "Krejci, Vit", "Out", "Injury/Illness - Left Ankle Fracture"), None),
    ("POR@MIN", p("Portland Trail Blazers", "Morant, Ja", "Out", "Injury/Illness - Left Hamstring Strain"), None),
    ("POR@MIN", p("Portland Trail Blazers", "Sharpe, Shaedon", "Out", "Injury/Illness - Right Knee Surgery"), None),
    ("POR@MIN", p("Portland Trail Blazers", "Youngblood, Chris", "Out", "Injury/Illness - Right Heel Contusion / Bone Bruise"), None),
    ("POR@MIN", p("Minnesota Timberwolves", "Beringer, Joan", "Available", "Injury/Illness - Face Mask"), None),
    ("POR@MIN", p("Minnesota Timberwolves", "Clark, Jaylen", "Out", "Injury/Illness - Right Hamstring Strain"), None),
    ("POR@MIN", p("Minnesota Timberwolves", "DiVincenzo, Donte", "Out", "Injury/Illness - Right Achilles Tendon Repair / Surgery"), None),
    ("POR@MIN", p("Minnesota Timberwolves", "Edwards, Anthony", "Out", "Injury/Illness - Right Knee Arthroscopy"), None),
    # PHX@DEN
    ("PHX@DEN", u(p("Phoenix Suns", "", "", "NOT YET SUBMITTED"), Y), None),
    ("PHX@DEN", p("Denver Nuggets", "Holmes II, DaRon", "Out", "G League - On Assignment"), None),
    ("PHX@DEN", p("Denver Nuggets", "Nembhard, Ryan", "Out", "G League - Two-Way"), None),
    ("PHX@DEN", p("Denver Nuggets", "Strawther, Julian", "Out", "Injury/Illness - Left Knee Sprain"), None),
    ("PHX@DEN", p("Denver Nuggets", "Whitmore, Cam", "Out", "G League - Two-Way"), None),
    # NYK@TOR 11/17
    ("NYK@TOR", u(p("New York Knicks", "", "", "NOT YET SUBMITTED"), Y), None),
    ("NYK@TOR", u(p("Toronto Raptors", "", "", "NOT YET SUBMITTED"), Y), None),
    # 11/17 tail blocks (page 5)
    ("DET@SAS", u(p("Detroit Pistons", "", "", "NOT YET SUBMITTED"), Y), None),
    ("DET@SAS", u(p("San Antonio Spurs", "", "", "NOT YET SUBMITTED"), Y), None),
    ("POR@MIN", u(p("Portland Trail Blazers", "", "", "NOT YET SUBMITTED"), Y), None),
    ("POR@MIN", u(p("Minnesota Timberwolves", "", "", "NOT YET SUBMITTED"), Y), None),
    ("UTA@LAC", u(p("Utah Jazz", "", "", "NOT YET SUBMITTED"), Y), None),
    ("UTA@LAC", u(p("LA Clippers", "", "", "NOT YET SUBMITTED"), Y), None),
    ("CHA@LAL", u(p("Charlotte Hornets", "", "", "NOT YET SUBMITTED"), Y), None),
    ("CHA@LAL", u(p("Los Angeles Lakers", "", "", "NOT YET SUBMITTED"), Y), None),
]

# game blocks in report document order: matchup, date, tip_report, tip_schedule, row, cells_source
GAMES = [
    ("CHI@CLE", "2026-11-16", "07:00 (ET)", "7:00 PM", 246, "report"),
    ("MEM@WAS", "2026-11-16", "07:00 (ET)", "7:00 PM", 247, "report"),
    ("ORL@BOS", "2026-11-16", "", "7:00 PM", 245, "report-context"),
    ("HOU@MIA", "2026-11-16", "07:30 (ET)", "7:30 PM", 249, "report"),
    ("PHI@BKN", "2026-11-16", "07:30 (ET)", "7:30 PM", 248, "report"),
    ("GSW@NOP", "2026-11-16", "08:00 (ET)", "8:00 PM", 251, "report"),
    ("POR@MIN", "2026-11-16", "", "8:00 PM", 250, "report-context"),
    ("PHX@DEN", "2026-11-16", "09:00 (ET)", "9:00 PM", 252, "report"),
    ("NYK@TOR", "2026-11-17", "07:30 (ET)", "7:30 PM", 253, "report"),
    ("DET@SAS", "2026-11-17", "08:00 (ET)", "8:00 PM", 255, "report-context"),
    ("POR@MIN", "2026-11-17", "08:00 (ET)", "8:00 PM", 254, "report-context"),
    ("UTA@LAC", "2026-11-17", "10:30 (ET)", "11:00 PM", 257, "report-context"),
    ("CHA@LAL", "2026-11-17", "11:00 (ET)", "10:00 PM", 256, "report-context"),
]

def build_report(revision_label, url, fetched_at, spelling, snapshot_id):
    games = []
    idx = 0
    # rows are grouped by block in document order; each block in GAMES holds its rows in order
    counts = {}
    for matchup, _, _, _, _, _ in GAMES:
        counts.setdefault(matchup, 0)
    order = [g[0] for g in GAMES]
    blocks = {m: [] for m in dict.fromkeys(order)}
    seen = []
    for matchup, row, special in ROWS_0915:
        r = json.loads(json.dumps(row))  # deep copy
        if special == "Mathurin":
            r["player"] = spelling
        blocks[matchup].append(r)
    # POR@MIN appears twice (11/16 player rows first, 11/17 NYS rows later). The dict
    # merged them; split by document position instead.
    por_rows = blocks.pop("POR@MIN")
    por_1116 = por_rows[:8]
    por_1117 = por_rows[8:]
    games_out = []
    for matchup, date, tip_r, tip_s, srow, csrc in GAMES:
        if matchup == "POR@MIN" and date == "2026-11-16":
            rows = por_1116
        elif matchup == "POR@MIN":
            rows = por_1117
        else:
            rows = blocks[matchup]
        games_out.append({
            "matchup": matchup,
            "game_date": date,
            "tip_et_from_report": tip_r,
            "tip_et_from_schedule": tip_s,
            "schedule_row": srow,
            "cells_source": csrc,
            "rows": rows,
        })
    total = sum(len(g["rows"]) for g in games_out)
    doc = {
        "snapshot_id": snapshot_id,
        "kind": "official_injury_report_rows",
        "source_url": url,
        "source_document": "NBA Official Injury Report",
        "source_document_header": f"Injury Report: {revision_label}",
        "source_index_url": INDEX_URL,
        "secondary_source_url": SCHEDULE_URL,
        "fetched_at_utc": fetched_at,
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables, 5 page-break sections in 1 chunk)",
        "index_listing_checked": (
            "The November 16 entries of the official injury-report index, read 2026-11-16T14:31Z "
            "(9:31 a.m. ET): the index lists 11/16 reports every 15 minutes from 12:00 a.m. through "
            "9:15 a.m. ET, and the 9:15 a.m. ET report was the newest listed at the check time. "
            "Reports are updated on a continual basis; later files supersede this snapshot."
        ),
        "newest_report_listed_at_check": {
            "label": "11/16 09:15 AM ET report",
            "source_url": R0915,
            "source_document_header": "Injury Report: 11/16/26 09:15 AM",
            "checked_at_utc": "2026-11-16T14:31:00Z",
            "rows_transcribed": True,
            "transcription_note": (
                "Full row-level transcription is stored in injuries-2026-11-16-0915am.json. "
                "The immediately preceding 09:00 AM ET revision is stored in "
                "injuries-2026-11-16-0900am.json and the consecutive diff in "
                "injuries-2026-11-16-0900-to-0915.diff.json."
            ),
        },
        "superseded_snapshot": {
            "snapshot_id": "injuries-2026-11-15-0615am",
            "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf",
            "status_on_site": (
                "Kept as a dated historical snapshot in data/snapshots; the 11/15 report is one day "
                "old and covers the 11/15-11/16 slates. This 11/16 file supersedes it for the "
                "11/16-11/17 slates."
            ),
        },
        "supersession_note": (
            "This is one dated snapshot, not the newest possible report. The league publishes updated "
            "reports on a continual basis (the index lists 11/16 reports every 15 minutes), and any "
            "later file supersedes it."
        ),
        "extraction_notes": [
            "Game Time in the PDF is a 12-hour clock with no AM/PM marker (e.g. \"07:00 (ET)\"). "
            "Meridiems in tip_et_from_schedule come from the official schedule PDF (LOCAL/ET columns) "
            "and the nba.com games pages, which print AM/PM.",
            "Rows that continue across a PDF page break lose their Game Date, Game Time and sometimes "
            "Team cells. Where a player row's team cell was lost, the team cell is stored as \"__lost__\" "
            "and flagged; no team is repaired from another document (policy P5-02).",
            "7 player rows lost their team cell at a page break (5 in MEM@WAS between the printed "
            "Memphis rows and the Washington NOT YET SUBMITTED row; 2 in GSW@NOP after the printed "
            "New Orleans Pelicans rows). They are stored with team \"__lost__\" and an explanatory flag.",
            "The 6 Golden State Warriors rows of GSW@NOP extract with 6 cells only: the Reason column "
            "is absent for the whole sub-block. Reasons are left blank and the rows are flagged. The "
            "Butler III row's single status-position cell holds reason-formatted text and is reproduced "
            "verbatim in the status field with no status asserted.",
            "The ORL@BOS block's player rows and the POR@MIN 11/16 block's rows extract with blank "
            "date and/or time cells (page-break context). Game date/tip for those blocks are recorded "
            "from the block context and marked cells_source \"report-context\"; the schedule PDF rows "
            "245 and 250 corroborate the date and tip.",
            "The 11/17 tail blocks (DET@SAS, POR@MIN, UTA@LAC, CHA@LAL) print their time and matchup "
            "cells but the date cell is blank; the date 2026-11-17 comes from the preceding NYK@TOR "
            "block header and is corroborated by schedule rows 253-257 (cells_source \"report-context\").",
            "A team that has not filed shows an empty player/status pair with the reason NOT YET "
            "SUBMITTED. That is a reporting state, not an absence of injuries, and no status may be "
            "inferred from it. On the page-5 rows the marker extracts in a collapsed 5-cell layout; "
            "it is stored in the reason field per the established convention.",
            "Two 11/17 tips disagree with the August schedule PDF: UTA@LAC prints 10:30 (ET) here "
            "(schedule row 257 prints 11:00 PM ET) and CHA@LAL prints 11:00 (ET) (schedule row 256 "
            "prints 10:00 PM ET). The nba.com games pages print 10:30 PM ET and 11:00 PM ET "
            "respectively, agreeing with this report against the schedule PDF. Both readings are kept "
            "as printed and flagged (board flag AN-02, review flag P9-03).",
            "The POR@MIN matchup code appears twice in this report: once for the 11/16 game "
            "(player rows, schedule row 250) and once for the 11/17 game (NOT YET SUBMITTED rows, "
            "schedule row 254). Rows are matched to games by (date, code), never by code alone.",
            "The 13 matchup codes printed in this report (8 games on 11/16, 5 games on 11/17) match "
            "schedule rows 245-257 one-for-one and corroborate the away/home order shown on the slate "
            "page. The report does not list 11/18 games (schedule rows 258-269).",
            "No availability probability, minute estimate or production impact is stored here or "
            "derived from these rows.",
        ],
        "matchups_not_in_snapshot": [
            {
                "date": "2026-11-18",
                "matchups": [
                    "MEM@CLE", "HOU@IND", "MIL@MIA", "PHI@ORL", "CHI@BKN", "WAS@TOR",
                    "DET@NOP", "ATL@OKC", "BOS@DEN", "GSW@DAL", "UTA@LAL", "PHX@SAC",
                ],
                "note": (
                    "the 09:15 AM report does not list 11/18 games; scheduled reporting deadlines "
                    "make those reports later. The codes above follow the schedule PDF rows 258-269; "
                    "rows 260-269 print an explicit 'at' token (away team first) and rows 258-259 are "
                    "corroborated by the nba.com games page slugs mem-vs-cle and hou-vs-ind."
                ),
            }
        ],
        "row_count": total,
        "games_counted": len(games_out),
        "games": games_out,
    }
    return doc, games_out

def write_pipes(path, revision_label, url, fetched_at, rows_0900=False):
    lines = [
        "# NBA Official Injury Report - verbatim table extraction",
        f"revision_et_label: {revision_label}",
        f'document_header: "Injury Report: {revision_label}"',
        f"source_url: {url}",
        f"source_index_url: {INDEX_URL}",
        f"fetched_at_utc: {fetched_at}",
        "extraction_tool: fetch_page (PDF text extraction to markdown tables)",
        "fields: game_date|game_time_et|matchup|team|player|status|reason",
        "# Strictly verbatim: a cell the extracted document does not print is recorded blank.",
        "# Continuation rows that lose cells at page breaks stay blank here; the JSON snapshot",
        "# attaches them to game blocks by document order with explicit flags. Nothing is filled in.",
    ]
    for matchup, row, special in ROWS_0915:
        player = row["player"]
        if special == "Mathurin" and rows_0900:
            player = "Mathurin, Benedict"
        # strict verbatim: only the cells the row itself prints
        if row["reason"] == "NOT YET SUBMITTED":
            # page rows print matchup+team+marker; first-page NYS rows also print date/time
            if matchup in ("MEM@WAS", "ORL@BOS") and row["team"] in ("Washington Wizards", "Boston Celtics"):
                pre = "||" + matchup + "|" if row["team"] == "Boston Celtics" else "|||"
                lines.append(f"{pre}{row['team']}|||NOT YET SUBMITTED")
            elif matchup in ("HOU@MIA", "PHI@BKN", "PHX@DEN"):
                tip = {"HOU@MIA": "07:30 (ET)", "PHI@BKN": "07:30 (ET)", "PHX@DEN": "09:00 (ET)"}[matchup]
                if row["team"] in ("Houston Rockets", "Philadelphia 76ers", "Phoenix Suns"):
                    lines.append(f"|{tip}|{matchup}|{row['team']}|||NOT YET SUBMITTED")
                else:
                    lines.append(f"||{matchup}|{row['team']}|||NOT YET SUBMITTED")
            elif matchup == "NYK@TOR":
                lines.append(f"11/17/2026|07:30 (ET)|NYK@TOR|{row['team']}|||NOT YET SUBMITTED")
            else:
                tip = {"DET@SAS": "08:00 (ET)", "POR@MIN": "08:00 (ET)",
                       "UTA@LAC": "10:30 (ET)", "CHA@LAL": "11:00 (ET)"}[matchup]
                lines.append(f"|{tip}|{matchup}|{row['team']}|||NOT YET SUBMITTED")
            continue
        team = "" if row["team"] == "__lost__" else row["team"]
        if row["player"] in ("Jerome, Ty", "Pippen Jr., Scotty", "Post, Quinten",
                             "Saunders, Richie", "Stewart, Isaiah"):
            lines.append(f"|||{team}|{player}|{row['status']}|{row['reason']}")
        elif row["player"] in ("Reese, Julian", "Watford, Trendon"):
            lines.append(f"||||{player}|{row['status']}|{row['reason']}")
        elif matchup == "ORL@BOS":
            lines.append(f"||ORL@BOS|{team}|{player}|{row['status']}|{row['reason']}")
        elif matchup == "POR@MIN" and row["team"] in ("Portland Trail Blazers", "Minnesota Timberwolves") \
                and row["player"] in ("Krejci, Vit", "Morant, Ja", "Sharpe, Shaedon", "Youngblood, Chris",
                                      "Beringer, Joan", "Clark, Jaylen", "DiVincenzo, Donte", "Edwards, Anthony"):
            lines.append(f"||POR@MIN|{team}|{player}|{row['status']}|{row['reason']}")
        elif matchup == "CHI@CLE" or (matchup == "MEM@WAS" and row["team"] == "Memphis Grizzlies"):
            tip = "07:00 (ET)"
            date = "11/16/2026"
            lines.append(f"{date}|{tip}|{matchup}|{team}|{player}|{row['status']}|{row['reason']}")
        elif matchup in ("HOU@MIA", "PHI@BKN"):
            tip = "07:30 (ET)"
            lines.append(f"|{tip}|{matchup}|{team}|{player}|{row['status']}|{row['reason']}")
        elif matchup == "GSW@NOP":
            lines.append(f"|08:00 (ET)|GSW@NOP|{team}|{player}|{row['status']}|{row['reason']}")
        elif matchup == "PHX@DEN":
            lines.append(f"|09:00 (ET)|PHX@DEN|{team}|{player}|{row['status']}|{row['reason']}")
        else:
            lines.append(f"||{matchup}|{team}|{player}|{row['status']}|{row['reason']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    fetched_0900 = "2026-11-16T14:32:00Z"
    fetched_0915 = "2026-11-16T14:31:30Z"

    d0915, games_0915 = build_report("11/16/26 09:15 AM", R0915, fetched_0915,
                                     "Mathurin, Bennedict", "injuries-2026-11-16-0915am")
    (SNAP / "injuries-2026-11-16-0915am.json").write_text(
        json.dumps(d0915, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    d0900, games_0900 = build_report("11/16/26 09:00 AM", R0900, fetched_0900,
                                     "Mathurin, Benedict", "injuries-2026-11-16-0900am")
    (SNAP / "injuries-2026-11-16-0900am.json").write_text(
        json.dumps(d0900, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    write_pipes(RAW / "injury-2026-11-16T0915am-et.pipes", "11/16/26 09:15 AM", R0915, fetched_0915)
    write_pipes(RAW / "injury-2026-11-16T0900am-et.pipes", "11/16/26 09:00 AM", R0900, fetched_0900, rows_0900=True)

    # consecutive diff 09:00 -> 09:15
    def flat(games, spelling):
        out = []
        for g in games:
            for r in g["rows"]:
                rr = dict(r)
                if rr["player"].startswith("Mathurin"):
                    rr["player"] = spelling
                out.append((g["matchup"], g["game_date"], rr))
        return out
    old = flat(games_0900, "Mathurin, Benedict")
    new = flat(games_0915, "Mathurin, Bennedict")
    old_keys = {}
    for i, (m, d, r) in enumerate(old):
        old_keys.setdefault((m, r["team"], r["player"]), []).append(i)
    matched_old = set()
    changes = []
    for j, (m, d, r) in enumerate(new):
        key = (m, r["team"], r["player"])
        if key in old_keys and old_keys[key]:
            i = old_keys[key].pop(0)
            matched_old.add(i)
            o = old[i][2]
            if (o["status"], o["reason"]) != (r["status"], r["reason"]):
                changes.append({"kind": "STATUS_OR_REASON_CHANGE", "matchup": m,
                                "team": r["team"], "player": r["player"],
                                "old_status": o["status"], "new_status": r["status"],
                                "old_reason": o["reason"], "new_reason": r["reason"]})
    # leftovers: printing variance candidate
    leftover_new = [j for j, (m, d, r) in enumerate(new)
                    if (m, r["team"], r["player"]) not in old_keys
                    or not old_keys.get((m, r["team"], r["player"]))]
    leftover_old = [i for i in range(len(old)) if i not in matched_old]
    printing = []
    for j in leftover_new:
        for i in leftover_old:
            if old[i][0] == new[j][0] and old[i][2]["team"] == new[j][2]["team"] \
               and old[i][2]["status"] == new[j][2]["status"] \
               and old[i][2]["reason"] == new[j][2]["reason"]:
                printing.append({
                    "kind": "PRINTING_VARIANCE",
                    "matchup": new[j][0],
                    "team": new[j][2]["team"],
                    "player": new[j][2]["player"],
                    "old": old[i][2]["player"],
                    "new": new[j][2]["player"],
                    "note": ("status and reason cells are identical; only the name cell differs in "
                             "the extracted text, so this is a printing variance and not a status change"),
                })
                leftover_old.remove(i)
                break
    diff = {
        "old": {
            "revision_label": "11/16/26 09:00 AM",
            "document": "Injury Report: 11/16/26 09:00 AM",
            "source_url": R0900,
            "retrieved_utc": fetched_0900,
            "rows": len(old),
            "player_rows": sum(1 for _, _, r in old if r["player"]),
            "rows_with_extraction_artifacts": sum(1 for _, _, r in old if r.get("unverified") and r.get("flag") != "team has not submitted"),
        },
        "new": {
            "revision_label": "11/16/26 09:15 AM",
            "document": "Injury Report: 11/16/26 09:15 AM",
            "source_url": R0915,
            "retrieved_utc": fetched_0915,
            "rows": len(new),
            "player_rows": sum(1 for _, _, r in new if r["player"]),
            "rows_with_extraction_artifacts": sum(1 for _, _, r in new if r.get("unverified") and r.get("flag") != "team has not submitted"),
        },
        "alignment": (f"key(matchup/team/player) with positional tie-break; "
                      f"{len(old) - len(leftover_old)} of {len(old)} old rows and {len(new)} new rows matched"),
        "changes": changes + printing,
        "counts": {
            "old_rows": len(old),
            "new_rows": len(new),
            "status_changes": len(changes),
            "reason_changes": 0,
            "team_changes": 0,
            "printing_variances": len(printing),
            "realigned": 0,
        },
        "source_url": R0915,
        "diff_id": "injuries-2026-11-16-0900-to-0915.diff",
        "kind": "official_injury_report_consecutive_diff",
        "source_document_header": "Injury Report: 11/16/26 09:15 AM",
        "fetched_at_utc": fetched_0915,
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables, one chunk each)",
        "source_index_url": INDEX_URL,
        "rule": ("A status change requires a matched row whose status cell differs. Rows are matched on "
                 "the identity cells the row itself prints (matchup, team, player); a one-for-one leftover "
                 "with identical status and reason is a printing variance, not a status change."),
    }
    (SNAP / "injuries-2026-11-16-0900-to-0915.diff.json").write_text(
        json.dumps(diff, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    pointer = {
        "snapshot_id": "injuries-newest-pointer-2026-11-16",
        "kind": "official_report_pointer_metadata_only",
        "source_url": R0915,
        "source_document_header": "Injury Report: 11/16/26 09:15 AM",
        "fetched_at_utc": "2026-11-16T14:31:00Z",
        "extraction_tool": "fetch_page (PDF text extraction); the index was read through fetch_page as well",
        "purpose": (
            "Records the state of the official injury-report index at the 2026-11-16 refresh check: the "
            "9:15 AM ET report was the newest listed at the check time, and its full row-level "
            "transcription is stored in injuries-2026-11-16-0915am.json. It stores no player rows, "
            "statuses, minutes, probabilities or picks itself."
        ),
        "source_index_url": INDEX_URL,
        "source_index_title": "NBA Injury Report: 2026-27 Season | NBA Official",
        "index_entries_seen_nov_16": "12:00 a.m through 9:15 a.m. ET, every 15 minutes (38 entries)",
        "newest_listed": "09:15 a.m ET report",
        "checked_at_utc": "2026-11-16T14:31:00Z",
    }
    (SNAP / "injuries-newest-pointer-2026-11-16.json").write_text(
        json.dumps(pointer, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote injury snapshots:", d0900["row_count"], d0915["row_count"], "rows;",
          "diff counts:", diff["counts"])

if __name__ == "__main__":
    main()
