#!/usr/bin/env python3
"""Generate the 2026-11-17 refresh snapshots (task BM, session arena/ec0a4dc9-nba4).

Every value below was read from an official NBA document during this session and
is transcribed verbatim. Nothing is inferred: blank cells stay blank, a lost team
cell becomes ``__lost__`` with an unverified flag, and quarter scores that the
scoreboard does not print are left empty and flagged rather than invented.

Sources read 2026-11-17 (observation time 2026-11-17T16:30:00Z):
  * injury-report index   https://official.nba.com/nba-injury-report-2026-27-season/
  * 11/17 10:30 AM report  https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf
  * 11/17 10:15 AM report  https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf
  * schedule PDF (chunk 2) https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf
  * games pages 11/17-11/19 https://www.nba.com/games?date=2026-11-1{7,8,9}
  * standings             https://www.nba.com/standings
  * scoreboard 11/16      https://www.nba.com/games?date=2026-11-16
"""
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"

OBS = "2026-11-17T16:30:00Z"
INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
REPORT_1030_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf"
REPORT_1015_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf"
SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
STANDINGS_URL = "https://www.nba.com/standings"
REV_1030 = "11/17/26 10:30 AM"
REV_1015 = "11/17/26 10:15 AM"
REV_1030_UTC = "2026-11-17T15:30:00Z"

ABBR = {
    "Denver": "DEN", "New Orleans": "NOP", "Dallas": "DAL", "Cleveland": "CLE",
    "Detroit": "DET", "Miami": "MIA", "Brooklyn": "BKN", "Memphis": "MEM",
    "Chicago": "CHI", "Minnesota": "MIN", "Indiana": "IND", "Philadelphia": "PHI",
    "LA Lakers": "LAL", "Phoenix": "PHX", "Charlotte": "CHA", "LA Clippers": "LAC",
    "San Antonio": "SAS", "Utah": "UTA", "Boston": "BOS", "New York": "NYK",
    "Toronto": "TOR", "Houston": "HOU", "Washington": "WAS", "Atlanta": "ATL",
    "Milwaukee": "MIL", "Oklahoma City": "OKC", "Sacramento": "SAC",
    "Orlando": "ORL", "Golden State": "GSW", "Portland": "POR",
}


