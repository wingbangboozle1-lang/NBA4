#!/usr/bin/env python3
"""One-shot snapshot writer for the 2026-11-17 refresh cycle (session arena/0fec89b5-nba4).

Every row below is transcribed verbatim from the fetch_page extractions recorded in
docs/verification-pass-0fec89b5.md. Blank means the extracted document prints nothing.
No value is inferred or repaired. This script performs no fetching; it only writes files.

Sources read in this session (2026-11-17, UTC):
  * injury index  https://official.nba.com/nba-injury-report-2026-27-season/  (15:52Z check)
  * 10:15 AM ET PDF  .../Injury-Report_2026-11-17_10_15AM.pdf  (fetched 15:55Z)
  * 10:30 AM ET PDF  .../Injury-Report_2026-11-17_10_30AM.pdf  (fetched 15:53Z)
  * schedule PDF chunks 1 and 2 (rows 211-273)                (fetched 15:56-15:57Z)
  * games pages 11/17, 11/18, 11/19                           (fetched 15:58-16:01Z)
  * standings page chunks 0 and 1                             (fetched 16:02-16:03Z)
  * eight official game pages for 11/16 finals                (fetched 16:00-16:04Z)
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
RAW = SNAP / "raw"

INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
SCHEDULE_URL = (
    "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
)
R1015 = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf"
R1030 = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf"
FETCHED_1015 = "2026-11-17T15:55:00Z"
FETCHED_1030 = "2026-11-17T15:53:00Z"

# ---------------------------------------------------------------- injury rows
# (game, team, player, status, reason, flag-or-None)
# Document order of the 10:30 AM extraction (59 printed rows). The 10:15 AM
# extraction is content-identical; only the printed header differs.
Y = "team has not submitted"
LOST_LAL = (
    "team cell lost at PDF page break; the row continues the CHA@LAL block after the "
    "printed Los Angeles Lakers rows (Grimes, Kessler) and before the 11/18 section, "
    "but the team is not asserted"
)
KESSLER_JOIN = (
    'reason cell spans a PDF page boundary; the two extracted fragments were joined '
    'verbatim ("Injury/Illness - Right Lower Leg " + "Soreness")'
)


def p(team, player, status, reason):
    return {"team": team, "player": player, "status": status, "reason": reason}


def u(row, flag):
    row["unverified"] = True
    row["flag"] = flag
    return row


def nys(team):
    return u(p(team, "", "", "NOT YET SUBMITTED"), Y)


ROWS = [
    # NYK@TOR (11/17) - Toronto only prints rows
    ("NYK@TOR", p("Toronto Raptors", "Bittle, Nate", "Out", "Injury/Illness - Right Foot Avulsion Fracture"), None),
    ("NYK@TOR", p("Toronto Raptors", "Leonard, Kawhi", "Out", "Injury/Illness - Left Knee Injury Management"), None),
    ("NYK@TOR", p("Toronto Raptors", "McCullar Jr., Kevin", "Out", "G League - Two-Way"), None),
    ("NYK@TOR", p("Toronto Raptors", "Smith, Malachi", "Out", "G League - Two-Way"), None),
    # DET@SAS (11/17)
    ("DET@SAS", p("Detroit Pistons", "Duren, Jalen", "Out", "Injury/Illness - Right Hamstring Strain"), None),
    ("DET@SAS", p("Detroit Pistons", "Holland II, Ronald", "Out", "Injury/Illness - Left Knee Contusion / Bone Bruise"), None),
    ("DET@SAS", p("Detroit Pistons", "Joe, Isaiah", "Doubtful", "Injury/Illness - Right Hip Contusion"), None),
    ("DET@SAS", p("Detroit Pistons", "Okorie, Ebuka", "Out", "G League - On Assignment"), None),
    ("DET@SAS", p("Detroit Pistons", "Onyenso, Ugonna", "Out", "G League - Two-Way"), None),
    ("DET@SAS", p("Detroit Pistons", "Prince, Taurean", "Out", "Injury/Illness - Right Knee Soreness"), None),
    ("DET@SAS", p("Detroit Pistons", "Robinson, Duncan", "Out", "Injury/Illness - Left Quadriceps Strain"), None),
    ("DET@SAS", p("San Antonio Spurs", "Brown, Maliq", "Out", "G League - Two-Way"), None),
    ("DET@SAS", p("San Antonio Spurs", "Gillespie, Ja'Kobi", "Out", "G League - Two-Way"), None),
    ("DET@SAS", p("San Antonio Spurs", "Harris, Tobias", "Out", "Injury/Illness - Left Calf Strain"), None),
    ("DET@SAS", p("San Antonio Spurs", "Quaintance, Jayden", "Out", "Injury/Illness - Right Knee Surgery"), None),
    # POR@MIN (11/17)
    ("POR@MIN", nys("Portland Trail Blazers"), None),
    ("POR@MIN", nys("Minnesota Timberwolves"), None),  # page-2 first row: date/time/matchup lost
    # UTA@LAC (11/17) - page 2 prints no Game Date column
    ("UTA@LAC", p("Utah Jazz", "Bufkin, Kobe", "Out", "G League - Two-Way"), None),
    ("UTA@LAC", p("Utah Jazz", "Hayes, Jaxson", "Out", "Injury/Illness - Left Knee Strain"), None),
    ("UTA@LAC", p("Utah Jazz", "Ingram, Harrison", "Out", "G League - Two-Way"), None),
    ("UTA@LAC", p("Utah Jazz", "Jackson Jr., Jaren", "Out", "Injury/Illness - Right MCL Tear"), None),
    ("UTA@LAC", p("Utah Jazz", "Markkanen, Lauri", "Out", "Injury/Illness - Right Hand Fracture"), None),
    ("UTA@LAC", p("Utah Jazz", "Nurkic, Jusuf", "Out", "Injury/Illness - Right Right Foot; 2nd Plantar Plate Tear"), None),
    ("UTA@LAC", p("LA Clippers", "Beal, Bradley", "Out", "Injury/Illness - Right Knee Injury Management"), None),
    ("UTA@LAC", p("LA Clippers", "Ingram, Brandon", "Out", "Injury/Illness - Right Heel Surgery"), None),
    ("UTA@LAC", p("LA Clippers", "Miller, Jordan", "Out", "Injury/Illness - Left Rotator Cuff Surgery"), None),
    ("UTA@LAC", p("LA Clippers", "Niederhauser, Yanic Konan", "Out", "Injury/Illness - Right Lisfranc Surgery"), None),
    # CHA@LAL (11/17) - page 2 prints no Game Date column
    ("CHA@LAL", p("Charlotte Hornets", "Ajayi, Michael", "Out", "G League - Two-Way"), None),
    ("CHA@LAL", p("Charlotte Hornets", "Boswell, Kylan", "Out", "G League - Two-Way"), None),
    ("CHA@LAL", p("Charlotte Hornets", "Knueppel, Kon", "Out", "Injury/Illness - Left Hamstring Strain"), None),
    ("CHA@LAL", p("Charlotte Hornets", "Schroder, Dennis", "Out", "Injury/Illness - Left Hamstring Strain"), None),
    ("CHA@LAL", p("Charlotte Hornets", "Steinbach, Hannes", "Out", "G League - On Assignment"), None),
    ("CHA@LAL", p("Los Angeles Lakers", "Grimes, Quentin", "Available", "Injury/Illness - Right Finger Splint"), None),
    ("CHA@LAL", u(p("Los Angeles Lakers", "Kessler, Walker", "Out",
                    "Injury/Illness - Right Lower Leg Soreness"), KESSLER_JOIN), None),
    ("CHA@LAL", u(p("__lost__", "Reaves, Austin", "Out",
                    "Injury/Illness - Left Heel Contusion / Bone Bruise"), LOST_LAL), None),
    # 11/18 NOT YET SUBMITTED blocks, page 3 (date printed)
    ("HOU@IND", nys("Houston Rockets"), None),
    ("HOU@IND", nys("Indiana Pacers"), None),
    ("MEM@CLE", nys("Memphis Grizzlies"), None),
    ("MEM@CLE", nys("Cleveland Cavaliers"), None),
    ("MIL@MIA", nys("Milwaukee Bucks"), None),
    ("MIL@MIA", nys("Miami Heat"), None),
    ("PHI@ORL", nys("Philadelphia 76ers"), None),
    ("PHI@ORL", nys("Orlando Magic"), None),
    ("CHI@BKN", nys("Chicago Bulls"), None),
    ("CHI@BKN", nys("Brooklyn Nets"), None),
    ("WAS@TOR", nys("Washington Wizards"), None),
    ("WAS@TOR", nys("Toronto Raptors"), None),
    ("ATL@OKC", nys("Atlanta Hawks"), None),
    ("ATL@OKC", nys("Oklahoma City Thunder"), None),
    ("DET@NOP", nys("Detroit Pistons"), None),
    ("DET@NOP", nys("New Orleans Pelicans"), None),
    # 11/18 NOT YET SUBMITTED blocks, page 4 (date cell absent on this page)
    ("GSW@DAL", nys("Golden State Warriors"), None),
    ("GSW@DAL", nys("Dallas Mavericks"), None),
    ("BOS@DEN", nys("Boston Celtics"), None),
    ("BOS@DEN", nys("Denver Nuggets"), None),
    ("PHX@SAC", nys("Phoenix Suns"), None),
    ("PHX@SAC", nys("Sacramento Kings"), None),
    ("UTA@LAL", nys("Utah Jazz"), None),
    ("UTA@LAL", nys("Los Angeles Lakers"), None),
]

# game blocks in report document order:
# matchup, date, tip_report, tip_schedule, schedule_row, cells_source, tip_disagreement-or-None
GAMES = [
    ("NYK@TOR", "2026-11-17", "07:30 (ET)", "7:30 PM", 253, "report", None),
    ("DET@SAS", "2026-11-17", "08:00 (ET)", "8:00 PM", 255, "report", None),
    ("POR@MIN", "2026-11-17", "08:00 (ET)", "8:00 PM", 254, "report", None),
    ("UTA@LAC", "2026-11-17", "10:30 (ET)", "11:00 PM", 257, "report-context",
     "the report and the games page print 10:30 (ET); the August schedule PDF row 257 "
     "prints 11:00 PM ET; both values are kept as printed"),
    ("CHA@LAL", "2026-11-17", "11:00 (ET)", "10:00 PM", 256, "report-context",
     "the report and the games page print 11:00 (ET); the August schedule PDF row 256 "
     "prints 10:00 PM ET; both values are kept as printed"),
    ("HOU@IND", "2026-11-18", "07:00 (ET)", "7:00 PM", 259, "report", None),
    ("MEM@CLE", "2026-11-18", "07:00 (ET)", "7:00 PM", 258, "report", None),
    ("MIL@MIA", "2026-11-18", "07:00 (ET)", "7:00 PM", 260, "report", None),
    ("PHI@ORL", "2026-11-18", "07:00 (ET)", "7:00 PM", 261, "report", None),
    ("CHI@BKN", "2026-11-18", "07:30 (ET)", "7:30 PM", 262, "report", None),
    ("WAS@TOR", "2026-11-18", "07:30 (ET)", "7:30 PM", 263, "report", None),
    ("ATL@OKC", "2026-11-18", "08:00 (ET)", "8:00 PM", 265, "report", None),
    ("DET@NOP", "2026-11-18", "08:00 (ET)", "8:00 PM", 264, "report", None),
    ("GSW@DAL", "2026-11-18", "", "9:30 PM", 267, "report-context",
     "the games page prints 8:00 PM ET and the August schedule PDF row 267 prints "
     "9:30 PM ET; this report prints no time cell for the game (PDF page break); "
     "both printed values are kept"),
    ("BOS@DEN", "2026-11-18", "09:30 (ET)", "9:00 PM", 266, "report-context",
     "the report and the games page print 09:30 (ET); the August schedule PDF row 266 "
     "prints 9:00 PM ET; both values are kept as printed"),
    ("PHX@SAC", "2026-11-18", "10:00 (ET)", "10:00 PM", 269, "report-context", None),
    ("UTA@LAL", "2026-11-18", "10:00 (ET)", "10:00 PM", 268, "report-context", None),
]


def build_report(revision_label, url, fetched_at, snapshot_id):
    # split ROWS onto blocks in document order
    blocks: dict[str, list] = {}
    for matchup, row, special in ROWS:
        blocks.setdefault(matchup, []).append(json.loads(json.dumps(row)))
    games_out = []
    for matchup, date, tip_r, tip_s, srow, csrc, tdis in GAMES:
        game = {
            "matchup": matchup,
            "game_date": date,
            "tip_et_from_report": tip_r,
            "tip_et_from_schedule": tip_s,
            "schedule_row": srow,
            "cells_source": csrc,
            "rows": blocks[matchup],
        }
        if tdis:
            game["tip_disagreement"] = tdis
        games_out.append(game)
    total = sum(len(g["rows"]) for g in games_out)
    return {
        "snapshot_id": snapshot_id,
        "kind": "official_injury_report_rows",
        "source_url": url,
        "source_document": "NBA Official Injury Report",
        "source_document_header": f"Injury Report: {revision_label}",
        "source_index_url": INDEX_URL,
        "secondary_source_url": SCHEDULE_URL,
        "fetched_at_utc": fetched_at,
        "extraction_tool": (
            "fetch_page (PDF text extraction to markdown tables; the document extracts as "
            "four page-break sections in 1 chunk)"
        ),
        "index_listing_checked": (
            "The November 17 entries of the official injury-report index, read 2026-11-17T15:52Z "
            "(10:52 a.m. ET): the index lists 11/17 reports every 15 minutes from 12:00 a.m. "
            "through 10:30 a.m. ET, and the 10:30 a.m. ET report was the newest listed at the "
            "check time. Reports are updated on a continual basis; later files supersede this "
            "snapshot."
        ),
        "newest_report_listed_at_check": {
            "label": "11/17 10:30 AM ET report",
            "source_url": R1030,
            "source_document_header": "Injury Report: 11/17/26 10:30 AM",
            "checked_at_utc": "2026-11-17T15:52:00Z",
            "rows_transcribed": True,
            "transcription_note": (
                "Full row-level transcription is stored in injuries-2026-11-17-1030am.json "
                "(this file). The immediately preceding 10:15 AM ET revision is stored in "
                "injuries-2026-11-17-1015am.json and the consecutive diff in "
                "injuries-2026-11-17-1015-to-1030.diff.json."
            ),
        },
        "superseded_snapshot": {
            "snapshot_id": "injuries-2026-11-16-1000am",
            "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_00AM.pdf",
            "status_on_site": (
                "Kept as a dated historical snapshot in data/snapshots; the 11/16 10:00 AM report "
                "covers the 11/16-11/17 slates. This 11/17 file supersedes it for the "
                "11/17-11/19 slates."
            ),
        },
        "supersession_note": (
            "This is one dated snapshot, not the newest possible report. The league publishes "
            "updated reports on a continual basis (the index lists 11/17 reports every 15 minutes), "
            "and any later file supersedes it."
        ),
        "extraction_notes": [
            "Game Time in the PDF is a 12-hour clock with no AM/PM marker (e.g. \"07:30 (ET)\"). "
            "Meridiems in tip_et_from_schedule come from the official schedule PDF (LOCAL/ET "
            "columns) and the nba.com games pages, which print AM/PM.",
            "Rows that continue across a PDF page break lose their Game Date, Game Time, Matchup "
            "and sometimes Team cells. Where a player row's team cell was lost, the team cell is "
            "stored as \"__lost__\" and flagged; no team is repaired from another document "
            "(policy P5-02). One row (Reaves, Austin, CHA@LAL) lost its team cell this way.",
            "Page 2 of the extracted document carries no Game Date column at all: the UTA@LAC and "
            "CHA@LAL blocks print time, matchup, team, player, status and reason but no date. "
            "The block date 2026-11-17 comes from the preceding 11/17 blocks and is corroborated "
            "by schedule rows 256-257; those blocks are marked cells_source \"report-context\".",
            "The Kessler, Walker reason cell spans the page 2 / page 3 boundary: the document "
            "prints \"Injury/Illness - Right Lower Leg\" on page 2 and the fragment \"Soreness\" "
            "in the player-name position of page 3's first row. The two fragments are joined "
            "verbatim (Sorber precedent, 11/15 06:15 AM snapshot) and the row is flagged; no "
            "other cell on the row is altered.",
            "Page 4 of the extracted document carries no Game Date column: the GSW@DAL, BOS@DEN, "
            "PHX@SAC and UTA@LAL NOT YET SUBMITTED blocks print time (except GSW@DAL, whose time "
            "cell is also blank), matchup, team and the marker. The block date 2026-11-18 comes "
            "from the page-3 11/18 section and is corroborated by schedule rows 266-269; those "
            "blocks are marked cells_source \"report-context\".",
            "A team that has not filed shows an empty player/status pair with the reason NOT YET "
            "SUBMITTED. That is a reporting state, not an absence of injuries, and no status may "
            "be inferred from it.",
            "Four tip clocks disagree with the August schedule PDF: UTA@LAC (report/games page "
            "10:30 (ET) vs schedule row 257 11:00 PM ET), CHA@LAL (11:00 vs 10:00 PM ET), "
            "BOS@DEN (09:30 vs 9:00 PM ET) and GSW@DAL (games page 8:00 PM ET vs schedule row "
            "267 9:30 PM ET; the report prints no time for GSW@DAL). The nba.com games pages "
            "agree with the report on the first three. All printed values are kept and flagged "
            "(extends flags AN-02 / P9-04).",
            "The 17 matchup codes printed in this report (5 games on 11/17, 12 games on 11/18) "
            "match schedule rows 253-269 one-for-one and corroborate the away/home order shown "
            "on the slate page. The report does not list 11/19 games (schedule rows 270-273).",
            "The 10:15 AM and 10:30 AM revisions print identical rows: 59 rows each, identical "
            "identity, status and reason cells. The diff is published as a measured zero-change "
            "result, never as an assumption that the report did not change.",
            "No availability probability, minute estimate or production impact is stored here or "
            "derived from these rows.",
        ],
        "matchups_not_in_snapshot": [
            {
                "date": "2026-11-19",
                "matchups": ["GSW@MEM", "POR@MIL", "NYK@MIN", "LAC@SAS"],
                "note": (
                    "the 10:30 AM report does not list 11/19 games; scheduled reporting "
                    "deadlines make those reports later. The codes above follow schedule PDF "
                    "rows 270-273, which print an explicit 'at' token (away team first) and "
                    "are corroborated by the nba.com games page slugs gsw-vs-mem, por-vs-mil, "
                    "nyk-vs-min and lac-vs-sas."
                ),
            }
        ],
        "row_count": total,
        "games_counted": len(games_out),
        "games": games_out,
    }


def write_pipes(path, revision_label, url, fetched_at):
    lines = [
        "# NBA Official Injury Report - verbatim table extraction",
        f"revision_utc: {'2026-11-17T15:15:00Z' if '10:15' in revision_label else '2026-11-17T15:30:00Z'}",
        f"revision_et_label: {revision_label}",
        f'document_header: "Injury Report: {revision_label}"',
        f"source_url: {url}",
        f"source_index_url: {INDEX_URL}",
        f"fetched_at_utc: {fetched_at}",
        "extraction_tool: fetch_page (PDF text extraction to markdown tables, single chunk)",
        "fields: game_date|game_time_et|matchup|team|player|status|reason",
        "# Strictly verbatim: a cell the extracted document does not print is recorded blank.",
        "# Continuation rows that lose cells at page breaks stay blank here; the JSON snapshot",
        "# attaches them to game blocks by document order with explicit flags. Nothing is filled in.",
        "# Page 2 and page 4 of the extraction carry no Game Date column: those rows record a blank",
        "# game_date. The Kessler, Walker reason cell is joined verbatim across the page 2/3 break",
        '# ("Injury/Illness - Right Lower Leg " + "Soreness") per the Sorber precedent; the joined',
        "# row is flagged in the JSON snapshot and no fragment row is invented.",
    ]
    for matchup, row, _special in ROWS:
        team = "" if row["team"] == "__lost__" else row["team"]
        if row["reason"] == "NOT YET SUBMITTED":
            if matchup == "POR@MIN" and row["team"] == "Portland Trail Blazers":
                lines.append("11/17/2026|08:00 (ET)|POR@MIN|Portland Trail Blazers|||NOT YET SUBMITTED")
            elif matchup == "POR@MIN":
                lines.append("|||Minnesota Timberwolves|||NOT YET SUBMITTED")
            elif matchup in ("UTA@LAC", "CHA@LAL"):
                tip = "10:30 (ET)" if matchup == "UTA@LAC" else "11:00 (ET)"
                lines.append(f"|{tip}|{matchup}|{row['team']}|||NOT YET SUBMITTED")
            elif matchup in ("GSW@DAL",):
                lines.append(f"||{matchup}|{row['team']}|||NOT YET SUBMITTED")
            elif matchup in ("BOS@DEN", "PHX@SAC", "UTA@LAL"):
                tip = {"BOS@DEN": "09:30 (ET)", "PHX@SAC": "10:00 (ET)",
                       "UTA@LAL": "10:00 (ET)"}[matchup]
                lines.append(f"|{tip}|{matchup}|{row['team']}|||NOT YET SUBMITTED")
            elif matchup in ("HOU@IND", "MEM@CLE", "MIL@MIA", "PHI@ORL"):
                tip = {"HOU@IND": "07:00 (ET)", "MEM@CLE": "07:00 (ET)",
                       "MIL@MIA": "07:00 (ET)", "PHI@ORL": "07:00 (ET)"}[matchup]
                lines.append(f"11/18/2026|{tip}|{matchup}|{row['team']}|||NOT YET SUBMITTED")
            else:
                tip = {"CHI@BKN": "07:30 (ET)", "WAS@TOR": "07:30 (ET)",
                       "ATL@OKC": "08:00 (ET)", "DET@NOP": "08:00 (ET)"}[matchup]
                lines.append(f"11/18/2026|{tip}|{matchup}|{row['team']}|||NOT YET SUBMITTED")
            continue
        if row["player"] == "Reaves, Austin":
            lines.append(f"||||{row['player']}|{row['status']}|{row['reason']}")
        elif matchup == "NYK@TOR":
            lines.append(
                f"11/17/2026|07:30 (ET)|NYK@TOR|{team}|{row['player']}|{row['status']}|{row['reason']}"
            )
        elif matchup == "DET@SAS":
            lines.append(
                f"11/17/2026|08:00 (ET)|DET@SAS|{team}|{row['player']}|{row['status']}|{row['reason']}"
            )
        elif matchup == "UTA@LAC":
            lines.append(
                f"|10:30 (ET)|UTA@LAC|{team}|{row['player']}|{row['status']}|{row['reason']}"
            )
        elif matchup == "CHA@LAL":
            lines.append(
                f"|11:00 (ET)|CHA@LAL|{team}|{row['player']}|{row['status']}|{row['reason']}"
            )
        else:  # pragma: no cover - defensive
            raise SystemExit(f"unhandled row: {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- slate
# (row, date, weekday, away, home, local, et, tv, code, slug, gp_tip, tdis, at_token, note)
SLATE = [
    (253, "2026-11-17", "Tue.", "New York", "Toronto", "7:30 PM", "7:30 PM", "",
     "NYK@TOR", "nyk-vs-tor", "7:30 PM ET", None, False, ""),
    (254, "2026-11-17", "Tue.", "Portland", "Minnesota", "7:00 PM", "8:00 PM", "",
     "POR@MIN", "por-vs-min", "8:00 PM ET", None, False, ""),
    (255, "2026-11-17", "Tue.", "Detroit", "San Antonio", "7:00 PM", "8:00 PM", "NBC/PCK",
     "DET@SAS", "det-vs-sas", "8:00 PM ET", None, False,
     "PDF broadcast column reads NBC/PCK"),
    (256, "2026-11-17", "Tue.", "Charlotte", "LA Lakers", "7:00 PM", "10:00 PM", "",
     "CHA@LAL", "cha-vs-lal", "11:00 PM ET",
     "games page prints 11:00 PM ET for this pairing; the August schedule PDF prints "
     "10:00 PM ET; the 11/17 10:30 AM injury report also prints 11:00 (ET)",
     False, ""),
    (257, "2026-11-17", "Tue.", "Utah", "LA Clippers", "8:00 PM", "11:00 PM", "NBC/PCK",
     "UTA@LAC", "uta-vs-lac", "10:30 PM ET",
     "games page prints 10:30 PM ET for this pairing; the August schedule PDF prints "
     "11:00 PM ET; the 11/17 10:30 AM injury report also prints 10:30 (ET)",
     False, "PDF broadcast column reads NBC/PCK"),
    (258, "2026-11-18", "Wed.", "Memphis", "Cleveland", "7:00 PM", "7:00 PM", "",
     "MEM@CLE", "mem-vs-cle", "7:00 PM ET", None, False, ""),
    (259, "2026-11-18", "Wed.", "Houston", "Indiana", "7:00 PM", "7:00 PM", "",
     "HOU@IND", "hou-vs-ind", "7:00 PM ET", None, False, ""),
    (260, "2026-11-18", "Wed.", "Milwaukee", "Miami", "7:00 PM", "7:00 PM", "ESPN",
     "MIL@MIA", "mil-vs-mia", "7:00 PM ET", None, True,
     "PDF broadcast column reads ESPN"),
    (261, "2026-11-18", "Wed.", "Philadelphia", "Orlando", "7:00 PM", "7:00 PM", "",
     "PHI@ORL", "phi-vs-orl", "7:00 PM ET", None, True, ""),
    (262, "2026-11-18", "Wed.", "Chicago", "Brooklyn", "7:30 PM", "7:30 PM", "",
     "CHI@BKN", "chi-vs-bkn", "7:30 PM ET", None, True, ""),
    (263, "2026-11-18", "Wed.", "Washington", "Toronto", "7:30 PM", "7:30 PM", "",
     "WAS@TOR", "was-vs-tor", "7:30 PM ET", None, True, ""),
    (264, "2026-11-18", "Wed.", "Detroit", "New Orleans", "7:00 PM", "8:00 PM", "",
     "DET@NOP", "det-vs-nop", "8:00 PM ET", None, True, ""),
    (265, "2026-11-18", "Wed.", "Atlanta", "Oklahoma City", "7:00 PM", "8:00 PM", "",
     "ATL@OKC", "atl-vs-okc", "8:00 PM ET", None, True, ""),
    (266, "2026-11-18", "Wed.", "Boston", "Denver", "7:00 PM", "9:00 PM", "",
     "BOS@DEN", "bos-vs-den", "9:30 PM ET",
     "games page prints 9:30 PM ET for this pairing; the August schedule PDF prints "
     "9:00 PM ET; the 11/17 10:30 AM injury report also prints 09:30 (ET)",
     True, ""),
    (267, "2026-11-18", "Wed.", "Golden State", "Dallas", "8:30 PM", "9:30 PM", "ESPN",
     "GSW@DAL", "gsw-vs-dal", "8:00 PM ET",
     "games page prints 8:00 PM ET for this pairing; the August schedule PDF prints "
     "9:30 PM ET; the 11/17 10:30 AM injury report prints no time cell for this game "
     "(PDF page break)",
     True, "PDF broadcast column reads ESPN"),
    (268, "2026-11-18", "Wed.", "Utah", "LA Lakers", "7:00 PM", "10:00 PM", "",
     "UTA@LAL", "uta-vs-lal", "10:00 PM ET", None, True, ""),
    (269, "2026-11-18", "Wed.", "Phoenix", "Sacramento", "7:00 PM", "10:00 PM", "",
     "PHX@SAC", "phx-vs-sac", "10:00 PM ET", None, True, ""),
    (270, "2026-11-19", "Thu.", "Golden State", "Memphis", "7:00 PM", "8:00 PM", "",
     None, "gsw-vs-mem", "8:00 PM ET", None, True, ""),
    (271, "2026-11-19", "Thu.", "Portland", "Milwaukee", "7:00 PM", "8:00 PM", "",
     None, "por-vs-mil", "8:00 PM ET", None, True, ""),
    (272, "2026-11-19", "Thu.", "New York", "Minnesota", "7:00 PM", "8:00 PM", "",
     None, "nyk-vs-min", "8:00 PM ET", None, True, ""),
    (273, "2026-11-19", "Thu.", "LA Clippers", "San Antonio", "7:00 PM", "8:00 PM", "",
     None, "lac-vs-sas", "8:00 PM ET", None, True, ""),
]


def build_slate():
    games = []
    for (row, date, weekday, away, home, local, et, tv, code, slug, gp_tip,
         tdis, at_token, note) in SLATE:
        g = {
            "row": row,
            "date": date,
            "weekday": weekday,
            "away": away,
            "home": home,
            "tip_et_col1": local,
            "tip_et_col2": et,
            "code": code,
            "code_source": "injury report 11/17 10:30 AM" if code else None,
            "games_page_slug": slug,
            "games_page_game_id": "00226002" + str(row - 200),
            "games_page_tip_et": gp_tip,
            "games_page_url": f"https://www.nba.com/game/{slug}-00226002{row - 200}",
            "order_corroborated_by": (
                [
                    "schedule PDF printed 'at' token (first cell = away, second = home)"
                    if at_token
                    else "schedule PDF printed order (first cell = away, per the "
                         "injury-report code where one exists)",
                ]
                + (["injury report matchup code AWAY@HOME (11/17 10:30 AM report)"]
                   if code else [])
                + ["games page URL slug 'away-vs-home'"]
            ),
            "tip_disagreement": tdis,
        }
        if at_token:
            g["at_token_printed"] = True
        if note:
            g["note"] = note
        games.append(g)
    return {
        "snapshot_id": "slate-2026-11-17",
        "kind": "official_schedule_rows",
        "source_url": SCHEDULE_URL,
        "source_document": "2026-27 NBA Regular Season Schedule By Date",
        "source_document_header": (
            "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE"
        ),
        "source_rows": "253-273",
        "fetched_at_utc": "2026-11-17T15:57:00Z",
        "extraction_tool": "fetch_page (PDF text extraction, chunks 1 and 2)",
        "window": {
            "start_utc": "2026-11-17T16:00:00Z",
            "end_utc": "2026-11-20T16:00:00Z",
            "rule": (
                "requested maximum horizon of 3 days from the observation time; games tipping "
                "off on or after 2026-11-20T16:00:00Z are outside the window"
            ),
        },
        "corroborating_urls": {
            "injury_report": R1030,
            "injury_index": INDEX_URL,
            "games_pages": (
                "https://www.nba.com/games?date=2026-11-17, "
                "https://www.nba.com/games?date=2026-11-18, "
                "https://www.nba.com/games?date=2026-11-19"
            ),
        },
        "basis": {
            "away_home_rule": (
                "The schedule PDF prints two team cells and, on rows 253-259, prints no 'at' or "
                "'vs' token between them. The away/home reading is therefore taken from the "
                "official injury report's matchup code (AWAY@HOME) when that report prints the "
                "same game, from the printed 'at' token where one exists (rows 260-273), and is "
                "otherwise corroborated by the games-page slug (away-vs-home) and left flagged."
            ),
            "games_this_window_with_injury_report_code": 17,
            "games_this_window_without_any_code": 4,
            "games_with_games_page_slug": 21,
            "games_order_corroborated": 21,
        },
        "games_page_corroboration": {
            "added_by": "session arena/0fec89b5-nba4 (pass 12, snapshot refresh)",
            "rows_with_games_page_slug": 21,
            "rows_where_id_equals_00226002_plus_schedule_row": 21,
            "rows_where_tip_matches_games_page": 17,
            "tip_disagreements_kept_as_printed": [256, 257, 266, 267],
            "rule": (
                "the schedule extraction published on main is the file of record; the games-page "
                "fields are added alongside it, and no printed value in it is overwritten"
            ),
        },
        "extraction_notes": [
            "The PDF text carries the column header \"LOCAL | ET\" (read 2026-11-17 from chunks 1 "
            "and 2 of the PDF text). The first time column (tip_et_col1) is the local tip time at "
            "the home venue and the second (tip_et_col2) is Eastern time. Checked for all 21 "
            "window rows: the Eastern value equals the home venue's local time converted to ET in "
            "21 of 21 rows. This is a consistency check against venue time zones, not a statement "
            "taken from the document; both values stay verbatim.",
            "The extracted PDF text prints no \"at\" token on rows 253-259 (11/17 to the first two "
            "11/18 rows) while rows 260 onward print \"at\"; re-confirmed on the 2026-11-17 fetch "
            "(matches the P7-02/AN-02 finding). Away/home order on rows 253-259 is therefore shown "
            "only where an independent source agrees: the 11/17 10:30 AM injury report prints "
            "matchup codes for all five 11/17 games and all twelve 11/18 games, and every one of "
            "the 21 window games has a games-page slug of the form away-vs-home. Rows 270-273 "
            "(11/19) are not listed by this report and rely on the printed 'at' token plus the "
            "slug; all four carry both.",
            "Four tips disagree between the August schedule PDF and the nba.com games pages: rows "
            "256 (schedule 10:00 PM ET / games page 11:00 PM ET), 257 (11:00 / 10:30), 266 (9:00 "
            "/ 9:30) and 267 (9:30 / 8:00). Both printed values are kept on the row; neither is "
            "overwritten (extends flags AN-02 and P9-04).",
            "Game ids follow the observed games-page pattern 00226002 + (schedule row - 200); "
            "checked on all 21 slugs read on 2026-11-17.",
            "No line, probability, pick or model output is present in this file.",
        ],
        "games": games,
    }


# ---------------------------------------------------------------- standings
# conf, seed, team, w, l, win_pct, gb, conf_rec, div_rec, home, road, neutral, ot, last10, streak
STANDINGS = [
    ("East", 1, "Philadelphia 76ers", 12, 3, ".800", "--", "12-3", "4-1", "6-2", "6-1", "0-0", "0-0", "8-2", "W 3"),
    ("East", 2, "Boston Celtics", 11, 3, ".786", "0.5", "10-2", "4-0", "6-1", "5-2", "0-0", "1-0", "8-2", "L 1"),
    ("East", 3, "Detroit Pistons", 8, 4, ".667", "2.5", "8-3", "0-0", "3-2", "5-2", "0-0", "1-0", "6-4", "L 1"),
    ("East", 4, "Miami Heat", 8, 6, ".571", "3.5", "4-2", "1-1", "4-3", "4-3", "0-0", "1-0", "8-2", "W 5"),
    ("East", 5, "Atlanta Hawks", 8, 6, ".571", "3.5", "8-2", "4-1", "3-3", "5-3", "0-0", "0-1", "6-4", "W 1"),
    ("East", 6, "New York Knicks", 7, 6, ".538", "4", "7-6", "2-3", "4-3", "3-3", "0-0", "1-0", "7-3", "W 1"),
    ("East", 7, "Cleveland Cavaliers", 8, 7, ".533", "4", "6-5", "2-0", "6-2", "2-5", "0-0", "1-0", "5-5", "W 2"),
    ("East", 8, "Orlando Magic", 6, 7, ".462", "5", "4-4", "0-2", "1-4", "5-3", "0-0", "0-1", "5-5", "W 4"),
    ("East", 9, "Toronto Raptors", 5, 8, ".385", "6", "4-4", "0-3", "2-4", "3-4", "0-0", "0-1", "3-7", "L 4"),
    ("East", 10, "Indiana Pacers", 5, 9, ".357", "6.5", "3-6", "0-1", "2-4", "3-4", "0-1", "0-0", "3-7", "L 1"),
    ("East", 11, "Charlotte Hornets", 4, 9, ".308", "7", "4-7", "2-2", "3-4", "1-5", "0-0", "0-0", "2-8", "L 2"),
    ("East", 12, "Washington Wizards", 4, 11, ".267", "8", "4-8", "2-3", "2-5", "2-6", "0-0", "0-1", "2-8", "L 8"),
    ("East", 13, "Brooklyn Nets", 3, 10, ".231", "8", "2-8", "0-3", "1-4", "2-6", "0-0", "0-1", "3-7", "L 2"),
    ("East", 14, "Chicago Bulls", 3, 10, ".231", "8", "2-9", "1-1", "1-4", "2-6", "0-0", "1-0", "2-8", "L 1"),
    ("East", 15, "Milwaukee Bucks", 1, 13, ".071", "10.5", "1-10", "1-2", "1-7", "0-6", "0-0", "0-0", "0-10", "L 10"),
    ("West", 1, "San Antonio Spurs", 12, 2, ".857", "--", "11-2", "2-1", "5-2", "7-0", "0-0", "1-0", "10-0", "W 12"),
    ("West", 2, "Los Angeles Lakers", 12, 2, ".857", "--", "7-2", "5-1", "5-1", "7-1", "0-0", "0-0", "9-1", "W 8"),
    ("West", 3, "Houston Rockets", 11, 4, ".733", "1.5", "6-3", "2-1", "7-1", "4-3", "0-0", "0-0", "6-4", "L 1"),
    ("West", 4, "Minnesota Timberwolves", 10, 4, ".714", "2", "6-2", "2-0", "6-2", "4-2", "0-0", "0-1", "7-3", "W 1"),
    ("West", 5, "Memphis Grizzlies", 10, 4, ".714", "2", "7-3", "1-1", "3-4", "7-0", "0-0", "0-1", "6-4", "W 3"),
    ("West", 6, "Portland Trail Blazers", 9, 4, ".692", "2.5", "9-4", "4-1", "3-2", "6-2", "0-0", "0-0", "6-4", "L 1"),
    ("West", 7, "Oklahoma City Thunder", 9, 5, ".643", "3", "6-5", "1-2", "5-0", "4-5", "0-0", "0-0", "5-5", "W 1"),
    ("West", 8, "Denver Nuggets", 7, 5, ".583", "4", "5-5", "0-2", "2-3", "4-2", "1-0", "1-0", "6-4", "L 1"),
    ("West", 9, "Golden State Warriors", 8, 6, ".571", "4", "6-6", "3-2", "6-1", "2-5", "0-0", "1-0", "7-3", "L 3"),
    ("West", 10, "Dallas Mavericks", 7, 7, ".500", "5", "3-5", "1-3", "5-2", "2-5", "0-0", "0-0", "5-5", "L 3"),
    ("West", 11, "Phoenix Suns", 6, 7, ".462", "5.5", "4-7", "2-2", "5-4", "1-3", "0-0", "0-0", "5-5", "W 1"),
    ("West", 12, "LA Clippers", 4, 8, ".333", "7", "3-6", "1-4", "4-3", "0-5", "0-0", "0-1", "3-7", "W 2"),
    ("West", 13, "New Orleans Pelicans", 5, 10, ".333", "7.5", "4-8", "1-1", "4-6", "1-4", "0-0", "2-1", "4-6", "W 1"),
    ("West", 14, "Sacramento Kings", 1, 12, ".077", "10.5", "1-10", "0-2", "0-8", "1-4", "0-0", "0-0", "1-9", "L 6"),
    ("West", 15, "Utah Jazz", 1, 13, ".071", "11", "1-11", "0-2", "1-7", "0-6", "0-0", "0-2", "0-10", "L 12"),
]


def _split(rec: str) -> tuple[int, int]:
    a, b = rec.split("-")
    return int(a), int(b)


def build_standings():
    rows = []
    hw = hl = rw = rl = nw = nl = tw = tl = 0
    home_games = road_games = neutral_games = 0
    last10_bad = []
    split_bad = []
    for conf, seed, team, w, l, pct, gb, conf_rec, div_rec, home, road, neutral, ot, last10, streak in STANDINGS:
        hg, hl_ = _split(home)
        rg, rl_ = _split(road)
        ng, nl_ = _split(neutral)
        hw, hl = hw + hg, hl + hl_
        rw, rl = rw + rg, rl + rl_
        nw, nl = nw + ng, nl + nl_
        tw, tl = tw + w, tl + l
        gp = w + l
        home_games += hg + hl_
        road_games += rg + rl_
        neutral_games += ng + nl_
        split_sum = (hg + hl_) + (rg + rl_) + (ng + nl_)
        l10w, l10l = _split(last10)
        l10_games = l10w + l10l
        if split_sum != gp:
            split_bad.append(team)
        if l10_games != 10 and l10_games != gp:
            last10_bad.append(team)
        rows.append({
            "conf": conf, "seed": seed, "team": team, "w": w, "l": l,
            "win_pct": pct, "gb": gb, "conf_rec": conf_rec, "div_rec": div_rec,
            "home": home, "road": road, "neutral": neutral, "ot": ot,
            "last10": last10, "streak": streak,
            "games_played_from_w_plus_l": gp,
            "home_games": hg + hl_, "road_games": rg + rl_, "neutral_games": ng + nl_,
            "split_sum": split_sum, "split_sum_equals_gp": split_sum == gp,
            "last10_games": l10_games,
            "last10_matches_gp_rule": l10_games == 10 or l10_games == gp,
        })
    league_lines = tw + tl
    return {
        "snapshot_id": "standings-2026-11-17",
        "kind": "official_standings_page",
        "source_url": "https://www.nba.com/standings",
        "source_document": "NBA 2026-27 Regular Season Standings",
        "source_document_header": "NBA 2026-27 Regular Season Standings (as printed on the standings page)",
        "source_page_title": "NBA Team Standings & Stats | NBA.com",
        "fetched_at_utc": "2026-11-17T16:03:00Z",
        "extraction_tool": "fetch_page (web page extraction, chunks 0 and 1)",
        "column_header_as_printed": "Team | w | L | WIN% | GB | CONF | DIV | HOME | ROAD | Neutral | OT | LAST10 | STREAK",
        "column_note": "HOME, ROAD and Neutral are the page's own split columns (record as printed, wins-losses).",
        "extraction_notes": [
            "Verbatim transcription of the standings page as read on 2026-11-17. The page reflects "
            "completed games through 2026-11-16 (all eight finals of that day are included: e.g. "
            "Orlando 6-7 after winning at Boston, the Celtics' first home loss, and Denver 7-5 "
            "after losing at home to Phoenix).",
            "Split records are printed as wins-losses; the derived fields on each row "
            "(games_played_from_w_plus_l, home_games, road_games, neutral_games, split_sum, "
            "last10 checks) are arithmetic on the printed cells, not new information.",
            "No ranking, rating, projection or pick is derived from this table here.",
        ],
        "consistency_checks": {
            "league_team_game_lines": league_lines,
            "league_home_games": home_games,
            "league_road_games": road_games,
            "league_neutral_games": neutral_games,
            "splits_sum_to_league_team_game_lines": (
                home_games + road_games + neutral_games == league_lines
            ),
            "formula": (
                "sum(HOME games)+sum(ROAD games)+sum(NEUTRAL games) must equal the number of "
                "team-game lines; each game prints one line for each team."
            ),
            "rows_where_home_road_neutral_do_not_sum_to_games": split_bad,
            "league_wins": tw,
            "league_losses": tl,
            "wins_equal_losses": tw == tl,
            "last10_rows_where_games_in_last10_neither_10_nor_gp": last10_bad,
            "last10_anomalies": last10_bad,
            "note": (
                "One game prints one HOME line for the home team and one ROAD line for the "
                "visitor (both NEUTRAL at a neutral site), so the league HOME+ROAD+NEUTRAL game "
                "counts must equal the number of team-game lines and league wins must equal "
                "league losses."
            ),
        },
        "rows": rows,
        "derived_checks": {
            "home_wins": hw, "home_losses": hl, "home_games": hw + hl,
            "road_wins": rw, "road_losses": rl, "road_games": rw + rl,
            "neutral_wins": nw, "neutral_losses": nl, "neutral_games": nw + nl,
        },
    }


# ---------------------------------------------------------------- results 11/16
RESULTS = [
    ["0022600245", "2026-11-16", "7:00 PM", "TD Garden", "Boston, MA", "ORL", "BOS",
     [20, 30, 25, 40], 115, [17, 24, 36, 28], 105, "ORL", "BOS",
     "https://www.nba.com/game/orl-vs-bos-0022600245"],
    ["0022600246", "2026-11-16", "7:00 PM", "Rocket Arena", "Cleveland, OH", "CHI", "CLE",
     [31, 17, 31, 36], 115, [25, 32, 31, 38], 126, "CLE", "CHI",
     "https://www.nba.com/game/chi-vs-cle-0022600246"],
    ["0022600247", "2026-11-16", "7:00 PM", "Capital One Arena", "Washington, DC", "MEM", "WAS",
     [33, 26, 42, 35], 136, [35, 34, 18, 33], 120, "MEM", "WAS",
     "https://www.nba.com/game/mem-vs-was-0022600247"],
    ["0022600248", "2026-11-16", "7:30 PM", "Barclays Center", "Brooklyn, NY", "PHI", "BKN",
     [33, 45, 27, 30], 135, [26, 33, 36, 28], 123, "PHI", "BKN",
     "https://www.nba.com/game/phi-vs-bkn-0022600248"],
    ["0022600249", "2026-11-16", "7:30 PM", "Kaseya Center", "Miami, FL", "HOU", "MIA",
     [15, 31, 35, 29], 110, [29, 33, 39, 27], 128, "MIA", "HOU",
     "https://www.nba.com/game/hou-vs-mia-0022600249"],
    ["0022600250", "2026-11-16", "8:00 PM", "Target Center", "Minneapolis, MN", "POR", "MIN",
     [26, 25, 22, 25], 98, [26, 33, 28, 19], 106, "MIN", "POR",
     "https://www.nba.com/game/por-vs-min-0022600250"],
    ["0022600251", "2026-11-16", "8:00 PM", "Smoothie King Center", "New Orleans, LA", "GSW", "NOP",
     [11, 25, 29, 29], 94, [35, 26, 32, 22], 115, "NOP", "GSW",
     "https://www.nba.com/game/gsw-vs-nop-0022600251"],
    ["0022600252", "2026-11-16", "9:00 PM", "Ball Arena", "Denver, CO", "PHX", "DEN",
     [20, 36, 34, 27], 117, [24, 29, 29, 23], 105, "PHX", "DEN",
     "https://www.nba.com/game/phx-vs-den-0022600252"],
]


def build_results():
    checks = []
    bad = 0
    for row in RESULTS:
        (gid, date, tip, arena, city, away, home, aq, af, hq, hf, win, lose, url) = row
        for abbr, qs, final in ((away, aq, af), (home, hq, hf)):
            agrees = sum(qs) == final
            bad += not agrees
            checks.append([gid, abbr, *qs, final, agrees])
    return {
        "snapshot_id": "results-2026-11-16",
        "kind": "official_finals_observation",
        "source_document": "NBA game summary pages for 2026-11-16",
        "source_document_header": (
            "Game Summary (LINESCORES + GAME INFO) as printed on each official NBA game page"
        ),
        "source_url": "https://www.nba.com/games?date=2026-11-16",
        "source_index_url": "https://www.nba.com/games",
        "fetched_at_utc": "2026-11-17T16:04:00Z",
        "extraction_tool": (
            "fetch_page (web page extraction; one game page per game, LINESCORES + GAME INFO)"
        ),
        "row_format": [
            "game_id", "date", "tip_et", "arena", "city", "away", "home",
            "away_q", "away_final", "home_q", "home_final", "winner", "loser",
            "source_url",
        ],
        "row_format_note": (
            "away_q/home_q hold every period score the page printed: four quarters, and the "
            "overtime period for games that went to OT (no 11/16 game printed an OT column). "
            "The tip is the Eastern-time value the game page prints; arena and city are the "
            "GAME INFO values."
        ),
        "verification": {
            "quarter_sum_rule": (
                "For every row the printed period scores (four quarters, plus any overtime "
                "periods) were added and compared with the printed Final. "
                f"{len(checks) - bad} of {len(checks)} team lines agree, so every row is "
                "SETTLEMENT_ELIGIBLE."
            ),
            "quarter_sum_check": checks,
            "settlement_eligible": bad == 0,
            "games": len(RESULTS),
            "team_lines_checked": len(checks),
            "lines_that_disagree": bad,
            "overtime_games": [],
        },
        "extraction_notes": [
            "Official observation of the printed final, quarter by quarter, retrieved on "
            "2026-11-17 after the last game of 2026-11-16 had ended. This is not a live feed "
            "and carries no game-end clock; no end time is invented.",
            "Every team line's printed periods add to the printed final, so all eight games are "
            "settlement-eligible under the rule stated in verification.quarter_sum_rule.",
            "Cross-check: the eight winners and losers above move the standings page read at "
            "2026-11-17T16:03Z exactly as printed (e.g. Orlando 6-7, Boston 11-3, Denver 7-5, "
            "Phoenix 6-7); no standings cell contradicts these results.",
            "No pick, probability, odds or model output is present in this file.",
        ],
        "rows": RESULTS,
    }


# ---------------------------------------------------------------- rest window
def build_rest():
    prev = json.loads((SNAP / "rest-window-2026-11-16.json").read_text(encoding="utf-8"))
    # rows dated 11/10 through 11/18 are re-read unchanged from the schedule PDF chunks
    # fetched in this session (chunks 1 and 2) and kept; the four 11/19 rows are new.
    kept = [r for r in prev["rows"] if r["date"] <= "2026-11-18"]
    new_rows = [
        {"row": 270, "date": "2026-11-19", "weekday": "Thu.", "away": "Golden State",
         "home": "Memphis", "tip_et": "7:00 PM", "at_token_printed": True, "at_token": "at"},
        {"row": 271, "date": "2026-11-19", "weekday": "Thu.", "away": "Portland",
         "home": "Milwaukee", "tip_et": "7:00 PM", "at_token_printed": True, "at_token": "at"},
        {"row": 272, "date": "2026-11-19", "weekday": "Thu.", "away": "New York",
         "home": "Minnesota", "tip_et": "7:00 PM", "at_token_printed": True, "at_token": "at"},
        {"row": 273, "date": "2026-11-19", "weekday": "Thu.", "away": "LA Clippers",
         "home": "San Antonio", "tip_et": "7:00 PM", "at_token_printed": True, "at_token": "at"},
    ]
    rows = kept + new_rows
    return {
        "snapshot_id": "rest-window-2026-11-17",
        "kind": "official_schedule_rows",
        "source_url": SCHEDULE_URL,
        "source_document": "2026-27 NBA Regular Season Schedule By Date",
        "source_document_header": (
            "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE"
        ),
        "source_rows": "34-42, 211-273 (dates 2026-11-10 through 2026-11-19)",
        "fetched_at_utc": "2026-11-17T15:57:00Z",
        "extraction_tool": "fetch_page (PDF text extraction, chunks 1 and 2)",
        "coverage": {
            "first_date": "2026-11-10",
            "last_date": "2026-11-19",
            "rule": (
                "rest, back-to-back and 3-in-4 are computed only from rows in this window; a "
                "team whose prior game falls before 2026-11-10 would be published as uncovered, "
                "never as rested"
            ),
        },
        "rows": rows,
        "extraction_notes": [
            "Rows 211-269 were re-read from schedule PDF chunks 1 and 2 on 2026-11-17 and match "
            "the rows already published for the 11/16 cycle; rows 270-273 (11/19) are newly "
            "transcribed from chunk 2. Rows 34-42 are the 11/13 in-season-tournament window "
            "rows kept from the previous window file.",
            "No rest, back-to-back or 3-in-4 value is stored in this file; the values are "
            "computed by engine/rest.py at render time from these dates only.",
        ],
    }


# ---------------------------------------------------------------- pointer
def build_pointer():
    return {
        "snapshot_id": "injuries-newest-pointer-2026-11-17",
        "kind": "official_report_pointer_metadata_only",
        "source_url": R1030,
        "source_document_header": "Injury Report: 11/17/26 10:30 AM",
        "fetched_at_utc": "2026-11-17T15:52:00Z",
        "extraction_tool": (
            "fetch_page (PDF text extraction); the index was read through fetch_page as well"
        ),
        "purpose": (
            "Records the state of the official injury-report index at the 2026-11-17 refresh "
            "check: the 10:30 AM ET report was the newest listed at the check time, and its "
            "full row-level transcription is stored in injuries-2026-11-17-1030am.json. It "
            "stores no player rows, statuses, minutes, probabilities or picks itself."
        ),
        "source_index_url": INDEX_URL,
        "source_index_title": "NBA Injury Report: 2026-27 Season | NBA Official",
        "index_entries_seen_nov_17": (
            "12:00 a.m. through 10:30 a.m. ET, every 15 minutes (43 entries)"
        ),
        "newest_listed": "10:30 a.m ET report",
        "checked_at_utc": "2026-11-17T15:52:00Z",
    }


def write(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    d1030 = build_report("11/17/26 10:30 AM", R1030, FETCHED_1030,
                         "injuries-2026-11-17-1030am")
    write(SNAP / "injuries-2026-11-17-1030am.json", d1030)
    d1015 = build_report("11/17/26 10:15 AM", R1015, FETCHED_1015,
                         "injuries-2026-11-17-1015am")
    write(SNAP / "injuries-2026-11-17-1015am.json", d1015)

    write_pipes(RAW / "injury-2026-11-17T1030am-et.pipes", "11/17/26 10:30 AM",
                R1030, FETCHED_1030)
    write_pipes(RAW / "injury-2026-11-17T1015am-et.pipes", "11/17/26 10:15 AM",
                R1015, FETCHED_1015)

    write(SNAP / "slate-2026-11-17.json", build_slate())
    write(SNAP / "standings-2026-11-17.json", build_standings())
    write(SNAP / "results-2026-11-16.json", build_results())
    write(SNAP / "rest-window-2026-11-17.json", build_rest())
    write(SNAP / "injuries-newest-pointer-2026-11-17.json", build_pointer())

    # sanity: row counts and quarter sums
    assert d1030["row_count"] == 59, d1030["row_count"]
    assert d1015["row_count"] == 59, d1015["row_count"]
    for row in RESULTS:
        assert sum(row[7]) == row[8], row[0]
        assert sum(row[9]) == row[10], row[0]
    st = build_standings()
    cc = st["consistency_checks"]
    assert cc["wins_equal_losses"] and cc["splits_sum_to_league_team_game_lines"], cc
    assert not cc["rows_where_home_road_neutral_do_not_sum_to_games"]
    assert not cc["last10_rows_where_games_in_last10_neither_10_nor_gp"]
    print(
        "wrote snapshots: injuries", d1030["row_count"], "rows x2;",
        "slate", len(build_slate()["games"]), "games;",
        "standings", len(st["rows"]), "rows;",
        "results", len(RESULTS), "games;",
        "rest", len(build_rest()["rows"]), "rows;",
        "home rate", st["derived_checks"]["home_wins"], "-",
        st["derived_checks"]["home_losses"], "over", st["derived_checks"]["home_games"],
    )


if __name__ == "__main__":
    main()
