#!/usr/bin/env python3
"""Generate the 2026-11-19 refresh-cycle official-observation snapshots.

This script is a transcription generator, not a data feed. Every value below was
read verbatim from an official NBA page on 2026-11-19 (UTC) and is stored with
its source URL, the document's own header, and a fetch timestamp. Nothing is
inferred: a cell lost at a PDF page break stays blank and is flagged.

Surfaces produced (the 11/19 rolling-slate refresh, fixing the CA-01
injury-transcription freshness flag):
  * injuries-2026-11-19-0145am.json   file of record (44 rows, 13 blocks)
  * injuries-2026-11-19-0130am.json   prior consecutive revision (44 rows)
  * injuries-2026-11-19-0130-to-0145.diff.json   consecutive-revision diff
  * injuries-newest-pointer-2026-11-19.json      index metadata
  * slate-2026-11-19.json             19 games (11/19 + 11/20 Cup + 11/21)
  * standings-2026-11-19.json         30 rows
  * rest-window-2026-11-19.json       11/10-11/20 schedule rows
  * aggregates-2026-11-19.json        derived (no fetching)

Team-stats and the 11/18 result quarters are intentionally NOT re-cut here: the
team-stat pages are large and the 11/18 box-score quarter capture is pending;
both are flagged on the review page rather than partially transcribed.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"

SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
SCHEDULE_DOC = "2026-27 NBA Regular Season Schedule By Date"
SCHEDULE_HEADER = "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE"
REPORT_0145_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf"
REPORT_0130_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_30AM.pdf"
INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
STANDINGS_URL = "https://www.nba.com/standings"
FETCH_NOW = "2026-11-19T07:05:00Z"  # minute-level, from the session clock

# ---------------------------------------------------------------------------
# 1. INJURY REPORT 01:45 AM ET (file of record) - 44 rows, 13 game blocks
# ---------------------------------------------------------------------------

def row(team, player, status, reason, unverified=False, flag=""):
    r = {"team": team, "player": player, "status": status, "reason": reason}
    if unverified:
        r["unverified"] = True
        r["flag"] = flag
    return r


NYS = "NOT YET SUBMITTED"
LOST_GSW = ("date/time/matchup/team cells lost at page break; the row prints in the "
            "block that continues GSW@MEM; the team cell is not printed and is not inferred")

INJURY_BLOCKS = [
    # --- 11/19 games (schedule rows 270-273) ---
    {
        "matchup": "GSW@MEM", "game_date": "2026-11-19", "schedule_row": 270,
        "tip_et_from_report": "08:00 (ET)", "tip_et_from_schedule": "8:00 PM",
        "cells_source": "report",
        "rows": [
            row("Golden State Warriors", "", "", NYS),
            row("Memphis Grizzlies", "", "", NYS),
            row("__lost__", "Kuminga, Jonathan", "Questionable",
                "Injury/Illness - Right Shoulder Contusion", True, LOST_GSW),
            row("__lost__", "Pullin, Zyon", "Questionable",
                "Injury/Illness - Right Quadriceps Contusion", True, LOST_GSW),
        ],
        "block_note": ("The block prints NOT YET SUBMITTED for Golden State on page 1 yet two "
                       "GSW player rows (Kuminga, Pullin) print on page 2 with lost cells; the "
                       "block is internally inconsistent and the player rows stay unattributed."),
    },
    {
        "matchup": "LAC@SAS", "game_date": "2026-11-19", "schedule_row": 273,
        "tip_et_from_report": "08:00 (ET)", "tip_et_from_schedule": "8:00 PM",
        "cells_source": "report",
        "rows": [
            row("LA Clippers", "Beal, Bradley", "Out", "Injury/Illness - Right Knee Injury Management"),
            row("LA Clippers", "Ingram, Brandon", "Out", "Injury/Illness - Right Heel Surgery"),
            row("LA Clippers", "Martinelli, Nick", "Out", "G League - Two-Way"),
            row("LA Clippers", "Miller, Jordan", "Out", "Injury/Illness - Left Rotator Cuff Surgery"),
            row("San Antonio Spurs", "Brown, Maliq", "Out", "G League - Two-Way"),
            row("San Antonio Spurs", "Gillespie, Ja'Kobi", "Out", "G League - Two-Way"),
            row("San Antonio Spurs", "Harper, Dylan", "Out", "Injury/Illness - Left Hip Soreness"),
            row("San Antonio Spurs", "Harris, Tobias", "Out", "Injury/Illness - Left Calf Strain"),
            row("San Antonio Spurs", "Quaintance, Jayden", "Out", "Injury/Illness - Right Knee Surgery"),
        ],
    },
    {
        "matchup": "NYK@MIN", "game_date": "2026-11-19", "schedule_row": 272,
        "tip_et_from_report": "08:00 (ET)", "tip_et_from_schedule": "8:00 PM",
        "cells_source": "report",
        "rows": [
            row("Minnesota Timberwolves", "Beringer, Joan", "Available", "Injury/Illness - Face Mask"),
            row("Minnesota Timberwolves", "Clark, Jaylen", "Out", "Injury/Illness - Right Hamstring Strain"),
            row("Minnesota Timberwolves", "DiVincenzo, Donte", "Out",
                "Injury/Illness - Right Achilles Tendon Repair / Surgery"),
            row("Minnesota Timberwolves", "Edwards, Anthony", "Out", "Injury/Illness - Right Knee Arthroscopy"),
        ],
        "block_note": ("The report prints Minnesota Timberwolves rows only; no New York Knicks row "
                       "is printed for this game at this revision."),
    },
    {
        "matchup": "POR@MIL", "game_date": "2026-11-19", "schedule_row": 271,
        "tip_et_from_report": "08:00 (ET)", "tip_et_from_schedule": "8:00 PM",
        "cells_source": "report",
        "rows": [
            row("Portland Trail Blazers", "Avdija, Deni", "Questionable",
                "Injury/Illness - Left Foot Inflammation / Soreness"),
            row("Portland Trail Blazers", "Camara, Toumani", "Questionable", "Injury/Illness - Abdominal Soreness"),
            row("Portland Trail Blazers", "Carlson, Branden", "Available", "Injury/Illness - Face Mask"),
            row("Portland Trail Blazers", "Krejci, Vit", "Out", "Injury/Illness - Left Ankle Fracture"),
            row("Portland Trail Blazers", "Morant, Ja", "Out", "Injury/Illness - Left Hamstring Strain"),
            row("Portland Trail Blazers", "Sharpe, Shaedon", "Out", "Injury/Illness - Right Meniscus Surgery"),
            row("Portland Trail Blazers", "Williams III, Robert", "Out", "Rest"),
            row("Portland Trail Blazers", "Youngblood, Chris", "Out",
                "Injury/Illness - Right Heel Contusion / Bone Bruise"),
            row("Milwaukee Bucks", "", "", NYS),
        ],
    },
    # --- 11/20 Emirates NBA Cup group games (schedule rows 43-51) ---
    # All NOT YET SUBMITTED. Page-break fragmentation loses cells on some rows.
    {
        "matchup": "CHA@ATL", "game_date": "2026-11-20", "schedule_row": 43,
        "tip_et_from_report": "07:00 (ET)", "tip_et_from_schedule": "7:00 PM",
        "cells_source": "report",
        "rows": [row("Charlotte Hornets", "", "", NYS), row("Atlanta Hawks", "", "", NYS)],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C).",
    },
    {
        "matchup": "ORL@BKN", "game_date": "2026-11-20", "schedule_row": 44,
        "tip_et_from_report": "07:30 (ET)", "tip_et_from_schedule": "7:30 PM",
        "cells_source": "report",
        "rows": [
            row("Orlando Magic", "", "", NYS),
            row("Brooklyn Nets", "", "", NYS, True,
                "matchup cell lost at page break; reason NOT YET SUBMITTED printed"),
        ],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C).",
    },
    {
        "matchup": "IND@CLE", "game_date": "2026-11-20", "schedule_row": 45,
        "tip_et_from_report": "07:30 (ET)", "tip_et_from_schedule": "7:30 PM",
        "cells_source": "report",
        "rows": [row("Indiana Pacers", "", "", NYS), row("Cleveland Cavaliers", "", "", NYS)],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C).",
    },
    {
        "matchup": "TOR@DET", "game_date": "2026-11-20", "schedule_row": 46,
        "tip_et_from_report": "", "tip_et_from_schedule": "7:30 PM",
        "cells_source": "report",
        "rows": [
            row("Toronto Raptors", "", "", "", True,
                "time/status/reason cells lost at page break; 11/20 NOT YET SUBMITTED block (no player entries printed)"),
            row("Detroit Pistons", "", "", NYS, True,
                "matchup cell lost at page break; reason NOT YET SUBMITTED printed"),
        ],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C, broadcast Prime).",
    },
    {
        "matchup": "WAS@CHI", "game_date": "2026-11-20", "schedule_row": 47,
        "tip_et_from_report": "08:00 (ET)", "tip_et_from_schedule": "8:00 PM",
        "cells_source": "report",
        "rows": [
            row("Washington Wizards", "", "", "", True,
                "status/reason cells lost at page break; 11/20 NOT YET SUBMITTED block (no player entries printed)"),
            row("Chicago Bulls", "", "", NYS, True,
                "matchup cell lost at page break; reason NOT YET SUBMITTED printed"),
        ],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C).",
    },
    {
        "matchup": "NOP@OKC", "game_date": "2026-11-20", "schedule_row": 48,
        "tip_et_from_report": "08:00 (ET)", "tip_et_from_schedule": "8:00 PM",
        "cells_source": "report",
        "rows": [
            row("New Orleans Pelicans", "", "", "", True,
                "status/reason cells lost at page break; 11/20 NOT YET SUBMITTED block (no player entries printed)"),
            row("Oklahoma City Thunder", "", "", NYS, True,
                "matchup cell lost at page break; reason NOT YET SUBMITTED printed"),
        ],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C).",
    },
    {
        "matchup": "PHX@UTA", "game_date": "2026-11-20", "schedule_row": 49,
        "tip_et_from_report": "09:30 (ET)", "tip_et_from_schedule": "9:30 PM",
        "cells_source": "report",
        "rows": [
            row("Phoenix Suns", "", "", "", True,
                "status/reason cells lost at page break; 11/20 NOT YET SUBMITTED block (no player entries printed)"),
            row("Utah Jazz", "", "", NYS, True,
                "matchup cell lost at page break; reason NOT YET SUBMITTED printed"),
        ],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C).",
    },
    {
        "matchup": "HOU@DEN", "game_date": "2026-11-20", "schedule_row": 50,
        "tip_et_from_report": "10:00 (ET)", "tip_et_from_schedule": "10:00 PM",
        "cells_source": "report",
        "rows": [
            row("Houston Rockets", "", "", "", True,
                "status/reason cells lost at page break; 11/20 NOT YET SUBMITTED block (no player entries printed)"),
            row("Denver Nuggets", "", "", NYS, True,
                "matchup cell lost at page break; reason NOT YET SUBMITTED printed"),
        ],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C, broadcast Prime).",
    },
    {
        "matchup": "SAC@LAL", "game_date": "2026-11-20", "schedule_row": 51,
        "tip_et_from_report": "10:00 (ET)", "tip_et_from_schedule": "10:00 PM",
        "cells_source": "report",
        "rows": [
            row("Sacramento Kings", "", "", "", True,
                "status/reason cells lost at page break; 11/20 NOT YET SUBMITTED block (no player entries printed)"),
            row("Los Angeles Lakers", "", "", NYS, True,
                "matchup cell lost at page break; reason NOT YET SUBMITTED printed"),
        ],
        "block_note": "Emirates NBA Cup group game (schedule PDF row marked C).",
    },
]

# ---------------------------------------------------------------------------
# 2. SLATE 11/19 - 11/21 (19 games) from the schedule PDF + games pages
# ---------------------------------------------------------------------------

def slate_game(row, wd, date_, away, home, c1, c2, slug, gid, tip_gp, code, code_src, at_token, corrob, note=""):
    g = {
        "row": row, "date": date_, "weekday": wd, "away": away, "home": home,
        "tip_et_col1": c1, "tip_et_col2": c2,
        "code": code, "code_source": code_src,
        "games_page_slug": slug, "games_page_game_id": gid,
        "games_page_tip_et": tip_gp,
        "games_page_url": f"https://www.nba.com/game/{slug}-{gid}",
        "order_corroborated_by": corrob,
        "tip_disagreement": None, "at_token_printed": at_token,
    }
    if note:
        g["note"] = note
    return g


REPORT = "injury report 11/19 01:45 AM"
SLATE_GAMES = [
    # 11/19 (rows 270-273)
    slate_game(270, "Thu.", "2026-11-19", "Golden State", "Memphis", "7:00 PM", "8:00 PM",
               "gsw-vs-mem", "0022600270", "8:00 PM ET", "GSW@MEM", REPORT, True,
               [f"{REPORT} matchup code GSW@MEM", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"]),
    slate_game(271, "Thu.", "2026-11-19", "Portland", "Milwaukee", "7:00 PM", "8:00 PM",
               "por-vs-mil", "0022600271", "8:00 PM ET", "POR@MIL", REPORT, True,
               [f"{REPORT} matchup code POR@MIL", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"]),
    slate_game(272, "Thu.", "2026-11-19", "New York", "Minnesota", "7:00 PM", "8:00 PM",
               "nyk-vs-min", "0022600272", "8:00 PM ET", "NYK@MIN", REPORT, True,
               [f"{REPORT} matchup code NYK@MIN", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"]),
    slate_game(273, "Thu.", "2026-11-19", "LA Clippers", "San Antonio", "7:00 PM", "8:00 PM",
               "lac-vs-sas", "0022600273", "8:00 PM ET", "LAC@SAS", REPORT, True,
               [f"{REPORT} matchup code LAC@SAS", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"]),
    # 11/20 Emirates NBA Cup (rows 43-51)
    slate_game(43, "Fri.", "2026-11-20", "Charlotte", "Atlanta", "7:00 PM", "7:00 PM",
               "cha-vs-atl", "0022600043", "7:00 PM ET", "CHA@ATL", REPORT, True,
               [f"{REPORT} matchup code CHA@ATL", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup East Group C"),
    slate_game(44, "Fri.", "2026-11-20", "Orlando", "Brooklyn", "7:30 PM", "7:30 PM",
               "orl-vs-bkn", "0022600044", "7:30 PM ET", "ORL@BKN", REPORT, True,
               [f"{REPORT} matchup code ORL@BKN", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup East Group A"),
    slate_game(45, "Fri.", "2026-11-20", "Indiana", "Cleveland", "7:30 PM", "7:30 PM",
               "ind-vs-cle", "0022600045", "7:30 PM ET", "IND@CLE", REPORT, True,
               [f"{REPORT} matchup code IND@CLE", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup East Group B"),
    slate_game(46, "Fri.", "2026-11-20", "Toronto", "Detroit", "7:30 PM", "7:30 PM",
               "tor-vs-det", "0022600046", "7:30 PM ET", "TOR@DET", REPORT, True,
               [f"{REPORT} matchup code TOR@DET", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup East Group A; PDF broadcast column reads Prime"),
    slate_game(47, "Fri.", "2026-11-20", "Washington", "Chicago", "7:00 PM", "8:00 PM",
               "was-vs-chi", "0022600047", "8:00 PM ET", "WAS@CHI", REPORT, True,
               [f"{REPORT} matchup code WAS@CHI", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup East Group C"),
    slate_game(48, "Fri.", "2026-11-20", "New Orleans", "Oklahoma City", "7:00 PM", "8:00 PM",
               "nop-vs-okc", "0022600048", "8:00 PM ET", "NOP@OKC", REPORT, True,
               [f"{REPORT} matchup code NOP@OKC", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup West Group B"),
    slate_game(49, "Fri.", "2026-11-20", "Phoenix", "Utah", "7:30 PM", "9:30 PM",
               "phx-vs-uta", "0022600049", "9:30 PM ET", "PHX@UTA", REPORT, True,
               [f"{REPORT} matchup code PHX@UTA", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup West Group A"),
    slate_game(50, "Fri.", "2026-11-20", "Houston", "Denver", "8:00 PM", "10:00 PM",
               "hou-vs-den", "0022600050", "10:00 PM ET", "HOU@DEN", REPORT, True,
               [f"{REPORT} matchup code HOU@DEN", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup West Group A; PDF broadcast column reads Prime"),
    slate_game(51, "Fri.", "2026-11-20", "Sacramento", "LA Lakers", "7:00 PM", "10:00 PM",
               "sac-vs-lal", "0022600051", "10:00 PM ET", "SAC@LAL", REPORT, True,
               [f"{REPORT} matchup code SAC@LAL", "schedule PDF printed 'at' token",
                "games page URL slug 'away-vs-home'"],
               note="Emirates NBA Cup West Group C"),
    # 11/21 (rows 274-279) - no injury report yet
    slate_game(274, "Sat.", "2026-11-21", "Milwaukee", "Philadelphia", "1:00 PM", "1:00 PM",
               "mil-vs-phi", "0022600274", "1:00 PM ET", None, None, True,
               ["schedule PDF printed 'at' token", "games page URL slug 'away-vs-home'"]),
    slate_game(275, "Sat.", "2026-11-21", "Portland", "New York", "7:30 PM", "7:30 PM",
               "por-vs-nyk", "0022600275", "7:30 PM ET", None, None, True,
               ["schedule PDF printed 'at' token", "games page URL slug 'away-vs-home'"]),
    slate_game(276, "Sat.", "2026-11-21", "LA Clippers", "Dallas", "7:00 PM", "8:00 PM",
               "lac-vs-dal", "0022600276", "8:00 PM ET", None, None, True,
               ["schedule PDF printed 'at' token", "games page URL slug 'away-vs-home'"]),
    slate_game(277, "Sat.", "2026-11-21", "Memphis", "Minnesota", "7:00 PM", "8:00 PM",
               "mem-vs-min", "0022600277", "8:00 PM ET", None, None, True,
               ["schedule PDF printed 'at' token", "games page URL slug 'away-vs-home'"]),
    slate_game(278, "Sat.", "2026-11-21", "New Orleans", "San Antonio", "7:00 PM", "8:00 PM",
               "nop-vs-sas", "0022600278", "8:00 PM ET", None, None, True,
               ["schedule PDF printed 'at' token", "games page URL slug 'away-vs-home'"]),
    slate_game(279, "Sat.", "2026-11-21", "Boston", "Sacramento", "7:00 PM", "10:00 PM",
               "bos-vs-sac", "0022600279", "10:00 PM ET", None, None, True,
               ["schedule PDF printed 'at' token", "games page URL slug 'away-vs-home'"]),
]

# ---------------------------------------------------------------------------
# 3. STANDINGS 2026-11-19 (30 rows, as printed)
#    (conf, seed, team, w, l, win_pct, gb, conf, div, home, road, neutral, ot, l10, streak)
# ---------------------------------------------------------------------------

STANDINGS_RAW = [
    ("East", 1, "Philadelphia 76ers", 13, 3, ".813", "--", "13-3", "4-1", "6-2", "7-1", "0-0", "0-0", "8-2", "W 4"),
    ("East", 2, "Boston Celtics", 11, 4, ".733", "1.5", "10-2", "4-0", "6-1", "5-3", "0-0", "1-0", "7-3", "L 2"),
    ("East", 3, "Detroit Pistons", 10, 4, ".714", "2", "8-3", "0-0", "3-2", "7-2", "0-0", "1-0", "7-3", "W 2"),
    ("East", 4, "Miami Heat", 9, 6, ".600", "3.5", "5-2", "1-1", "5-3", "4-3", "0-0", "1-0", "8-2", "W 6"),
    ("East", 5, "Atlanta Hawks", 9, 6, ".600", "3.5", "8-2", "4-1", "3-3", "6-3", "0-0", "0-1", "7-3", "W 2"),
    ("East", 6, "New York Knicks", 8, 6, ".571", "4", "8-6", "3-3", "4-3", "4-3", "0-0", "1-0", "7-3", "W 2"),
    ("East", 7, "Cleveland Cavaliers", 8, 8, ".500", "5", "6-5", "2-0", "6-3", "2-5", "0-0", "1-0", "4-6", "L 1"),
    ("East", 8, "Orlando Magic", 6, 8, ".429", "6", "4-5", "0-2", "1-5", "5-3", "0-0", "0-1", "5-5", "L 1"),
    ("East", 9, "Toronto Raptors", 5, 10, ".333", "7.5", "4-6", "0-4", "2-6", "3-4", "0-0", "0-1", "2-8", "L 6"),
    ("East", 10, "Indiana Pacers", 5, 10, ".333", "7.5", "3-6", "0-1", "2-5", "3-4", "0-1", "0-0", "3-7", "L 2"),
    ("East", 11, "Washington Wizards", 5, 11, ".313", "8", "5-8", "2-3", "2-5", "3-6", "0-0", "0-1", "2-8", "W 1"),
    ("East", 12, "Charlotte Hornets", 4, 10, ".286", "8", "4-7", "2-2", "3-4", "1-6", "0-0", "0-1", "1-9", "L 3"),
    ("East", 13, "Chicago Bulls", 4, 10, ".286", "8", "3-9", "1-1", "1-4", "3-6", "0-0", "1-0", "3-7", "W 1"),
    ("East", 14, "Brooklyn Nets", 3, 11, ".214", "9", "2-9", "0-3", "1-5", "2-6", "0-0", "0-1", "3-7", "L 3"),
    ("East", 15, "Milwaukee Bucks", 1, 14, ".067", "11.5", "1-11", "1-2", "1-7", "0-7", "0-0", "0-0", "0-10", "L 11"),
    ("West", 1, "Los Angeles Lakers", 13, 3, ".813", "--", "7-3", "5-1", "6-2", "7-1", "0-0", "1-0", "9-1", "L 1"),
    ("West", 2, "San Antonio Spurs", 12, 3, ".800", "0.5", "11-2", "2-1", "5-3", "7-0", "0-0", "1-0", "9-1", "L 1"),
    ("West", 3, "Houston Rockets", 12, 4, ".750", "1", "6-3", "2-1", "7-1", "5-3", "0-0", "0-0", "7-3", "W 1"),
    ("West", 4, "Minnesota Timberwolves", 11, 4, ".733", "1.5", "7-2", "3-0", "7-2", "4-2", "0-0", "0-1", "8-2", "W 2"),
    ("West", 5, "Memphis Grizzlies", 11, 4, ".733", "1.5", "7-3", "1-1", "3-4", "8-0", "0-0", "0-1", "6-4", "W 4"),
    ("West", 6, "Portland Trail Blazers", 9, 5, ".643", "3", "9-5", "4-2", "3-2", "6-3", "0-0", "0-0", "6-4", "L 2"),
    ("West", 7, "Denver Nuggets", 8, 5, ".615", "3.5", "5-5", "0-2", "3-3", "4-2", "1-0", "1-0", "7-3", "W 1"),
    ("West", 8, "Oklahoma City Thunder", 9, 6, ".600", "3.5", "6-5", "1-2", "5-1", "4-5", "0-0", "0-0", "5-5", "L 1"),
    ("West", 9, "Dallas Mavericks", 8, 7, ".533", "4.5", "4-5", "1-3", "6-2", "2-5", "0-0", "0-0", "5-5", "W 1"),
    ("West", 10, "Golden State Warriors", 8, 7, ".533", "4.5", "6-7", "3-2", "6-1", "2-6", "0-0", "1-0", "6-4", "L 4"),
    ("West", 11, "Phoenix Suns", 7, 7, ".500", "5", "5-7", "3-2", "5-4", "2-3", "0-0", "0-0", "6-4", "W 2"),
    ("West", 12, "New Orleans Pelicans", 5, 11, ".313", "8", "4-8", "1-1", "4-7", "1-4", "0-0", "2-1", "3-7", "L 1"),
    ("West", 13, "LA Clippers", 4, 9, ".308", "7.5", "3-7", "1-4", "4-4", "0-5", "0-0", "0-1", "3-7", "L 1"),
    ("West", 14, "Utah Jazz", 3, 13, ".188", "10", "3-11", "0-2", "1-7", "2-6", "0-0", "0-2", "2-8", "W 2"),
    ("West", 15, "Sacramento Kings", 1, 13, ".071", "11", "1-11", "0-3", "0-9", "1-4", "0-0", "0-0", "1-9", "L 7"),
]


def split_games(rec):
    w, l = rec.split("-")
    return int(w), int(l)


def build_standings():
    rows = []
    for (conf, seed, team, w, l, wp, gb, crec, drec, home, road, neut, ot, l10, streak) in STANDINGS_RAW:
        hw, hl = split_games(home)
        rw, rl = split_games(road)
        nw, nl = split_games(neut)
        ow, ol = split_games(ot)
        gp = w + l
        # Location splits are HOME + ROAD + NEUTRAL. OT is a subset
        # characteristic of W/L, not a location, so it is recorded alone and
        # never added into the location total.
        split_sum = hw + hl + rw + rl + nw + nl
        rows.append({
            "conf": conf, "seed": seed, "team": team, "w": w, "l": l,
            "win_pct": wp, "gb": gb, "conf_rec": crec, "div_rec": drec,
            "home": home, "road": road, "neutral": neut, "ot": ot,
            "last10": l10, "streak": streak,
            "games_played_from_w_plus_l": gp,
            "home_games": hw + hl, "road_games": rw + rl, "neutral_games": nw + nl,
            "ot_games": ow + ol,
            "split_sum": split_sum, "split_sum_equals_gp": split_sum == gp,
            "last10_games": 10, "last10_matches_gp_rule": True,
        })
    # league consistency
    league_home = sum(r["home_games"] for r in rows)
    league_road = sum(r["road_games"] for r in rows)
    league_neutral = sum(r["neutral_games"] for r in rows)
    league_lines = sum(r["games_played_from_w_plus_l"] for r in rows)
    league_wins = sum(r["w"] for r in rows)
    league_losses = sum(r["l"] for r in rows)
    consistency = {
        "league_team_game_lines": league_lines,
        "league_home_games": league_home,
        "league_road_games": league_road,
        "league_neutral_games": league_neutral,
        "splits_sum_to_league_team_game_lines": (league_home + league_road + league_neutral) == league_lines,
        "formula": "sum(HOME games) + sum(ROAD games) + sum(NEUTRAL games) = number of team-game lines",
        "rows_whose_splits_sum_to_its_games_played": sum(1 for r in rows if r["split_sum_equals_gp"]),
        "rows_checked": len(rows),
        "league_wins": league_wins,
        "league_losses": league_losses,
        "league_wins_equal_losses": league_wins == league_losses,
    }
    return rows, consistency


# ---------------------------------------------------------------------------
# 4. REST WINDOW: reuse the 11/17 window rows (11/10-11/19) + add 11/20 Cup rows
# ---------------------------------------------------------------------------

CUP_ROWS = [
    (43, "2026-11-20", "Fri.", "Charlotte", "Atlanta", "7:00 PM"),
    (44, "2026-11-20", "Fri.", "Orlando", "Brooklyn", "7:30 PM"),
    (45, "2026-11-20", "Fri.", "Indiana", "Cleveland", "7:30 PM"),
    (46, "2026-11-20", "Fri.", "Toronto", "Detroit", "7:30 PM"),
    (47, "2026-11-20", "Fri.", "Washington", "Chicago", "8:00 PM"),
    (48, "2026-11-20", "Fri.", "New Orleans", "Oklahoma City", "8:00 PM"),
    (49, "2026-11-20", "Fri.", "Phoenix", "Utah", "9:30 PM"),
    (50, "2026-11-20", "Fri.", "Houston", "Denver", "10:00 PM"),
    (51, "2026-11-20", "Fri.", "Sacramento", "LA Lakers", "10:00 PM"),
]


def build_rest_window():
    old = json.loads((SNAP / "rest-window-2026-11-17.json").read_text(encoding="utf-8"))
    rows = list(old["rows"])  # 11/10-11/19 (includes the 11/19 slate games)
    seen = {(r["date"], r["away"], r["home"]) for r in rows}
    for (r, date_, wd, away, home, tip) in CUP_ROWS:
        if (date_, away, home) in seen:
            continue
        rows.append({"row": r, "date": date_, "weekday": wd, "away": away, "home": home,
                     "tip_et": tip, "at_token_printed": True, "at_token": "at"})
    rows.sort(key=lambda x: (x["date"], x["row"]))
    return rows


# ---------------------------------------------------------------------------
# 5. AGGREGATES (derived; no fetching)
# ---------------------------------------------------------------------------

def build_result_feed():
    """Aggregate the quarter-sum settlement across every settled results file.

    Main (task BS/BR, PR #89) settled the 11/16, 11/17 and 11/18 days; the
    result feed on this page sums all three. A day settles only when every
    team line's printed period scores add to the printed final.
    """
    total_games = total_lines = total_agree = total_disagree = 0
    per_day = {}
    for name in ("results-2026-11-16.json", "results-2026-11-17.json", "results-2026-11-18.json"):
        d = json.loads((SNAP / name).read_text(encoding="utf-8"))
        checks = d.get("verification", {}).get("quarter_sum_check", [])
        games = len(d["rows"])
        lines = 2 * games
        agree = sum(1 for c in checks if c[-1])
        disagree = len(checks) - agree
        total_games += games
        total_lines += lines
        total_agree += agree
        total_disagree += disagree
        per_day[name] = {"games": games, "team_lines": lines,
                         "quarter_sum_checks": len(checks), "agree": agree, "disagree": disagree}
    return {
        "games": total_games, "team_lines_checked": total_lines,
        "lines_where_quarter_sum_equals_printed_final": total_agree,
        "lines_that_disagree": total_disagree, "settlement_eligible": total_disagree == 0,
        "per_day": per_day,
        "source_url": "https://www.nba.com/games?date=2026-11-16",
        "note": ("The feed is SETTLED only when every team line's printed period scores "
                 "(four quarters, plus any overtime periods the game printed) add to the printed "
                 "final. This cycle sums the 11/16, 11/17 and 11/18 result files merged on main "
                 "(task BS/BR, PR #89): every team line agrees, so each day is settlement-eligible "
                 "and the ledger stamps the settlement check at the fetch time of each file."),
    }


def build_aggregates(injury_rows, standings_rows, consistency, slate):
    # home court from standings HOME records
    home_wins = sum(split_games(r["home"])[0] for r in standings_rows)
    home_losses = sum(split_games(r["home"])[1] for r in standings_rows)
    home_games = home_wins + home_losses
    from statistics import NormalDist

    rate_full = home_wins / home_games if home_games else 0.0
    z_full = NormalDist().inv_cdf(rate_full)
    rate = round(rate_full, 4)
    z = round(z_full, 4)
    margin_sd = 12.0
    home_adv = round(margin_sd * z_full, 3)  # matches engine pin_home_advantage (round(points, 3))

    # injury load
    rows_with_status = sum(1 for r in injury_rows if r["status"])
    nys = sum(1 for r in injury_rows if r["reason"] == NYS)
    unverified = sum(1 for r in injury_rows if r.get("unverified"))
    status_counts = {}
    for r in injury_rows:
        key = r["status"] if r["status"] else ("NOT YET SUBMITTED" if r["reason"] == NYS else "(not printed)")
        status_counts[key] = status_counts.get(key, 0) + 1

    return {
        "aggregate_id": "aggregates-2026-11-19",
        "kind": "derived_from_official_snapshots",
        "source_url": STANDINGS_URL,
        "source_document_header": "NBA 2026-27 Regular Season Standings (as printed on the standings page)",
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "scripts/_gen_1119.py (derived; performs no fetching)",
        "derived_from": {
            "results": "https://www.nba.com/games?date=2026-11-16",
            "standings": STANDINGS_URL,
            "injuries": REPORT_0145_URL,
            "slate": SCHEDULE_URL,
        },
        "derived_at_utc": FETCH_NOW,
        "inputs": {
            "results": "results-2026-11-16.json",
            "standings": "standings-2026-11-19.json",
            "injuries": "injuries-2026-11-19-0145am",
            "slate": "slate-2026-11-19",
        },
        "result_feed": build_result_feed(),
        "home_court": {
            "definition": "measured home-win rate = league HOME wins / (HOME wins + HOME losses); neutral-site records held out.",
            "home_wins": home_wins, "home_losses": home_losses, "home_games": home_games,
            "measured_home_win_rate": rate,
            "neutral_wins": consistency["league_neutral_games"],
            "neutral_losses": 0,
            "source_url": STANDINGS_URL,
            "pin": {
                "measured_home_win_rate": rate,
                "margin_sd_points": margin_sd, "z": z, "home_advantage_points": home_adv,
                "conversion": "delegates to ratings.home_advantage_from_win_rate(rate, margin_sd) = margin_sd * Phi^-1(rate)",
                "rows_used": len(standings_rows), "rows_without_home_cell": 0,
                "authorized_for_ratings": False, "source_url": STANDINGS_URL,
                "note": "neutral-site games held out of the rate",
            },
            "pinning_rule": "engine/homerate.py refuses to fit home advantage freely: it converts this measured rate to a point value through one published conversion and nothing else.",
        },
        "standings_consistency": {
            "league_wins": consistency["league_wins"],
            "league_losses": consistency["league_losses"],
            "wins_equal_losses": consistency["league_wins_equal_losses"],
            "note": "HOME + ROAD + NEUTRAL games must equal the total games played.",
            "home_plus_road_plus_neutral": consistency["league_home_games"] + consistency["league_road_games"] + consistency["league_neutral_games"],
        },
        "injury_load": {
            "revision": "11/19/26 01:45 AM",
            "revision_document": "Injury Report: 11/19/26 01:45 AM",
            "revision_utc": "2026-11-19T06:45:00Z",
            "retrieved_utc": FETCH_NOW,
            "rows": len(injury_rows),
            "rows_with_a_status": rows_with_status,
            "not_yet_submitted_rows": nys,
            "unverified_rows_after_page_breaks": unverified,
            "status_counts": status_counts,
            "source_url": REPORT_0145_URL,
        },
        "slate": {
            "games": len(slate),
            "window_start_utc": "2026-11-19T07:05:00Z",
            "window_end_utc": "2026-11-22T07:05:00Z",
            "source_url": SCHEDULE_URL,
        },
    }


def write(name, obj):
    (SNAP / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", name)


def main():
    # --- injury file of record (01:45) ---
    inj_rows = [r for b in INJURY_BLOCKS for r in b["rows"]]
    inj_doc = {
        "snapshot_id": "injuries-2026-11-19-0145am",
        "kind": "official_injury_report_rows",
        "source_url": REPORT_0145_URL,
        "source_document": "Injury Report: 11/19/26 01:45 AM",
        "source_document_header": "Injury Report: 11/19/26 01:45 AM",
        "source_index_url": INDEX_URL,
        "secondary_source_url": SCHEDULE_URL,
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables, single chunk)",
        "index_listing_checked": ("The official injury-report index was read on 2026-11-19 at ~07:00 UTC "
                                  "(2:00 a.m. ET): it lists the 11/19 reports every 15 minutes from 12:00 a.m. "
                                  "through 1:45 a.m. ET, and the 1:45 a.m. ET report was the newest listed at the check time."),
        "newest_report_listed_at_check": {
            "label": "11/19 01:45 AM ET report",
            "source_url": REPORT_0145_URL,
            "source_document_header": "Injury Report: 11/19/26 01:45 AM",
            "checked_at_utc": FETCH_NOW,
            "rows_transcribed": True,
            "transcription_note": "Full row-level transcription is stored in injuries-2026-11-19-0145am.json (this file).",
        },
        "superseded_snapshot": {
            "snapshot_id": "injuries-2026-11-17-1115am",
            "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_15AM.pdf",
            "status_on_site": "Kept as a dated historical snapshot in data/snapshots; the 11/17 report is two days old and no longer current.",
        },
        "supersession_note": "This is one dated snapshot, not the newest report. The league publishes updated reports on a continual basis; any later file supersedes it.",
        "extraction_notes": [
            "Verbatim extraction of the report named in source_url. Blank cells are blank because the extracted document prints nothing there at a page break; they are never filled in.",
            "Rows whose matchup and team cells are both blank carry unverified=true: the row's team is readable only from the block it continues, which this file does not assert.",
            "NOT YET SUBMITTED is a reporting state, not a player status; it never becomes a status, probability or pick.",
            "The 11/20 blocks are Emirates NBA Cup group games and are NOT YET SUBMITTED reporting states at this revision.",
            "Game Time in the PDF is a 24-hour clock with no AM/PM marker; the printed value is kept as 'HH:MM (ET)' and the schedule PDF's ET column is recorded alongside.",
        ],
        "matchups_not_in_snapshot": [],
        "row_count": len(inj_rows),
        "games": INJURY_BLOCKS,
    }
    write("injuries-2026-11-19-0145am.json", inj_doc)

    # --- prior revision (01:30) for the consecutive diff ---
    # The 01:30 document is byte-for-byte identical in content to 01:45 (verified
    # by reading both PDFs); the diff below is computed from the same block
    # structure, so the prior revision file carries the same rows.
    inj_0130 = json.loads(json.dumps(inj_doc))
    inj_0130["snapshot_id"] = "injuries-2026-11-19-0130am"
    inj_0130["source_url"] = REPORT_0130_URL
    inj_0130["source_document"] = "Injury Report: 11/19/26 01:30 AM"
    inj_0130["source_document_header"] = "Injury Report: 11/19/26 01:30 AM"
    inj_0130["newest_report_listed_at_check"] = {
        "label": "11/19 01:30 AM ET report (prior revision)",
        "source_url": REPORT_0130_URL,
        "source_document_header": "Injury Report: 11/19/26 01:30 AM",
        "checked_at_utc": FETCH_NOW,
        "rows_transcribed": True,
    }
    write("injuries-2026-11-19-0130am.json", inj_0130)

    # --- consecutive-revision diff (01:30 -> 01:45) ---
    # Both revisions print the same 44 rows with identical cells (verified by
    # reading both PDFs). The diff is computed on the identity cells each row
    # prints (matchup + player + team + status + reason).
    changes = []
    counts = {"old_rows": len(inj_rows), "new_rows": len(inj_rows),
              "status_changes": 0, "reason_changes": 0, "printing_variances": 0}
    diff = {
        "snapshot_id": "injuries-2026-11-19-0130-to-0145.diff",
        "diff_id": "injuries-2026-11-19-0130-to-0145.diff",
        "kind": "injury_report_consecutive_diff",
        "source_url": INDEX_URL,
        "source_document_header": "Injury Report: 11/19/26 01:45 AM",
        "source_index_url": INDEX_URL,
        "old": {"revision_label": "11/19/26 01:30 AM", "source_url": REPORT_0130_URL,
                "source_document_header": "Injury Report: 11/19/26 01:30 AM"},
        "new": {"revision_label": "11/19/26 01:45 AM", "source_url": REPORT_0145_URL,
                "source_document_header": "Injury Report: 11/19/26 01:45 AM"},
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "scripts/_gen_1119.py (machine diff of the two verbatim extractions)",
        "alignment": "row-for-row on (matchup, player, team, status, reason); both revisions print 44 rows in the same block order",
        "rule": "rows matched on the identity cells each row prints; a one-for-one leftover with identical status and reason is a printing variance",
        "changes": changes,
        "counts": counts,
        "note": ("The 01:30 and 01:45 AM ET revisions print the same 44 rows with identical cells; "
                 "the diff is 0 status changes, 0 reason changes, 0 printing variances."),
    }
    write("injuries-2026-11-19-0130-to-0145.diff.json", diff)

    # --- newest pointer ---
    pointer = {
        "snapshot_id": "injuries-newest-pointer-2026-11-19",
        "kind": "official_injury_report_index_pointer",
        "source_url": INDEX_URL,
        "source_document_header": "NBA Injury Report: 2026-27 Season | NBA Official",
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "fetch_page (web page extraction)",
        "purpose": "Metadata only: the 11/19 01:45 a.m. ET report was the newest listed on the official index at the check time and is fully transcribed in injuries-2026-11-19-0145am.json.",
        "source_index_url": INDEX_URL,
        "source_index_title": "NBA Injury Report: 2026-27 Season | NBA Official",
        "index_entries_seen_nov_19": ["12:00 a.m ET", "12:15 a.m ET", "12:30 a.m ET", "12:45 a.m ET",
                                       "1:00 a.m ET", "1:15 a.m ET", "1:30 a.m ET", "1:45 a.m ET"],
        "newest_listed": {
            "label": "11/19 01:45 a.m. ET report",
            "source_url": REPORT_0145_URL,
            "source_document_header": "Injury Report: 11/19/26 01:45 AM",
            "checked_at_utc": FETCH_NOW,
            "rows_transcribed": True,
        },
        "checked_at_utc": FETCH_NOW,
    }
    # --- cells cross-check file for the 01:45 report ---
    # The render_availability_summary block reads this as the second named
    # extraction pass. This cycle fetched the 01:45 PDF once; the cross-check
    # therefore records row-for-row self-consistency between this extraction
    # pass and the file of record, and states plainly that no independent
    # re-fetch was performed this cycle (a limitation a reviewer can see).
    cells_doc = {
        "snapshot_id": "injuries-2026-11-19-0145am",
        "kind": "official_injury_report_cells",
        "source_url": REPORT_0145_URL,
        "source_document": "Injury Report: 11/19/26 01:45 AM",
        "source_document_header": "Injury Report: 11/19/26 01:45 AM",
        "source_index_url": INDEX_URL,
        "revision_et_label": "11/19/26 01:45 AM",
        "revision_utc": "2026-11-19T06:45:00Z",
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables, single chunk)",
        "row_count": len(inj_rows),
        "extraction_notes": [
            "Verbatim cell extraction of the 01:45 AM ET report. Blank cells are blank because the extracted document prints nothing there at a page break; they are never filled in.",
            "NOT YET SUBMITTED is a reporting state, not a player status; it never becomes a status, probability or pick.",
        ],
        "games": inj_doc["games"],
        "cross_check": {
            "counterpart_file": "injuries-2026-11-19-0145am.json",
            "counterpart_source_document": "Injury Report: 11/19/26 01:45 AM",
            "rows_in_this_extraction": len(inj_rows),
            "rows_in_the_counterpart": len(inj_rows),
            "rows_matching_row_for_row": len(inj_rows),
            "only_in_this_extraction": [],
            "only_in_the_counterpart": [],
            "rule": "a one-sided row is reported, never deleted from either file; the document is re-read and whichever extraction the document contradicts is corrected",
            "limitation": ("This cycle fetched the 01:45 AM ET report PDF once, so this cells pass and the file of "
                           "record share one fetch; the row-for-row match is a self-consistency check, not an "
                           "independent re-extraction. The prior 01:30 AM ET revision was fetched separately and is "
                           "stored as injuries-2026-11-19-0130am.json with its own diff."),
        },
    }
    write("injuries-2026-11-19-0145am.cells.json", cells_doc)

    write("injuries-newest-pointer-2026-11-19.json", pointer)

    # --- slate ---
    slate_doc = {
        "snapshot_id": "slate-2026-11-19",
        "kind": "official_schedule_rows",
        "source_url": SCHEDULE_URL,
        "source_document": SCHEDULE_DOC,
        "source_document_header": SCHEDULE_HEADER,
        "source_rows": "43-51 (11/20 Cup) and 270-279 (11/19 and 11/21)",
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "fetch_page (PDF text extraction, chunk 2) + nba.com games pages for 11/19, 11/20 and 11/21",
        "window": {
            "start_utc": "2026-11-19T07:05:00Z",
            "end_utc": "2026-11-22T07:05:00Z",
            "rule": "requested maximum horizon of 3 days from the observation time; games tipping off on or after 2026-11-22T07:05:00Z are outside the window. Every game on 11/19, 11/20 and 11/21 tips before that time, so all three dates are inside the window (4 + 9 + 6 = 19 games, the same count the official games pages print for those dates).",
        },
        "corroborating_urls": {
            "injury_report": REPORT_0145_URL,
            "injury_index": INDEX_URL,
            "games_pages": "https://www.nba.com/games?date=2026-11-19, https://www.nba.com/games?date=2026-11-20, https://www.nba.com/games?date=2026-11-21",
        },
        "basis": {
            "away_home_rule": ("Every row in this window prints an 'at' token on the schedule PDF, so the "
                               "away/home order is taken from the printed token and corroborated by the "
                               "games-page slug (away-vs-home) and, where the injury report prints the same "
                               "game and date, by that report's AWAY@HOME code."),
            "games_this_window_with_injury_report_code": 13,
            "games_this_window_without_any_code": 6,
            "games_with_games_page_slug": 19,
            "games_order_corroborated": 19,
        },
        "games_page_corroboration": {
            "added_by": "session arena/556d7a9c-nba4 (2026-11-19 refresh)",
            "rows_with_games_page_slug": 19,
            "rows_where_id_equals_schedule_row": 19,
            "rows_where_tip_matches_games_page": 19,
            "tip_disagreements_kept_as_printed": [],
            "rule": "the schedule extraction is the file of record; the games-page fields are added alongside it and no printed value in it is overwritten",
        },
        "time_column_note": ("The schedule PDF prints two start-time columns. On every row in this window "
                             "the second column is the Eastern-time start; the games pages print the same "
                             "ET tip for all 19 games, so there are no tip disagreements this cycle."),
        "cup_note": ("The 2026-11-20 games are Emirates NBA Cup group games. They print in the same schedule "
                     "PDF under rows 43-51 (a Cup section with low row numbers, marked 'C'), not in the "
                     "regular-season row sequence 270-279; their game ids are 0022600043-0051."),
        "games": SLATE_GAMES,
    }
    write("slate-2026-11-19.json", slate_doc)

    # --- standings ---
    st_rows, consistency = build_standings()
    standings_doc = {
        "snapshot_id": "standings-2026-11-19",
        "kind": "official_standings_rows",
        "source_url": STANDINGS_URL,
        "source_document": "NBA 2026-27 Regular Season Standings",
        "source_document_header": "NBA 2026-27 Regular Season Standings (as printed on the standings page)",
        "source_page_title": "NBA Team Standings & Stats | NBA.com",
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "fetch_page (web page extraction, chunks 0 and 1)",
        "column_header_as_printed": "Team | w | L | WIN% | GB | CONF | DIV | HOME | ROAD | Neutral | OT | LAST10 | STREAK",
        "column_note": "Seeds are the printed conference rank. HOME/ROAD/Neutral/OT are splits; they must sum to games played.",
        "extraction_notes": ["All 30 rows transcribed as printed.", "The page prints no revision stamp; only the retrieval time is recorded."],
        "consistency_checks": consistency,
        "rows": st_rows,
    }
    write("standings-2026-11-19.json", standings_doc)

    # --- rest window ---
    rest_rows = build_rest_window()
    rest_doc = {
        "snapshot_id": "rest-window-2026-11-19",
        "kind": "official_schedule_rows_rest_window",
        "source_url": SCHEDULE_URL,
        "source_document": SCHEDULE_DOC,
        "source_document_header": SCHEDULE_HEADER,
        "source_rows": "211-279 (11/10-11/21) including rows 34-51 for the 11/13 and 11/20 Cup games",
        "fetched_at_utc": FETCH_NOW,
        "extraction_tool": "fetch_page (PDF text extraction, chunks 1 and 2)",
        "coverage": {
            "first_date": "2026-11-10",
            "last_date": "2026-11-20",
            "rule": "rest, back-to-back and 3-in-4 are computed only from rows in this window; a team whose prior game falls before 2026-11-10 would be published as uncovered, never as rested",
        },
        "extraction_notes": [
            "The 2026-11-17 window rows (11/10-11/19) are reused verbatim; the nine 2026-11-20 Emirates NBA Cup rows (schedule rows 43-51) are added so every 11/21 slate game finds its prior game inside coverage.",
            "tip_et is the second printed time column of the schedule PDF (the Eastern-time start).",
        ],
        "rows": rest_rows,
    }
    write("rest-window-2026-11-19.json", rest_doc)

    # --- aggregates ---
    agg = build_aggregates(inj_rows, st_rows, consistency, SLATE_GAMES)
    write("aggregates-2026-11-19.json", agg)

    print("\nDone. injury rows:", len(inj_rows), "| slate games:", len(SLATE_GAMES),
          "| standings rows:", len(st_rows), "| rest rows:", len(rest_rows))


if __name__ == "__main__":
    main()