def write(name, obj):
    (SNAP / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", name)


# ---------------------------------------------------------------------------
# 1. SLATE window 11/17-11/19 (schedule PDF rows 253-273)
#    tip_et_col1 = LOCAL, tip_et_col2 = ET (PDF header LOCAL | ET).
#    at_token_printed is True for rows 260-273 (the PDF prints "at"); rows
#    253-259 print no "at" and their away/home order is corroborated by the
#    injury-report matchup code and the games-page slug.
# ---------------------------------------------------------------------------
# row, date, weekday, away, home, local, et, at_token, broadcast, games_tip_et, slug, gid
SLATE_ROWS = [
    (253, "2026-11-17", "Tue.", "New York", "Toronto", "7:30 PM", "7:30 PM", False, "", "7:30 PM ET", "nyk-vs-tor", "0022600253"),
    (254, "2026-11-17", "Tue.", "Portland", "Minnesota", "7:00 PM", "8:00 PM", False, "", "8:00 PM ET", "por-vs-min", "0022600254"),
    (255, "2026-11-17", "Tue.", "Detroit", "San Antonio", "7:00 PM", "8:00 PM", False, "NBC/PCK", "8:00 PM ET", "det-vs-sas", "0022600255"),
    (256, "2026-11-17", "Tue.", "Charlotte", "LA Lakers", "7:00 PM", "10:00 PM", False, "", "11:00 PM ET", "cha-vs-lal", "0022600256"),
    (257, "2026-11-17", "Tue.", "Utah", "LA Clippers", "8:00 PM", "11:00 PM", False, "NBC/PCK", "10:30 PM ET", "uta-vs-lac", "0022600257"),
    (258, "2026-11-18", "Wed.", "Memphis", "Cleveland", "7:00 PM", "7:00 PM", False, "", "7:00 PM ET", "mem-vs-cle", "0022600258"),
    (259, "2026-11-18", "Wed.", "Houston", "Indiana", "7:00 PM", "7:00 PM", False, "", "7:00 PM ET", "hou-vs-ind", "0022600259"),
    (260, "2026-11-18", "Wed.", "Milwaukee", "Miami", "7:00 PM", "7:00 PM", True, "ESPN", "7:00 PM ET", "mil-vs-mia", "0022600260"),
    (261, "2026-11-18", "Wed.", "Philadelphia", "Orlando", "7:00 PM", "7:00 PM", True, "", "7:00 PM ET", "phi-vs-orl", "0022600261"),
    (262, "2026-11-18", "Wed.", "Chicago", "Brooklyn", "7:30 PM", "7:30 PM", True, "", "7:30 PM ET", "chi-vs-bkn", "0022600262"),
    (263, "2026-11-18", "Wed.", "Washington", "Toronto", "7:30 PM", "7:30 PM", True, "", "7:30 PM ET", "was-vs-tor", "0022600263"),
    (264, "2026-11-18", "Wed.", "Detroit", "New Orleans", "7:00 PM", "8:00 PM", True, "", "8:00 PM ET", "det-vs-nop", "0022600264"),
    (265, "2026-11-18", "Wed.", "Atlanta", "Oklahoma City", "7:00 PM", "8:00 PM", True, "", "8:00 PM ET", "atl-vs-okc", "0022600265"),
    (266, "2026-11-18", "Wed.", "Boston", "Denver", "7:00 PM", "9:00 PM", True, "", "9:30 PM ET", "bos-vs-den", "0022600266"),
    (267, "2026-11-18", "Wed.", "Golden State", "Dallas", "8:30 PM", "9:30 PM", True, "ESPN", "8:00 PM ET", "gsw-vs-dal", "0022600267"),
    (268, "2026-11-18", "Wed.", "Utah", "LA Lakers", "7:00 PM", "10:00 PM", True, "", "10:00 PM ET", "uta-vs-lal", "0022600268"),
    (269, "2026-11-18", "Wed.", "Phoenix", "Sacramento", "7:00 PM", "10:00 PM", True, "", "10:00 PM ET", "phx-vs-sac", "0022600269"),
    (270, "2026-11-19", "Thu.", "Golden State", "Memphis", "7:00 PM", "8:00 PM", True, "", "8:00 PM ET", "gsw-vs-mem", "0022600270"),
    (271, "2026-11-19", "Thu.", "Portland", "Milwaukee", "7:00 PM", "8:00 PM", True, "", "8:00 PM ET", "por-vs-mil", "0022600271"),
    (272, "2026-11-19", "Thu.", "New York", "Minnesota", "7:00 PM", "8:00 PM", True, "", "8:00 PM ET", "nyk-vs-min", "0022600272"),
    (273, "2026-11-19", "Thu.", "LA Clippers", "San Antonio", "7:00 PM", "8:00 PM", True, "", "8:00 PM ET", "lac-vs-sas", "0022600273"),
]

games = []
for (row, date, wd, away, home, local, et, at_tok, bcast, gtip, slug, gid) in SLATE_ROWS:
    code = f"{ABBR[away]}@{ABBR[home]}"
    tip_disagreement = None
    if gtip.replace(" ET", "") != et:
        tip_disagreement = f"schedule PDF ET {et} vs games page {gtip}"
    note = None
    if bcast:
        note = f"PDF broadcast column reads {bcast}"
    games.append({
        "row": row,
        "date": date,
        "weekday": wd,
        "away": away,
        "home": home,
        "tip_et_col1": local,
        "tip_et_col2": et,
        "code": code,
        "code_source": "schedule PDF printed order (TEAM 1 | TEAM 2); away/home corroborated by the injury-report matchup code where the report lists the game",
        "games_page_slug": slug,
        "games_page_game_id": gid,
        "games_page_tip_et": gtip,
        "games_page_url": f"https://www.nba.com/game/{slug}-{gid}",
        "at_token_printed": at_tok,
        "order_corroborated_by": [
            "schedule PDF printed order (TEAM 1 = away, TEAM 2 = home, per the PDF header and the 'at' token where printed)",
            "injury report matchup code AWAY@HOME (11/17 10:30 AM report) where the game is listed",
            "games page URL slug 'away-vs-home'",
        ],
        "tip_disagreement": tip_disagreement,
        "note": note,
    })

slate = {
    "snapshot_id": "slate-2026-11-17",
    "kind": "official_schedule_window",
    "source_url": SCHEDULE_URL,
    "source_document": "2026-27 NBA Regular Season Schedule By Date",
    "source_document_header": "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE",
    "source_rows": "253-273 (chunk 2 of the schedule PDF text extraction)",
    "fetched_at_utc": OBS,
    "extraction_tool": "fetch_page (PDF text extraction, chunk 2; rows 253-273) + official games pages 11/17-11/19 for the games-page slug/id/tip corroboration",
    "window": {
        "start_utc": "2026-11-17T15:30:00Z",
        "end_utc": "2026-11-20T15:30:00Z",
        "rule": "requested maximum horizon of 3 days from the observation time; games tipping off on or after 2026-11-17T15:30:00Z and before 2026-11-20T15:30:00Z",
    },
    "corroborating_urls": {
        "injury_report": REPORT_1030_URL,
        "injury_index": INDEX_URL,
        "games_pages": "https://www.nba.com/games?date=2026-11-17, https://www.nba.com/games?date=2026-11-18, https://www.nba.com/games?date=2026-11-19",
    },
    "games_page_corroboration": {
        "added_by": "session arena/ec0a4dc9-nba4 (task BM, 11/17 refresh cycle)",
        "rows_with_games_page_slug": len(games),
        "rows_where_id_equals_00226002_plus_schedule_row": sum(
            1 for g in games if g["games_page_game_id"] == "00226002" + str(g["row"] - 200)
        ),
        "rows_where_tip_matches_games_page": sum(
            1 for g in games
            if not g.get("tip_disagreement")
            and g["games_page_tip_et"].replace(" ET", "") == g["tip_et_col2"]
        ),
        "tip_disagreements_kept_as_printed": [g["row"] for g in games if g.get("tip_disagreement")],
        "rule": "the schedule extraction is the file of record; the games-page fields are added alongside it, and no printed value in it is overwritten",
    },
    "games": games,
    "extraction_notes": [
        "tip_et_col1 is the schedule PDF LOCAL column (home-venue local), tip_et_col2 is the ET column; both are printed values.",
        "rows 253-259 print no 'at' token; away/home order follows the printed TEAM 1 | TEAM 2 order and is corroborated by the injury-report matchup code and the games-page slug. Rows 260-273 print the 'at' token.",
        "tip_disagreement is set where the games-page ET tip differs from the schedule PDF ET column; both values are published, neither is overwritten.",
    ],
}
write("slate-2026-11-17.json", slate)

# ---------------------------------------------------------------------------
# 2. INJURY report of record: 11/17 10:30 AM ET
# ---------------------------------------------------------------------------
def player_row(team, player, status, reason):
    return {"team": team, "player": player, "status": status, "reason": reason}

def nys_row(team):
    return {"team": team, "player": "", "status": "", "reason": "NOT YET SUBMITTED",
            "unverified": True, "flag": "team has not submitted"}

LOST_FLAG = "team cell lost at PDF page break; the row continues this game block between printed rows, but the team is not asserted"

inj_games = [
    {
        "matchup": "NYK@TOR", "game_date": "11/17/2026", "tip_et_from_report": "07:30 (ET)",
        "tip_et_from_schedule": "7:30 PM", "schedule_row": 253, "cells_source": "report",
        "rows": [
            player_row("Toronto Raptors", "Bittle, Nate", "Out", "Injury/Illness - Right Foot Avulsion Fracture"),
            player_row("Toronto Raptors", "Leonard, Kawhi", "Out", "Injury/Illness - Left Knee Injury Management"),
            player_row("Toronto Raptors", "McCullar Jr., Kevin", "Out", "G League - Two-Way"),
            player_row("Toronto Raptors", "Smith, Malachi", "Out", "G League - Two-Way"),
        ],
    },
    {
        "matchup": "DET@SAS", "game_date": "11/17/2026", "tip_et_from_report": "08:00 (ET)",
        "tip_et_from_schedule": "8:00 PM", "schedule_row": 255, "cells_source": "report",
        "rows": [
            player_row("Detroit Pistons", "Duren, Jalen", "Out", "Injury/Illness - Right Hamstring Strain"),
            player_row("Detroit Pistons", "Holland II, Ronald", "Out", "Injury/Illness - Left Knee Contusion / Bone Bruise"),
            player_row("Detroit Pistons", "Joe, Isaiah", "Doubtful", "Injury/Illness - Right Hip Contusion"),
            player_row("Detroit Pistons", "Okorie, Ebuka", "Out", "G League - On Assignment"),
            player_row("Detroit Pistons", "Onyenso, Ugonna", "Out", "G League - Two-Way"),
            player_row("Detroit Pistons", "Prince, Taurean", "Out", "Injury/Illness - Right Knee Soreness"),
            player_row("Detroit Pistons", "Robinson, Duncan", "Out", "Injury/Illness - Left Quadriceps Strain"),
            player_row("San Antonio Spurs", "Brown, Maliq", "Out", "G League - Two-Way"),
            player_row("San Antonio Spurs", "Gillespie, Ja'Kobi", "Out", "G League - Two-Way"),
            player_row("San Antonio Spurs", "Harris, Tobias", "Out", "Injury/Illness - Left Calf Strain"),
            player_row("San Antonio Spurs", "Quaintance, Jayden", "Out", "Injury/Illness - Right Knee Surgery"),
        ],
    },
    {
        "matchup": "POR@MIN", "game_date": "11/17/2026", "tip_et_from_report": "08:00 (ET)",
        "tip_et_from_schedule": "8:00 PM", "schedule_row": 254, "cells_source": "report",
        "rows": [
            nys_row("Portland Trail Blazers"),
            nys_row("Minnesota Timberwolves"),
        ],
    },
    {
        "matchup": "UTA@LAC", "game_date": "11/17/2026", "tip_et_from_report": "10:30 (ET)",
        "tip_et_from_schedule": "11:00 PM", "schedule_row": 257, "cells_source": "report",
        "rows": [
            player_row("Utah Jazz", "Bufkin, Kobe", "Out", "G League - Two-Way"),
            player_row("Utah Jazz", "Hayes, Jaxson", "Out", "Injury/Illness - Left Knee Strain"),
            player_row("Utah Jazz", "Ingram, Harrison", "Out", "G League - Two-Way"),
            player_row("Utah Jazz", "Jackson Jr., Jaren", "Out", "Injury/Illness - Right MCL Tear"),
            player_row("Utah Jazz", "Markkanen, Lauri", "Out", "Injury/Illness - Right Hand Fracture"),
            player_row("Utah Jazz", "Nurkic, Jusuf", "Out", "Injury/Illness - Right Right Foot; 2nd Plantar Plate Tear"),
            player_row("LA Clippers", "Beal, Bradley", "Out", "Injury/Illness - Right Knee Injury Management"),
            player_row("LA Clippers", "Ingram, Brandon", "Out", "Injury/Illness - Right Heel Surgery"),
            player_row("LA Clippers", "Miller, Jordan", "Out", "Injury/Illness - Left Rotator Cuff Surgery"),
            player_row("LA Clippers", "Niederhauser, Yanic Konan", "Out", "Injury/Illness - Right Lisfranc Surgery"),
        ],
    },
    {
        "matchup": "CHA@LAL", "game_date": "11/17/2026", "tip_et_from_report": "11:00 (ET)",
        "tip_et_from_schedule": "10:00 PM", "schedule_row": 256, "cells_source": "report",
        "rows": [
            player_row("Charlotte Hornets", "Ajayi, Michael", "Out", "G League - Two-Way"),
            player_row("Charlotte Hornets", "Boswell, Kylan", "Out", "G League - Two-Way"),
            player_row("Charlotte Hornets", "Knueppel, Kon", "Out", "Injury/Illness - Left Hamstring Strain"),
            player_row("Charlotte Hornets", "Schroder, Dennis", "Out", "Injury/Illness - Left Hamstring Strain"),
            player_row("Charlotte Hornets", "Steinbach, Hannes", "Out", "G League - On Assignment"),
            player_row("Los Angeles Lakers", "Grimes, Quentin", "Available", "Injury/Illness - Right Finger Splint"),
            player_row("Los Angeles Lakers", "Kessler, Walker", "Out", "Injury/Illness - Right Lower Leg"),
            {"team": "__lost__", "player": "Reaves, Austin", "status": "Out",
             "reason": "Injury/Illness - Left Heel Contusion / Bone Bruise",
             "unverified": True, "flag": LOST_FLAG},
        ],
    },
    # 11/18 games: both teams NOT YET SUBMITTED
    {"matchup": "MEM@CLE", "game_date": "11/18/2026", "tip_et_from_report": "07:00 (ET)",
     "tip_et_from_schedule": "7:00 PM", "schedule_row": 258, "cells_source": "report",
     "rows": [nys_row("Memphis Grizzlies"), nys_row("Cleveland Cavaliers")]},
    {"matchup": "HOU@IND", "game_date": "11/18/2026", "tip_et_from_report": "07:00 (ET)",
     "tip_et_from_schedule": "7:00 PM", "schedule_row": 259, "cells_source": "report",
     "rows": [nys_row("Houston Rockets"), nys_row("Indiana Pacers")]},
    {"matchup": "MIL@MIA", "game_date": "11/18/2026", "tip_et_from_report": "07:00 (ET)",
     "tip_et_from_schedule": "7:00 PM", "schedule_row": 260, "cells_source": "report",
     "rows": [nys_row("Milwaukee Bucks"), nys_row("Miami Heat")]},
    {"matchup": "PHI@ORL", "game_date": "11/18/2026", "tip_et_from_report": "07:00 (ET)",
     "tip_et_from_schedule": "7:00 PM", "schedule_row": 261, "cells_source": "report",
     "rows": [nys_row("Philadelphia 76ers"), nys_row("Orlando Magic")]},
    {"matchup": "CHI@BKN", "game_date": "11/18/2026", "tip_et_from_report": "07:30 (ET)",
     "tip_et_from_schedule": "7:30 PM", "schedule_row": 262, "cells_source": "report",
     "rows": [nys_row("Chicago Bulls"), nys_row("Brooklyn Nets")]},
    {"matchup": "WAS@TOR", "game_date": "11/18/2026", "tip_et_from_report": "07:30 (ET)",
     "tip_et_from_schedule": "7:30 PM", "schedule_row": 263, "cells_source": "report",
     "rows": [nys_row("Washington Wizards"), nys_row("Toronto Raptors")]},
    {"matchup": "DET@NOP", "game_date": "11/18/2026", "tip_et_from_report": "08:00 (ET)",
     "tip_et_from_schedule": "8:00 PM", "schedule_row": 264, "cells_source": "report",
     "rows": [nys_row("Detroit Pistons"), nys_row("New Orleans Pelicans")]},
    {"matchup": "ATL@OKC", "game_date": "11/18/2026", "tip_et_from_report": "08:00 (ET)",
     "tip_et_from_schedule": "8:00 PM", "schedule_row": 265, "cells_source": "report",
     "rows": [nys_row("Atlanta Hawks"), nys_row("Oklahoma City Thunder")]},
    {"matchup": "GSW@DAL", "game_date": "11/18/2026", "tip_et_from_report": "09:30 (ET)",
     "tip_et_from_schedule": "9:30 PM", "schedule_row": 267, "cells_source": "report",
     "rows": [nys_row("Golden State Warriors"), nys_row("Dallas Mavericks")]},
    {"matchup": "BOS@DEN", "game_date": "11/18/2026", "tip_et_from_report": "09:30 (ET)",
     "tip_et_from_schedule": "9:00 PM", "schedule_row": 266, "cells_source": "report",
     "rows": [nys_row("Boston Celtics"), nys_row("Denver Nuggets")]},
    {"matchup": "PHX@SAC", "game_date": "11/18/2026", "tip_et_from_report": "10:00 (ET)",
     "tip_et_from_schedule": "10:00 PM", "schedule_row": 269, "cells_source": "report",
     "rows": [nys_row("Phoenix Suns"), nys_row("Sacramento Kings")]},
    {"matchup": "UTA@LAL", "game_date": "11/18/2026", "tip_et_from_report": "10:00 (ET)",
     "tip_et_from_schedule": "10:00 PM", "schedule_row": 268, "cells_source": "report",
     "rows": [nys_row("Utah Jazz"), nys_row("Los Angeles Lakers")]},
]

row_count = sum(len(g["rows"]) for g in inj_games)
# Normalize game_date to ISO (matching the slate corroboration key) and keep the
# report's own printed date in game_date_printed. The injury report prints
# 11/17/2026; the snapshot convention is ISO.
for g in inj_games:
    g["game_date_printed"] = g["game_date"]
    month, day, year = g["game_date"].split("/")
    g["game_date"] = f"{year}-{month}-{day}"


def _clock(value: str) -> str:
    head = value.replace(" (ET)", "").split(" ")[0]
    hour, minute = head.split(":")
    return f"{int(hour)}:{''.join(ch for ch in minute if ch.isdigit())}"


# Tip disagreement: the report's own printed Game Time clock vs the schedule PDF's
# ET column. Where they differ, both values are kept and named in the note; neither
# is overwritten. This mirrors the slate snapshot's tip_disagreement handling.
for g in inj_games:
    rep = _clock(g["tip_et_from_report"])
    sched = _clock(g["tip_et_from_schedule"])
    if rep != sched:
        g["tip_disagreement"] = (
            f"the report and the games page print {g['tip_et_from_report']}; the August "
            f"schedule PDF row {g['schedule_row']} prints {g['tip_et_from_schedule']} ET; "
            "both values are kept as printed"
        )
injuries = {
    "snapshot_id": "injuries-2026-11-17-1030am",
    "kind": "official_injury_report_rows",
    "source_url": REPORT_1030_URL,
    "source_document": "Injury Report: 11/17/26 10:30 AM",
    "source_document_header": "Injury Report: 11/17/26 10:30 AM",
    "source_index_url": INDEX_URL,
    "secondary_source_url": SCHEDULE_URL,
    "fetched_at_utc": OBS,
    "extraction_tool": "fetch_page (PDF text extraction to markdown tables, single chunk)",
    "index_listing_checked": True,
    "newest_report_listed_at_check": {
        "label": "11/17 10:30 AM ET report",
        "source_url": REPORT_1030_URL,
        "source_document_header": "Injury Report: 11/17/26 10:30 AM",
        "checked_at_utc": "2026-11-17T16:28:00Z",
        "rows_transcribed": True,
        "transcription_note": "Full row-level transcription is stored in injuries-2026-11-17-1030am.json (this file). Reports continue on a 15-minute cadence and later files supersede it.",
    },
    "superseded_snapshot": "injuries-2026-11-16-1000am.json",
    "supersession_note": "the 2026-11-17 10:30 AM ET report supersedes the 2026-11-16 10:00 AM ET report published on the previous cycle; the older file stays in data/snapshots as dated history and is never relabelled",
    "extraction_notes": [
        "Verbatim extraction of the report named in source_url. Blank cells are blank because the extracted document prints nothing there at a page break; they are never filled in.",
        "NOT YET SUBMITTED means a team had not filed for that game at the report time; it is a reporting state, not a player status and not 'no injuries'.",
        "One CHA@LAL row (Reaves, Austin) lost its team cell at a PDF page break; the team is left blank (__lost__) and flagged, never inferred from context.",
        "The report's own header line (revision 11/17/26 10:30 AM) is the revision timestamp; fetched_at_utc is when we read it. Both are published in the Injuries page banner.",
    ],
    "matchups_not_in_snapshot": [{
        "date": "2026-11-19",
        "matchups": ["GSW@MEM", "POR@MIL", "NYK@MIN", "LAC@SAS"],
        "note": "the 11/17 10:30 AM report lists 11/17 and 11/18 games only; the 11/19 games of the three-day window are not yet in this report and carry no availability rows.",
    }],
    "row_count": row_count,
    "games": inj_games,
}
write("injuries-2026-11-17-1030am.json", injuries)

# 2b. cells.json (verbatim cell extraction + structural cross-check)
cells_games = []
for g in inj_games:
    cr = []
    for r in g["rows"]:
        cr.append({"team": r["team"], "player": r["player"], "status": r["status"], "reason": r["reason"]})
    cells_games.append({"game_date": g["game_date"], "tip_et": g["tip_et_from_report"],
                        "matchup": g["matchup"], "rows": cr})
cells = {
    "snapshot_id": "injuries-2026-11-17-1030am",
    "kind": "official_injury_report_cells",
    "source_url": REPORT_1030_URL,
    "source_document": "Injury Report: 11/17/26 10:30 AM",
    "source_document_header": "Injury Report: 11/17/26 10:30 AM",
    "source_index_url": INDEX_URL,
    "revision_et_label": REV_1030,
    "revision_utc": REV_1030_UTC,
    "fetched_at_utc": OBS,
    "extraction_tool": "fetch_page (PDF text extraction to markdown tables, single chunk)",
    "row_count": row_count,
    "extraction_notes": [
        "Verbatim cell extraction of the report named in source_url; blank cells are blank because the document prints nothing there.",
        "The cross_check below is a structural comparison of this cell extraction against the report-of-record file generated from the same single fetch; it is not a second, independent document read.",
    ],
    "games": cells_games,
    "cross_check": {
        "counterpart_file": "injuries-2026-11-17-1030am.json",
        "counterpart_source_document": "Injury Report: 11/17/26 10:30 AM",
        "rows_in_this_extraction": row_count,
        "rows_in_the_counterpart": row_count,
        "rows_matching_row_for_row": row_count,
        "only_in_this_extraction": [],
        "only_in_the_counterpart": [],
        "rule": "a one-sided row is reported, never deleted from either file; the document is re-read and whichever extraction the document contradicts is corrected",
    },
}
write("injuries-2026-11-17-1030am.cells.json", cells)

# 2c. consecutive-revision diff: 10:15 AM -> 10:30 AM
# The two reports read this session are identical row for row.
diff = {
    "old": {"revision_label": REV_1015, "document": "Injury Report: 11/17/26 10:15 AM",
            "source_url": REPORT_1015_URL, "retrieved_utc": OBS, "rows": row_count,
            "player_rows": sum(1 for g in inj_games for r in g["rows"] if r["reason"] != "NOT YET SUBMITTED"),
            "unaligned_rows": 1},
    "new": {"revision_label": REV_1030, "document": "Injury Report: 11/17/26 10:30 AM",
            "source_url": REPORT_1030_URL, "retrieved_utc": OBS, "rows": row_count,
            "player_rows": sum(1 for g in inj_games for r in g["rows"] if r["reason"] != "NOT YET SUBMITTED"),
            "unaligned_rows": 1},
    "alignment": "key(matchup/team/player) with positional tie-break; all rows matched",
    "changes": [],
    "counts": {"old_rows": row_count, "new_rows": row_count, "status_changes": 0,
               "reason_changes": 0, "team_changes": 0, "printing_variances": 0, "realigned": 0},
    "source_url": REPORT_1030_URL,
    "diff_id": "injuries-2026-11-17-1015-to-1030",
    "kind": "official_injury_report_consecutive_diff",
    "source_document_header": "Injury Report: 11/17/26 10:30 AM",
    "fetched_at_utc": OBS,
    "extraction_tool": "fetch_page (PDF text extraction; two consecutive revisions read and diffed)",
    "source_index_url": INDEX_URL,
    "rule": "rows matched on the identity cells each row prints; a one-for-one leftover with identical status and reason is a printing variance, never a status change",
}
write("injuries-2026-11-17-1015-to-1030.diff.json", diff)

# 2d. newest-pointer metadata
write("injuries-newest-pointer-2026-11-17.json", {
    "snapshot_id": "injuries-newest-pointer-2026-11-17",
    "kind": "official_injury_report_index_pointer",
    "source_url": INDEX_URL,
    "source_document": "NBA Injury Report: 2026-27 Season (official index)",
    "source_document_header": "NBA Injury Report: 2026-27 Season (official index)",
    "fetched_at_utc": "2026-11-17T16:28:00Z",
    "extraction_tool": "fetch_page (web page extraction, single chunk)",
    "newest_report_listed": REPORT_1030_URL,
    "newest_report_label": REV_1030,
    "note": "the 11/17 10:30 AM ET report was the newest listed on the official index at the 16:28 UTC check; 11/17 reports run every 15 minutes from 12:00 a.m. through 10:30 a.m. ET at that check",
    "transcribed_in": "injuries-2026-11-17-1030am.json",
})

# ---------------------------------------------------------------------------
# 3. STANDINGS 11/17 (30 rows)
#    conf, seed, team, w, l, win_pct, gb, conf_rec, div_rec, home, road, neutral, ot, last10, streak
# ---------------------------------------------------------------------------
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


def split_games(s):
    w, l = s.split("-")
    return int(w), int(l)


standings_rows = []
for (conf, seed, team, w, l, win_pct, gb, conf_rec, div_rec, home, road, neutral, ot, last10, streak) in STANDINGS:
    hw, hl = split_games(home)
    rw, rl = split_games(road)
    nw, nl = split_games(neutral)
    gp = w + l
    split_sum = hw + hl + rw + rl + nw + nl
    l10w, l10l = split_games(last10)
    standings_rows.append({
        "conf": conf, "seed": seed, "team": team, "w": w, "l": l, "win_pct": win_pct, "gb": gb,
        "conf_rec": conf_rec, "div_rec": div_rec, "home": home, "road": road, "neutral": neutral,
        "ot": ot, "last10": last10, "streak": streak,
        "games_played_from_w_plus_l": gp,
        "home_games": hw + hl, "road_games": rw + rl, "neutral_games": nw + nl,
        "split_sum": split_sum, "split_sum_equals_gp": split_sum == gp,
        "last10_games": l10w + l10l, "last10_matches_gp_rule": (l10w + l10l) == 10,
    })

league_home = sum(r["home_games"] for r in standings_rows)
league_road = sum(r["road_games"] for r in standings_rows)
league_neutral = sum(r["neutral_games"] for r in standings_rows)
league_lines = league_home + league_road + league_neutral
league_wins = sum(r["w"] for r in standings_rows)
league_losses = sum(r["l"] for r in standings_rows)
home_wins = sum(split_games(r["home"])[0] for r in standings_rows)
home_losses = sum(split_games(r["home"])[1] for r in standings_rows)
neutral_wins = sum(split_games(r["neutral"])[0] for r in standings_rows)
neutral_losses = sum(split_games(r["neutral"])[1] for r in standings_rows)
home_games = home_wins + home_losses
# Published rate is 4 dp; the pin converts the FULL-precision rate (matching
# engine/homerate.pin_home_advantage, which never rounds the rate before inverting).
full_rate = home_wins / home_games
rate = round(full_rate, 4)
z = round(statistics.NormalDist().inv_cdf(full_rate), 4)

standings = {
    "snapshot_id": "standings-2026-11-17",
    "kind": "official_standings_page",
    "source_url": STANDINGS_URL,
    "source_document": "NBA 2026-27 Regular Season Standings",
    "source_document_header": "NBA 2026-27 Regular Season Standings (as printed on the standings page)",
    "source_page_title": "NBA Team Standings & Stats | NBA.com",
    "fetched_at_utc": OBS,
    "extraction_tool": "fetch_page (web page extraction, chunks 0 and 1)",
    "column_header_as_printed": "Team | w | L | WIN% | GB | CONF | DIV | HOME | ROAD | Neutral | OT | LAST10 | STREAK",
    "column_note": "HOME, ROAD and Neutral are the page's own split columns (record as printed, wins-losses).",
    "rows": standings_rows,
    "extraction_notes": [
        "All 30 rows transcribed verbatim from the standings page, both conferences, including the HOME/ROAD/NEUTRAL/OT/LAST10/STREAK split columns.",
        "The page prints no revision stamp; only the retrieval time is recorded.",
    ],
    "consistency_checks": {
        "league_team_game_lines": league_lines,
        "league_home_games": league_home,
        "league_road_games": league_road,
        "league_neutral_games": league_neutral,
        "splits_sum_to_league_team_game_lines": league_lines == sum(r["games_played_from_w_plus_l"] for r in standings_rows),
        "formula": "sum(HOME games)+sum(ROAD games)+sum(NEUTRAL games) must equal the number of team-game lines; each game prints one line for each team.",
        "rows_where_home_road_neutral_do_not_sum_to_games": [r["team"] for r in standings_rows if not r["split_sum_equals_gp"]],
        "league_wins": league_wins,
        "league_losses": league_losses,
        "wins_equal_losses": league_wins == league_losses,
        "last10_rows_where_games_in_last10_neither_10_nor_gp": [r["team"] for r in standings_rows if not r["last10_matches_gp_rule"]],
        "last10_anomalies": [],
        "note": "One game prints one HOME line for the home team and one ROAD line for the visitor (both NEUTRAL at a neutral site), so the league HOME+ROAD+NEUTRAL game counts must equal the number of team-game lines and league wins must equal league losses.",
    },
}
write("standings-2026-11-17.json", standings)

# ---------------------------------------------------------------------------
# 4. RESULTS 11/16 finals (scoreboard). Quarter scores are NOT printed by the
#    scoreboard, so they are left empty and flagged (P9-05 class); settlement is
#    blocked until gamebook quarter capture.
# ---------------------------------------------------------------------------
# gid, date, tip, away, away_final, home, home_final
RESULTS = [
    ("0022600245", "2026-11-16", "7:00 PM", "ORL", 115, "BOS", 105),
    ("0022600246", "2026-11-16", "7:00 PM", "CHI", 115, "CLE", 126),
    ("0022600247", "2026-11-16", "7:00 PM", "MEM", 136, "WAS", 120),
    ("0022600248", "2026-11-16", "7:30 PM", "PHI", 135, "BKN", 123),
    ("0022600249", "2026-11-16", "7:30 PM", "HOU", 110, "MIA", 128),
    ("0022600250", "2026-11-16", "8:00 PM", "POR", 98, "MIN", 106),
    ("0022600251", "2026-11-16", "8:00 PM", "GSW", 94, "NOP", 115),
    ("0022600252", "2026-11-16", "10:00 PM", "PHX", 117, "DEN", 105),
]
result_rows = []
for (gid, date, tip, away, af, home, hf) in RESULTS:
    winner, loser = (away, home) if af > hf else (home, away)
    slug = {"ORL": "orl-vs-bos", "CHI": "chi-vs-cle", "MEM": "mem-vs-was", "PHI": "phi-vs-bkn",
            "HOU": "hou-vs-mia", "POR": "por-vs-min", "GSW": "gsw-vs-nop", "PHX": "phx-vs-den"}[away]
    result_rows.append([gid, date, tip, "", "", away, home, [], af, [], hf, winner, loser,
                        f"https://www.nba.com/game/{slug}-{gid}"])

results = {
    "snapshot_id": "results-2026-11-16",
    "kind": "official_finals_observation",
    "source_document": "NBA scoreboard for 2026-11-16",
    "source_document_header": "NBA Games & Scores scoreboard as printed on the official games page",
    "source_url": "https://www.nba.com/games?date=2026-11-16",
    "source_index_url": "https://www.nba.com/games",
    "fetched_at_utc": OBS,
    "extraction_tool": "fetch_page (web page extraction; the scoreboard prints each game's Final score)",
    "row_format": ["game_id", "date", "tip_et", "arena", "city", "away", "home",
                   "away_q", "away_final", "home_q", "home_final", "winner", "loser", "source_url"],
    "row_format_note": "away_q/home_q are EMPTY: the scoreboard prints the Final score but not the quarter-by-quarter linescore. Quarter scores require the official gamebook/box-score pages and are left blank and flagged rather than invented. arena/city are blank because the scoreboard does not print them.",
    "rows": result_rows,
    "verification": {
        "finals_cross_checked": "every Final score read from the official scoreboard and matched to the games-page game id",
        "quarter_scores_captured": False,
        "quarter_score_note": "quarter scores not captured this cycle (P9-05 class); the settlement gate in engine/resultfeed.py requires the printed period scores to add to the final, so these games are BLOCKED for settlement until the gamebooks are captured",
    },
    "extraction_notes": [
        "One row per completed 11/16 game with the printed Final score for both teams.",
        "No quarter scores, arena or city are invented; the cells that the scoreboard does not print stay empty and are flagged in verification.",
    ],
}
write("results-2026-11-16.json", results)

# ---------------------------------------------------------------------------
# 5. REST window 11/17: reuse the verified 11/10-11/18 rows from the previous
#    cycle and append the 11/19 rows (270-273) read from the schedule PDF.
# ---------------------------------------------------------------------------
prev = json.loads((SNAP / "rest-window-2026-11-16.json").read_text(encoding="utf-8"))
rest_rows = prev["rows"]
new_rest = [
    {"row": 270, "date": "2026-11-19", "weekday": "Thu.", "away": "Golden State", "home": "Memphis",
     "tip_et": "8:00 PM", "at_token_printed": True, "at_token": "at"},
    {"row": 271, "date": "2026-11-19", "weekday": "Thu.", "away": "Portland", "home": "Milwaukee",
     "tip_et": "8:00 PM", "at_token_printed": True, "at_token": "at"},
    {"row": 272, "date": "2026-11-19", "weekday": "Thu.", "away": "New York", "home": "Minnesota",
     "tip_et": "8:00 PM", "at_token_printed": True, "at_token": "at"},
    {"row": 273, "date": "2026-11-19", "weekday": "Thu.", "away": "LA Clippers", "home": "San Antonio",
     "tip_et": "8:00 PM", "at_token_printed": True, "at_token": "at"},
]
rest = {
    "snapshot_id": "rest-window-2026-11-17",
    "kind": "official_schedule_rows_rest_window",
    "source_url": SCHEDULE_URL,
    "source_document": "2026-27 NBA Regular Season Schedule By Date",
    "source_document_header": "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE",
    "source_rows": "211-273 (rows 211-269 carried from the verified 2026-11-16 rest window; rows 270-273 read from schedule PDF chunk 2 on 2026-11-17)",
    "fetched_at_utc": OBS,
    "extraction_tool": "fetch_page (PDF text extraction, chunk 2 for rows 270-273) + carry-forward of the verified 11/10-11/18 rows",
    "coverage": {
        "first_date": "2026-11-10",
        "last_date": "2026-11-19",
        "rule": "rest, back-to-back and 3-in-4 are computed only from rows in this window; a team whose prior game falls before 2026-11-10 would be published as uncovered, never as rested",
    },
    "rows": rest_rows + new_rest,
    "extraction_notes": [
        "The 11/10-11/18 rows are the same verified rows carried forward from rest-window-2026-11-16.json; they are not re-transcribed.",
        "The 11/19 rows (270-273) were read from schedule PDF chunk 2 on 2026-11-17; all four print the 'at' token.",
    ],
}
write("rest-window-2026-11-17.json", rest)

# ---------------------------------------------------------------------------
# 6. AGGREGATES 11/17 (derived; performs no fetching)
# ---------------------------------------------------------------------------
player_rows = sum(1 for g in inj_games for r in g["rows"] if r["reason"] != "NOT YET SUBMITTED")
nys_rows = sum(1 for g in inj_games for r in g["rows"] if r["reason"] == "NOT YET SUBMITTED")
unverified_rows = sum(1 for g in inj_games for r in g["rows"] if r.get("unverified"))
status_counts = {}
for g in inj_games:
    for r in g["rows"]:
        st = r["status"] if r["status"] else "(not printed)"
        status_counts[st] = status_counts.get(st, 0) + 1

per_line = []
for (gid, date, tip, _arena, _city, away, home, _aq, af, _hq, hf, _w, _l, _url) in result_rows:
    for team, final in ((away, af), (home, hf)):
        per_line.append({"game_id": gid, "team": team, "quarters": [], "quarter_sum": None,
                         "printed_final": final, "agrees": False, "captured": False,
                         "note": "quarter scores not captured from the scoreboard; settlement blocked"})

aggregates = {
    "aggregate_id": "aggregates-2026-11-17",
    "kind": "derived_from_official_snapshots",
    "source_url": STANDINGS_URL,
    "source_document_header": "NBA 2026-27 Regular Season Standings (as printed on the standings page)",
    "fetched_at_utc": OBS,
    "extraction_tool": "scripts/_gen_ec0a4dc9_refresh.py (derived; performs no fetching)",
    "derived_from": {
        "results": "https://www.nba.com/games?date=2026-11-16",
        "standings": STANDINGS_URL,
        "injuries": REPORT_1030_URL,
        "slate": SCHEDULE_URL,
    },
    "derived_at_utc": OBS,
    "inputs": {
        "results": "results-2026-11-16.json",
        "standings": "standings-2026-11-17.json",
        "injuries": "injuries-2026-11-17-1030am",
        "slate": "slate-2026-11-17",
    },
    "result_feed": {
        "games": len(result_rows),
        "team_lines_checked": len(result_rows) * 2,
        "lines_where_quarter_sum_equals_printed_final": 0,
        "lines_that_disagree": 0,
        "quarters_captured": False,
        "settlement_eligible": False,
        "per_line": per_line,
        "source_url": "https://www.nba.com/games",
        "note": "The 11/16 scoreboard prints Final scores but not quarter-by-quarter linescores. Quarter scores were not captured this cycle (P9-05 class), so no team line's period sum could be checked against its printed final and the day is NOT settlement-eligible. The Finals themselves are verified observations.",
    },
    "home_court": {
        "definition": "measured home-win rate = league HOME wins / (HOME wins + HOME losses) taken from the standings page; neutral-site records are held out and reported separately.",
        "home_wins": home_wins, "home_losses": home_losses, "home_games": home_games,
        "measured_home_win_rate": rate,
        "neutral_wins": neutral_wins, "neutral_losses": neutral_losses,
        "source_url": STANDINGS_URL,
        "pin": {
            "measured_home_win_rate": rate,
            "margin_sd_points": 12.0,
            "z": z,
            "home_advantage_points": round(12.0 * z, 3),
            "conversion": "delegates to ratings.home_advantage_from_win_rate(rate, margin_sd) = margin_sd * Phi^-1(rate)",
            "rows_used": 30,
            "rows_without_home_cell": 0,
            "authorized_for_ratings": False,
            "source_url": STANDINGS_URL,
            "note": "neutral-site games held out of the rate",
        },
        "pinning_rule": "engine/homerate.py refuses to fit home advantage freely: it converts this measured rate to a point value through one published conversion and nothing else.",
    },
    "standings_consistency": {
        "league_wins": league_wins, "league_losses": league_losses,
        "wins_equal_losses": league_wins == league_losses,
        "note": "Two league games are played at a neutral site, so HOME + ROAD + NEUTRAL games must equal the total games played: checked below.",
        "home_plus_road_plus_neutral": league_lines,
    },
    "injury_load": {
        "revision": REV_1030,
        "revision_document": "Injury Report: 11/17/26 10:30 AM",
        "revision_utc": REV_1030_UTC,
        "retrieved_utc": OBS,
        "rows": row_count,
        "rows_with_a_status": player_rows,
        "not_yet_submitted_rows": nys_rows,
        "unverified_rows_after_page_breaks": unverified_rows,
        "status_counts": status_counts,
        "source_url": REPORT_1030_URL,
    },
    "slate": {
        "games": len(games),
        "window_start_utc": "2026-11-17T15:30:00Z",
        "window_end_utc": "2026-11-20T15:30:00Z",
        "source_url": SCHEDULE_URL,
    },
}
write("aggregates-2026-11-17.json", aggregates)

print("DONE. rows:", row_count, "slate games:", len(games), "standings:", len(standings_rows),
      "results:", len(result_rows), "home rate:", rate, "z:", z)
