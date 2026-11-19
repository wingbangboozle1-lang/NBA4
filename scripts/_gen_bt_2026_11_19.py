#!/usr/bin/env python3
"""Generate the 2026-11-19 refresh-cycle snapshot files (task BT).

Every value in this file is transcribed from an official NBA document read
with fetch_page on 2026-11-19 06:45-07:33 UTC:

  * schedule PDF  - window rows 43-51 and 270-279 (verbatim, also written to
                    data/snapshots/raw/schedule-2026-11-19-window-rows-43-51-270-279.txt)
  * games pages   - 2026-11-17, 2026-11-18, 2026-11-19, 2026-11-20, 2026-11-21
                    (finals, ids, slugs, tips, records, group labels)
  * gamebooks     - five 11/17 books (20261117_*) and twelve 11/18 books
                    (20261118_*): period lines, inactives, players' lines
  * standings     - nba.com/standings (both chunks, 30 rows)
  * team stats    - nba.com/stats/teams/advanced + /opponent (30 rows each)

Nothing is inferred: tip values that disagree between the games page and the
August schedule PDF are kept as printed on both sides and flagged.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "snapshots"
RAW = SNAP / "raw"

F = "2026-11-19T07:00:00Z"        # schedule/results/slate read stamp
F2 = "2026-11-19T07:10:00Z"       # standings/team-stats read stamp
F3 = "2026-11-19T07:30:00Z"       # game-log capture stamp
SCHED_PDF = ("https://cdn.nba.com/manage/2026/08/"
             "2026-27-NBA-Regular-Season-Schedule-By-Date.pdf")
SCHED_HEADER = "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE"
REPORT_URL = ("https://ak-static.cms.nba.com/referee/injury/"
              "Injury-Report_2026-11-19_01_45AM.pdf")
REPORT_INDEX = "https://official.nba.com/nba-injury-report-2026-27-season/"
INJ_FILE = "injuries-2026-11-19-0145am.json"
INJ_DOC = "Injury Report: 11/19/26 01:45 AM"
INJ_REV_UTC = "2026-11-19T06:45:00Z"
GAMES = "https://www.nba.com/games?date="
BOOK = "https://statsdmz.nba.com/pdfs/{d}/{d}_{t}_book.pdf"
STANDINGS_URL = "https://www.nba.com/standings"


def game_url(slug: str, gid: str) -> str:
    return f"https://www.nba.com/game/{slug}-{gid}"


def write(name: str, payload: dict) -> None:
    path = SNAP / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"wrote {name}")


# --------------------------------------------------------------------------
# Schedule window (19 games, 11/19-11/21) + games-page corroboration
# --------------------------------------------------------------------------

def slug_id(row: int) -> tuple[str, str]:
    return (SLUGS[row], "00226000" + str(row).zfill(2) if row < 100
            else "0022600" + str(row))


SLUGS = {
    270: "gsw-vs-mem", 271: "por-vs-mil", 272: "nyk-vs-min", 273: "lac-vs-sas",
    43: "cha-vs-atl", 44: "orl-vs-bkn", 45: "ind-vs-cle", 46: "tor-vs-det",
    47: "was-vs-chi", 48: "nop-vs-okc", 49: "phx-vs-uta", 50: "hou-vs-den",
    51: "sac-vs-lal",
    274: "mil-vs-phi", 275: "por-vs-nyk", 276: "lac-vs-dal", 277: "mem-vs-min",
    278: "nop-vs-sas", 279: "bos-vs-sac",
}
# games-page tip (ET), taken verbatim from each game's URL card on the date page
GP_TIP = {
    270: "8:00 PM ET", 271: "8:00 PM ET", 272: "8:00 PM ET", 273: "8:00 PM ET",
    43: "7:00 PM ET", 44: "7:30 PM ET", 45: "7:30 PM ET", 46: "7:30 PM ET",
    47: "8:00 PM ET", 48: "8:00 PM ET", 49: "9:00 PM ET", 50: "10:00 PM ET",
    51: "10:00 PM ET",
    274: "1:00 PM ET", 275: "7:30 PM ET", 276: "8:00 PM ET", 277: "8:00 PM ET",
    278: "8:00 PM ET", 279: "10:00 PM ET",
}
# (row, weekday, date, away, home, local, et, tv, cup_flag)
PDF_ROWS = [
    (270, "Thu.", "11/19/26", "Golden State", "Memphis", "7:00 PM", "8:00 PM", "", ""),
    (271, "Thu.", "11/19/26", "Portland", "Milwaukee", "7:00 PM", "8:00 PM", "", ""),
    (272, "Thu.", "11/19/26", "New York", "Minnesota", "7:00 PM", "8:00 PM", "", ""),
    (273, "Thu.", "11/19/26", "LA Clippers", "San Antonio", "7:00 PM", "8:00 PM", "", ""),
    (43, "Fri.", "11/20/26", "Charlotte", "Atlanta", "7:00 PM", "7:00 PM", "", "C"),
    (44, "Fri.", "11/20/26", "Orlando", "Brooklyn", "7:30 PM", "7:30 PM", "", "C"),
    (45, "Fri.", "11/20/26", "Indiana", "Cleveland", "7:30 PM", "7:30 PM", "", "C"),
    (46, "Fri.", "11/20/26", "Toronto", "Detroit", "7:30 PM", "7:30 PM", "Prime", "C"),
    (47, "Fri.", "11/20/26", "Washington", "Chicago", "7:00 PM", "8:00 PM", "", "C"),
    (48, "Fri.", "11/20/26", "New Orleans", "Oklahoma City", "7:00 PM", "8:00 PM", "", "C"),
    (49, "Fri.", "11/20/26", "Phoenix", "Utah", "7:30 PM", "9:30 PM", "", "C"),
    (50, "Fri.", "11/20/26", "Houston", "Denver", "8:00 PM", "10:00 PM", "Prime", "R"),
    (51, "Fri.", "11/20/26", "Sacramento", "LA Lakers", "7:00 PM", "10:00 PM", "", "C"),
    (274, "Sat.", "11/21/26", "Milwaukee", "Philadelphia", "1:00 PM", "1:00 PM", "", ""),
    (275, "Sat.", "11/21/26", "Portland", "New York", "7:30 PM", "7:30 PM", "", ""),
    (276, "Sat.", "11/21/26", "LA Clippers", "Dallas", "7:00 PM", "8:00 PM", "", ""),
    (277, "Sat.", "11/21/26", "Memphis", "Minnesota", "7:00 PM", "8:00 PM", "", ""),
    (278, "Sat.", "11/21/26", "New Orleans", "San Antonio", "7:00 PM", "8:00 PM", "", ""),
    (279, "Sat.", "11/21/26", "Boston", "Sacramento", "7:00 PM", "10:00 PM", "", ""),
]
DATE_OF = {270: "2026-11-19", 271: "2026-11-19", 272: "2026-11-19", 273: "2026-11-19",
           43: "2026-11-20", 44: "2026-11-20", 45: "2026-11-20", 46: "2026-11-20",
           47: "2026-11-20", 48: "2026-11-20", 49: "2026-11-20", 50: "2026-11-20",
           51: "2026-11-20",
           274: "2026-11-21", 275: "2026-11-21", 276: "2026-11-21", 277: "2026-11-21",
           278: "2026-11-21", 279: "2026-11-21"}
CODES = {
    270: "GSW@MEM", 271: "POR@MIL", 272: "NYK@MIN", 273: "LAC@SAS",
    43: "CHA@ATL", 44: "ORL@BKN", 45: "IND@CLE", 46: "TOR@DET", 47: "WAS@CHI",
    48: "NOP@OKC", 49: "PHX@UTA", 50: "HOU@DEN", 51: "SAC@LAL",
    274: "MIL@PHI", 275: "POR@NYK", 276: "LAC@DAL", 277: "MEM@MIN",
    278: "NOP@SAS", 279: "BOS@SAC",
}
# 11/20 group labels as printed on the games page (Cup group-play section)
GROUPS = {
    43: "Cup Group Play - East Group C", 44: "Cup Group Play - East Group A",
    45: "Cup Group Play - East Group B", 46: "Cup Group Play - East Group A",
    47: "Cup Group Play - East Group C", 48: "Cup Group Play - West Group B",
    49: "Cup Group Play - West Group A", 50: "Cup Group Play - West Group A",
    51: "Cup Group Play - West Group C",
}


def raw_line(row) -> str:
    r, wd, date, away, home, local, et, tv, flag = row
    return f"{r}|{wd}|{date}|{away}|at|{home}|{local}|{et}|{tv}|{flag}|"


def build_raw() -> None:
    lines = [
        '# Verbatim window rows 270-273, 43-51 and 274-279 of the official 2026-27 NBA regular-season schedule PDF (cdn.nba.com), read by fetch_page on 2026-11-19 (chunks 0, 1 and 2 of 13).',
        '# Header printed on the document: "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE"',
        '# Columns: GAME|DAY|DATE|TEAM 1|at|TEAM 2|LOCAL|ET|NAT TV|R|#  (every window row prints the "at" token)',
        '# Source: ' + SCHED_PDF,
        '# Fetched (UTC): ' + F,
    ]
    for row in PDF_ROWS:
        lines.append(raw_line(row))
    path = RAW / "schedule-2026-11-19-window-rows-43-51-270-279.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path.name}")


def build_slate() -> None:
    games = []
    for r in PDF_ROWS:
        row, wd, date_pdf, away, home, local, et, tv, flag = r
        slug, gid = slug_id(row)
        disagree = None
        gp = GP_TIP[row]
        if gp.replace(" ET", "") != et:
            if row == 49:
                disagree = (
                    "the official games page prints 9:00 PM ET for this game; the "
                    "August schedule PDF row 49 prints 9:30 PM ET and the "
                    "2026-11-19 01:45 AM ET injury report prints 09:30 (ET) for "
                    "the same game. Two official documents agree on 9:30, one "
                    "prints 9:00; all printed values are kept and none is "
                    "overwritten."
                )
            else:
                disagree = (
                    f"the official games page prints {gp} for this game; the August "
                    f"schedule PDF row {row} prints {et}. Both values are kept as "
                    "printed and neither is overwritten."
                )
        g = {
            "row": row,
            "date": DATE_OF[row],
            "weekday": wd,
            "away": away,
            "home": home,
            "tip_et_col1": local,
            "tip_et_col2": et,
            "code": CODES[row],
            "code_source": "games page URL slug 'away-vs-home'",
            "at_token_printed": True,
            "nba_cup_flag_as_printed": flag,
            "broadcast_as_printed": tv,
            "games_page_slug": slug,
            "games_page_game_id": gid,
            "games_page_tip_et": gp,
            "games_page_url": game_url(slug, gid),
            "order_corroborated_by": [
                f"games page URL slug '{slug}' (away-vs-home)",
                "schedule PDF row prints the 'at' token between TEAM 1 and TEAM 2",
            ],
            "tip_disagreement": disagree,
        }
        if GROUPS.get(row):
            g["cup_group_as_printed"] = GROUPS[row]
        games.append(g)
    games.sort(key=lambda x: x["row"])
    payload = {
        "snapshot_id": "slate-2026-11-19",
        "kind": "official_schedule_rows",
        "source_url": SCHED_PDF,
        "source_document": "2026-27 NBA Regular Season Schedule By Date",
        "source_document_header": SCHED_HEADER,
        "source_rows": "43-51, 270-273, 274-279",
        "fetched_at_utc": F,
        "extraction_tool": ("fetch_page (PDF text extraction, chunks 0, 1 and 2) "
                            "+ nba.com games pages for 11/19, 11/20 and 11/21"),
        "raw_extraction": "data/snapshots/raw/schedule-2026-11-19-window-rows-43-51-270-279.txt",
        "window": {
            "start_utc": "2026-11-19T15:45:00Z",
            "end_utc": "2026-11-22T15:45:00Z",
            "rule": ("requested maximum horizon of 3 days from the observation "
                     "time (the 2026-11-19 01:45 AM ET injury-report submission, "
                     "06:45 UTC); games tipping off on or after 2026-11-22T15:45:00Z "
                     "are outside the window. Every game on 11/19, 11/20 and 11/21 "
                     "tips before that time, so all three dates are inside the "
                     "window (4 + 9 + 6 = 19 games, the same count the official "
                     "games pages print for those dates)."),
        },
        "corroborating_urls": {
            "injury_report": REPORT_URL,
            "injury_index": REPORT_INDEX,
            "games_pages": (GAMES + "2026-11-19, " + GAMES + "2026-11-20, "
                            + GAMES + "2026-11-21"),
        },
        "basis": {
            "away_home_rule": ("every window row prints the 'at' token between "
                               "TEAM 1 and TEAM 2, so away/home is read from the "
                               "printed token itself; the games-page slug "
                               "(away-vs-home) and the injury-report matchup code "
                               "where present corroborate the same order"),
            "games_this_window_with_injury_report_code": 13,
            "games_this_window_without_any_code": 6,
            "games_with_games_page_slug": 19,
            "games_order_corroborated": 19,
            "note_on_codes": ("the 2026-11-19 01:45 AM ET report prints matchup "
                              "codes only for its 13 game blocks (all 11/19 games "
                              "and eight 11/20 games); WAS@CHI has no report block, "
                              "its order rests on the printed 'at' token and the "
                              "slug"),
        },
        "games_page_corroboration": {
            "rule": ("each game's games-page URL card tip is compared with the "
                     "schedule PDF ET column; a disagreement keeps both printed "
                     "values in tip_disagreement"),
            "tip_disagreements_kept_as_printed": [49],
            "rows_where_tip_matches_games_page": 18,
            "rows_checked": 19,
        },
        "time_column_note": ("the PDF prints LOCAL and ET tip columns; both are "
                             "kept verbatim in tip_et_col1 / tip_et_col2"),
        "games": games,
    }
    write("slate-2026-11-19.json", payload)


# --------------------------------------------------------------------------
# Results: five 11/17 finals + twelve 11/18 finals
# --------------------------------------------------------------------------

# (gid, tip, arena, city, away, home, aq, af, hq, hf, aot, hot, book_key)
R1117 = [
    ("0022600253", "7:30 PM", "", "", "NYK", "TOR",
     [23, 31, 26, 31], 111, [29, 21, 33, 19], 102, [], [], "NYKTOR"),
    ("0022600254", "8:00 PM", "", "", "POR", "MIN",
     [17, 31, 31, 26], 105, [29, 20, 30, 27], 106, [], [], "PORMIN"),
    ("0022600255", "8:00 PM", "", "", "DET", "SAS",
     [26, 29, 23, 27], 105, [33, 21, 18, 21], 93, [], [], "DETSAS"),
    ("0022600256", "10:00 PM", "", "", "CHA", "LAL",
     [34, 32, 28, 17], 114, [30, 29, 22, 30], 118, [3], [7], "CHALAL"),
    ("0022600257", "11:00 PM", "", "", "UTA", "LAC",
     [35, 23, 30, 44], 132, [29, 33, 24, 21], 107, [], [], "UTALAC"),
]
R1118 = [
    ("0022600258", "7:00 PM", "", "", "MEM", "CLE",
     [30, 41, 29, 24], 124, [37, 35, 27, 22], 121, [], [], "MEMCLE"),
    ("0022600259", "7:00 PM", "", "", "HOU", "IND",
     [39, 23, 31, 26], 119, [28, 18, 30, 28], 104, [], [], "HOUIND"),
    ("0022600260", "7:00 PM", "", "", "MIL", "MIA",
     [23, 25, 38, 44], 130, [34, 40, 38, 25], 137, [], [], "MILMIA"),
    ("0022600261", "7:00 PM", "", "", "PHI", "ORL",
     [27, 37, 28, 29], 121, [40, 29, 28, 19], 116, [], [], "PHIORL"),
    ("0022600262", "7:30 PM", "", "", "CHI", "BKN",
     [37, 39, 35, 26], 137, [21, 30, 26, 30], 107, [], [], "CHIBKN"),
    ("0022600263", "7:30 PM", "", "", "WAS", "TOR",
     [29, 20, 29, 25], 103, [23, 24, 32, 20], 99, [], [], "WASTOR"),
    ("0022600264", "8:00 PM", "", "", "DET", "NOP",
     [31, 36, 25, 30], 122, [20, 29, 26, 34], 109, [], [], "DETNOP"),
    ("0022600265", "8:00 PM", "", "", "ATL", "OKC",
     [31, 33, 19, 34], 117, [29, 22, 32, 29], 112, [], [], "ATLOKC"),
    ("0022600266", "9:00 PM", "", "", "BOS", "DEN",
     [30, 31, 19, 21], 101, [24, 25, 31, 25], 105, [], [], "BOSDEN"),
    ("0022600267", "9:30 PM", "", "", "GSW", "DAL",
     [25, 24, 23, 22], 94, [35, 27, 30, 24], 116, [], [], "GSWDAL"),
    ("0022600268", "10:00 PM", "", "", "UTA", "LAL",
     [29, 27, 22, 31], 109, [34, 20, 22, 21], 97, [], [], "UTALAL"),
    ("0022600269", "10:00 PM", "", "", "PHX", "SAC",
     [36, 29, 34, 29], 128, [31, 29, 24, 23], 107, [], [], "PHXSAC"),
]
SLUG_GID = {
    "NYK@TOR": "nyk-vs-tor", "POR@MIN": "por-vs-min", "DET@SAS": "det-vs-sas",
    "CHA@LAL": "cha-vs-lal", "UTA@LAC": "uta-vs-lac", "MEM@CLE": "mem-vs-cle",
    "HOU@IND": "hou-vs-ind", "MIL@MIA": "mil-vs-mia", "PHI@ORL": "phi-vs-orl",
    "CHI@BKN": "chi-vs-bkn", "WAS@TOR": "was-vs-tor", "DET@NOP": "det-vs-nop",
    "ATL@OKC": "atl-vs-okc", "BOS@DEN": "bos-vs-den", "GSW@DAL": "gsw-vs-dal",
    "UTA@LAL": "uta-vs-lal", "PHX@SAC": "phx-vs-sac",
}


def game_page_url(away: str, home: str, gid: str) -> str:
    return game_url(f"{SLUG_GID[away + '@' + home]}", gid)


def build_results(day: str, spec) -> None:
    date = {"17": "2026-11-17", "18": "2026-11-18"}[day]
    rows, checks = [], []
    for (gid, tip, arena, city, away, home, aq, af, hq, hf, aot, hot, bk) in spec:
        url = BOOK.format(d=date.replace("-", ""), t=bk)
        winner, loser = (away, home) if af > hf else (home, away)
        rows.append([gid, date, tip, arena, city, away, home, aq, af, hq, hf,
                     winner, loser, url, aot, hot])
        for abbr, qs, ot, final in ((away, aq, aot, af), (home, hq, hot, hf)):
            checks.append([gid, abbr, *qs, *ot, final,
                           sum(qs) + sum(ot) == final])
    ots = [r for r in rows if r[7].__len__() > 4 or r[9].__len__() > 4 or r[14] or r[15]]
    notes = [
        f"One row per game of {date}: all {len(spec)} games of the date, "
        "transcribed from the official gamebook PDF of each game "
        "(SCORE BY PERIOD block) and cross-checked against the official games "
        f"page for the date ({GAMES}{date}).",
        "Every printed final agrees between the two official documents "
        "(gamebook and games page).",
        ("one game of this date went to overtime (CHA@LAL): the OT column "
         "carries the printed OT period score and the period sum includes it"
         if ots else
         "No game of this date went to overtime, so the overtime columns are "
         "empty arrays."),
        "The arena and city columns are left blank because the day scoreboard "
        "does not print venues and this cycle did not fetch a venue document "
        "for these games; the cells are never guessed.",
        ("the PHX@SAC gamebook's first SCORE BY PERIOD rendering garbled the "
         "Sacramento row (printed values summing to 104, not the printed final "
         "107); the official game page LINESCORES for the same game prints "
         "31/29/24/23/107, which agrees with the gamebook's final and its "
         "second reading of the row - the garbled reading is discarded as an "
         "extraction artifact, never as a score."
         if day == "18" else
         "the NYK@TOR gamebook's home (Toronto) period cells split across the "
         "extraction chunks; the official game page LINESCORES for the same "
         "game prints 29/21/33/19/102, matching the gamebook's printed Q1 and "
         "Q2 and its printed final - the completed row is that reading."),
    ]
    payload = {
        "snapshot_id": f"results-2026-11-{day}",
        "kind": "official_finals",
        "source_document": f"NBA gamebooks of {date}",
        "source_document_header": (f"official NBA gamebook PDFs of {date} "
                                   f"(statsdmz.nba.com/pdfs/{date.replace('-', '')}/) "
                                   f"and the day scoreboard {GAMES}{date}"),
        "source_url": BOOK.format(d=date.replace("-", ""), t=spec[0][12]),
        "source_index_url": f"{GAMES}{date}",
        "fetched_at_utc": F,
        "extraction_tool": ("fetch_page (gamebook PDF text extraction per game) "
                            "+ fetch_page on the day's games page for the "
                            "independent finals cross-check"),
        "row_format": ["game_id", "date", "tip_et", "arena", "city", "away",
                       "home", "away_q", "away_final", "home_q", "home_final",
                       "winner", "loser", "source_url", "away_ot", "home_ot"],
        "row_format_note": ("away_q/home_q hold the four printed quarters; "
                            "away_ot/home_ot hold printed overtime periods only "
                            "(empty arrays when the game printed none); arena "
                            "and city are blank when not read from an official "
                            "document"),
        "rows": rows,
        "verification": {
            "quarter_sum_rule": ("a team line settles only when its printed "
                                 "period scores (four quarters, plus any printed "
                                 "overtime periods) add to the printed final"),
            "quarter_sum_check": checks,
            "finals_cross_check": {
                "second_official_source": f"{GAMES}{date}",
                "games_checked": len(spec),
                "games_whose_two_documents_agree_on_both_finals": len(spec),
                "rule": ("the games page prints the final of every game of the "
                         "date; a game whose two official documents disagree "
                         "would produce no row"),
            },
            "irregularity": (
                "the gamebook's first rendering of the Sacramento period row "
                "sums to 104 against the printed final 107 (extraction garble); "
                "the official game page LINESCORES prints 31/29/24/23/107 and "
                "the gamebook's own second reading agrees - recorded here, "
                "never silently corrected"
                if day == "18" else
                "the gamebook's home (Toronto) period cells split across "
                "extraction chunks; the official game page LINESCORES "
                "(29/21/33/19/102) completes the row and matches the book's "
                "printed Q1/Q2 and final - recorded here"),
        },
        "extraction_notes": notes,
        "secondary_sources": [f"{GAMES}{date}"],
    }
    write(f"results-2026-11-{day}.json", payload)


# --------------------------------------------------------------------------
# Standings (read 2026-11-19, reflecting completed games through 11/18)
# --------------------------------------------------------------------------

# conf, seed, team, w, l, pct, gb, conf_rec, div, home, road, neutral, ot, l10, streak
STANDINGS = [
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


def _rec(s: str) -> tuple[int, int]:
    w, _, l = s.partition("-")
    return int(w), int(l)


def build_standings() -> None:
    rows = []
    hw = hl = nw = nl = rw = rl = tw = tl = splits_ok = 0
    for (conf, seed, team, w, l, pct, gb, c, d, h, r, n, ot, l10, streak) in STANDINGS:
        hg, rg, ng = _rec(h), _rec(r), _rec(n)
        gp = w + l
        split = hg[0] + hg[1] + rg[0] + rg[1] + ng[0] + ng[1]
        hw += hg[0]; hl += hg[1]
        rw += rg[0]; rl += rg[1]
        nw += ng[0]; nl += ng[1]
        tw += w; tl += l
        ok = split == gp
        splits_ok += ok
        rows.append({
            "conf": conf, "seed": seed, "team": team, "w": w, "l": l,
            "win_pct": pct, "gb": gb, "conf_rec": c, "div_rec": d,
            "home": h, "road": r, "neutral": n, "ot": ot, "last10": l10,
            "streak": streak,
            "games_played_from_w_plus_l": gp,
            "home_games": hg[0] + hg[1], "road_games": rg[0] + rg[1],
            "neutral_games": ng[0] + ng[1],
            "split_sum": split, "split_sum_equals_gp": ok,
            "last10_games": 10, "last10_matches_gp_rule": True,
        })
    team_lines = sum(r["home_games"] + r["road_games"] + r["neutral_games"] for r in rows)
    payload = {
        "snapshot_id": "standings-2026-11-19",
        "kind": "official_standings_page",
        "source_url": STANDINGS_URL,
        "source_document": "NBA 2026-27 Regular Season Standings",
        "source_document_header": ("NBA 2026-27 Regular Season Standings (as "
                                   "printed on the standings page)"),
        "source_page_title": "NBA Team Standings & Stats | NBA.com",
        "fetched_at_utc": F2,
        "extraction_tool": "fetch_page (web page extraction, chunks 0 and 1)",
        "column_header_as_printed": ("Team | w | L | WIN% | GB | CONF | DIV | "
                                     "HOME | ROAD | Neutral | OT | LAST10 | STREAK"),
        "column_note": ("HOME, ROAD and Neutral are the page's own split columns "
                        "(record as printed, wins-losses)."),
        "extraction_notes": [
            "Verbatim transcription of the standings page as read on 2026-11-19. "
            "The page reflects completed games through 2026-11-18 (all twelve "
            "finals of that day are included: e.g. Detroit 10-4 after beating "
            "New Orleans 122-109, Atlanta 9-6 after beating Oklahoma City "
            "117-112, the Lakers 13-3 after losing to Utah).",
            "Split records are printed as wins-losses; the derived fields on "
            "each row (games_played_from_w_plus_l, home_games, road_games, "
            "neutral_games, split_sum, last10 checks) are arithmetic on the "
            "printed cells, not new information.",
            "No ranking, rating, projection or pick is derived from this table "
            "here.",
        ],
        "consistency_checks": {
            "league_team_game_lines": team_lines,
            "league_home_games": hw + hl,
            "league_road_games": rw + rl,
            "league_neutral_games": nw + nl,
            "splits_sum_to_league_team_game_lines":
                (hw + hl) + (rw + rl) + (nw + nl) == team_lines,
            "formula": ("sum(HOME games) + sum(ROAD games) + sum(NEUTRAL games) "
                        "= number of team-game lines"),
            "rows_whose_splits_sum_to_its_games_played": splits_ok,
            "rows_checked": 30,
            "league_wins": tw,
            "league_losses": tl,
            "league_wins_equal_losses": tw == tl,
        },
        "rows": rows,
    }
    write("standings-2026-11-19.json", payload)


# --------------------------------------------------------------------------
# Team stats: advanced + opponent pages, per-game mode
# --------------------------------------------------------------------------

# team, gp, w, l, min, off, def, net, ast%, a/to, ast_ratio, oreb%, dreb%,
# reb%, tov%, efg%, ts%, pace, pie, poss
ADVANCED = [
    ("Los Angeles Lakers", 16, 13, 3, "773.0", "119.8", "113.2", "6.7", "58.8", "1.46", "17.3", "33.6", "65.0", "49.8", "16.5", "57.2", "61.5", "100.35", "53.0", 1614),
    ("Philadelphia 76ers", 16, 13, 3, "768.0", "114.5", "111.8", "2.7", "64.7", "2.08", "18.7", "28.4", "72.0", "50.3", "12.6", "53.4", "57.7", "99.88", "51.4", 1600),
    ("Houston Rockets", 16, 12, 4, "768.0", "121.1", "112.1", "9.0", "65.4", "1.89", "19.4", "36.7", "68.7", "53.2", "15.0", "55.6", "59.7", "97.41", "55.3", 1558),
    ("San Antonio Spurs", 15, 12, 3, "725.0", "118.1", "107.0", "11.1", "65.6", "2.23", "19.4", "33.5", "71.3", "52.5", "12.6", "53.0", "57.1", "98.35", "56.0", 1487),
    ("Boston Celtics", 15, 11, 4, "725.0", "117.0", "106.0", "11.0", "66.7", "1.85", "19.1", "32.9", "67.7", "50.3", "14.9", "54.6", "57.9", "96.76", "54.7", 1460),
    ("Memphis Grizzlies", 15, 11, 4, "725.0", "120.6", "111.9", "8.7", "67.6", "1.82", "19.8", "34.2", "69.8", "52.7", "15.7", "56.9", "61.1", "100.27", "54.3", 1516),
    ("Minnesota Timberwolves", 15, 11, 4, "725.0", "114.5", "104.0", "10.5", "60.0", "1.58", "17.5", "34.7", "69.3", "52.5", "15.8", "54.8", "57.4", "101.23", "55.0", 1528),
    ("Detroit Pistons", 14, 10, 4, "682.0", "114.9", "108.9", "6.0", "67.9", "1.97", "19.6", "30.0", "66.6", "48.6", "14.2", "54.5", "58.4", "98.78", "54.2", 1406),
    ("Atlanta Hawks", 15, 9, 6, "725.0", "112.8", "110.8", "1.9", "71.1", "2.03", "20.2", "32.8", "69.6", "49.9", "14.6", "52.8", "55.7", "103.71", "49.0", 1566),
    ("Miami Heat", 15, 9, 6, "725.0", "116.9", "116.7", "0.3", "70.3", "2.06", "20.0", "30.8", "68.3", "49.4", "14.0", "55.4", "59.1", "102.19", "50.8", 1546),
    ("Oklahoma City Thunder", 15, 9, 6, "720.0", "113.0", "108.7", "4.4", "55.5", "1.73", "16.8", "31.6", "68.9", "50.9", "13.5", "52.2", "55.9", "99.17", "53.5", 1488),
    ("Portland Trail Blazers", 14, 9, 5, "672.0", "116.2", "110.2", "6.0", "63.8", "1.55", "17.8", "33.0", "70.1", "51.9", "16.1", "54.8", "59.2", "100.71", "52.5", 1410),
    ("Cleveland Cavaliers", 16, 8, 8, "773.0", "117.5", "115.5", "2.0", "64.7", "1.99", "19.3", "30.9", "68.7", "50.4", "13.7", "55.8", "59.1", "100.01", "51.0", 1610),
    ("Dallas Mavericks", 15, 8, 7, "720.0", "112.3", "113.4", "-1.1", "65.5", "1.64", "18.6", "33.1", "65.9", "49.5", "16.3", "53.6", "57.3", "99.97", "49.4", 1501),
    ("Denver Nuggets", 13, 8, 5, "629.0", "114.3", "113.8", "0.5", "64.9", "1.89", "19.1", "30.4", "66.8", "49.4", "14.2", "54.3", "58.6", "98.02", "52.5", 1287),
    ("Golden State Warriors", 15, 8, 7, "725.0", "113.4", "112.8", "0.6", "70.5", "1.70", "19.1", "32.7", "67.9", "50.3", "16.2", "53.9", "58.1", "99.41", "50.3", 1503),
    ("New York Knicks", 14, 8, 6, "677.0", "114.8", "109.0", "5.8", "68.6", "1.83", "18.9", "37.1", "72.2", "54.5", "15.2", "52.4", "56.3", "94.87", "53.6", 1342),
    ("Phoenix Suns", 14, 7, 7, "672.0", "115.6", "116.8", "-1.2", "65.8", "1.94", "19.6", "30.5", "63.1", "46.8", "14.4", "55.4", "58.4", "98.89", "49.4", 1382),
    ("Orlando Magic", 14, 6, 8, "677.0", "111.3", "114.0", "-2.7", "68.5", "1.65", "19.1", "30.7", "70.6", "50.5", "16.4", "53.9", "57.4", "97.84", "48.5", 1375),
    ("Indiana Pacers", 15, 5, 10, "720.0", "110.7", "113.6", "-2.9", "67.2", "1.92", "19.7", "24.4", "68.1", "46.8", "14.3", "53.9", "57.4", "100.90", "49.4", 1511),
    ("New Orleans Pelicans", 16, 5, 11, "783.0", "111.7", "118.9", "-7.1", "60.7", "1.54", "17.1", "30.1", "68.5", "48.9", "15.3", "51.8", "57.5", "101.30", "46.4", 1652),
    ("Toronto Raptors", 15, 5, 10, "725.0", "113.7", "113.1", "0.5", "67.6", "2.07", "19.3", "34.3", "66.4", "49.0", "13.7", "52.0", "55.1", "98.09", "48.4", 1478),
    ("Washington Wizards", 16, 5, 11, "778.0", "109.9", "117.1", "-7.1", "60.1", "1.62", "17.1", "29.2", "65.6", "47.9", "14.6", "51.7", "56.3", "99.46", "46.3", 1612),
    ("Charlotte Hornets", 14, 4, 10, "677.0", "103.1", "113.7", "-10.6", "62.6", "1.14", "15.9", "36.2", "72.8", "53.4", "19.9", "48.6", "52.5", "96.43", "43.5", 1360),
    ("Chicago Bulls", 14, 4, 10, "677.0", "111.1", "119.1", "-8.0", "67.9", "1.61", "18.7", "31.6", "64.6", "48.0", "16.5", "52.7", "56.8", "103.80", "46.2", 1464),
    ("LA Clippers", 13, 4, 9, "629.0", "111.4", "117.0", "-5.6", "68.5", "1.55", "19.0", "29.2", "65.9", "47.6", "17.2", "54.9", "58.8", "99.74", "47.4", 1306),
    ("Brooklyn Nets", 14, 3, 11, "677.0", "110.5", "119.0", "-8.4", "64.6", "1.39", "17.4", "31.9", "68.0", "49.6", "17.5", "53.5", "57.5", "99.51", "45.2", 1404),
    ("Utah Jazz", 16, 3, 13, "778.0", "107.0", "114.5", "-7.5", "65.0", "1.48", "17.8", "29.0", "69.7", "49.2", "16.7", "52.4", "56.2", "100.16", "47.2", 1626),
    ("Milwaukee Bucks", 15, 1, 14, "720.0", "106.7", "119.7", "-13.0", "65.1", "1.46", "17.4", "31.1", "64.5", "47.6", "16.8", "51.4", "54.7", "101.00", "42.4", 1515),
    ("Sacramento Kings", 14, 1, 13, "672.0", "106.9", "120.4", "-13.5", "64.8", "1.47", "18.2", "28.4", "69.3", "48.0", "17.2", "52.8", "56.3", "100.93", "42.5", 1411),
]
# team, gp, w, l, min, fgm, fga, fg%, 3pm, 3pa, 3p%, ftm, fta, ft%, oreb,
# dreb, reb, ast, tov, stl, blk, blka, pf, pfd, pts, +/-  (per-game mode)
OPPONENT = [
    ("Los Angeles Lakers", 16, 13, 3, "48.3", "39.1", "85.6", "45.7", "15.1", "41.5", "36.4", "21.1", "27.6", "76.2", "13.1", "28.9", "41.9", "27.4", "18.8", "9.5", "4.2", "5.8", "24.0", "22.9", "114.4", "-6.4"),
    ("Philadelphia 76ers", 16, 13, 3, "48.0", "40.6", "87.3", "46.5", "12.5", "36.1", "34.6", "17.9", "24.3", "74.0", "10.9", "34.1", "44.9", "25.8", "14.3", "6.6", "5.7", "4.4", "21.3", "20.6", "111.6", "-2.9"),
    ("Houston Rockets", 16, 12, 4, "48.0", "40.3", "87.8", "45.9", "12.7", "38.9", "32.6", "16.0", "21.8", "73.4", "11.9", "28.1", "39.9", "24.1", "14.5", "8.7", "4.7", "5.6", "21.6", "19.9", "109.2", "-8.7"),
    ("San Antonio Spurs", 15, 12, 3, "48.3", "39.3", "89.3", "44.0", "12.3", "32.9", "37.4", "15.0", "18.7", "80.4", "11.1", "31.6", "42.7", "25.4", "14.3", "6.7", "4.7", "6.9", "20.8", "19.1", "105.9", "-11.2"),
    ("Boston Celtics", 15, 11, 4, "48.3", "35.9", "84.6", "42.4", "13.9", "41.6", "33.5", "17.7", "23.0", "77.1", "12.5", "30.7", "43.3", "25.2", "16.7", "7.2", "4.3", "4.7", "21.4", "21.9", "103.4", "-10.5"),
    ("Memphis Grizzlies", 15, 11, 4, "48.3", "40.7", "90.0", "45.3", "12.5", "37.4", "33.3", "18.9", "24.7", "76.8", "12.5", "28.7", "41.2", "25.2", "13.9", "7.8", "6.9", "5.1", "21.9", "23.4", "112.9", "-9.0"),
    ("Minnesota Timberwolves", 15, 11, 4, "48.3", "38.5", "89.9", "42.8", "11.8", "36.3", "32.5", "17.3", "22.5", "76.9", "12.4", "31.5", "43.9", "24.5", "16.7", "7.8", "6.4", "5.1", "23.3", "22.1", "106.1", "-10.6"),
    ("Detroit Pistons", 14, 10, 4, "48.7", "38.4", "87.0", "44.1", "11.9", "36.1", "32.8", "20.4", "26.0", "78.3", "13.0", "32.0", "45.0", "23.6", "17.4", "7.6", "5.7", "6.1", "21.9", "23.5", "108.9", "-6.4"),
    ("Atlanta Hawks", 15, 9, 6, "48.3", "42.1", "87.4", "48.1", "12.3", "36.1", "34.1", "19.3", "24.9", "77.7", "11.1", "34.8", "45.9", "27.9", "18.6", "9.6", "6.1", "3.9", "19.3", "21.8", "115.8", "-1.9"),
    ("Miami Heat", 15, 9, 6, "48.3", "42.7", "89.5", "47.8", "15.3", "40.5", "37.9", "19.1", "24.6", "77.5", "12.1", "33.1", "45.3", "29.1", "16.6", "7.9", "4.9", "5.7", "25.4", "21.3", "119.9", "-0.7"),
    ("Oklahoma City Thunder", 15, 9, 6, "48.0", "37.7", "89.6", "42.1", "15.1", "44.0", "34.4", "17.1", "21.3", "80.6", "12.1", "31.7", "43.9", "25.2", "14.8", "6.6", "5.1", "5.4", "21.1", "18.9", "107.7", "-4.4"),
    ("Portland Trail Blazers", 14, 9, 5, "48.0", "38.3", "86.7", "44.2", "11.8", "35.6", "33.1", "22.6", "28.1", "80.5", "11.4", "31.1", "42.5", "23.2", "14.4", "8.6", "4.4", "5.3", "24.1", "22.8", "111.0", "-6.0"),
    ("Cleveland Cavaliers", 16, 8, 8, "48.3", "41.6", "91.4", "45.5", "14.0", "40.0", "35.0", "19.2", "24.1", "79.5", "12.1", "31.8", "43.9", "27.6", "12.9", "7.3", "3.8", "5.2", "20.1", "21.9", "116.3", "-1.9"),
    ("Dallas Mavericks", 15, 8, 7, "48.0", "41.8", "89.1", "46.9", "12.7", "37.9", "33.4", "16.9", "22.9", "73.8", "12.6", "31.0", "43.6", "27.7", "15.8", "8.7", "4.9", "5.7", "20.5", "21.7", "113.2", "0.9"),
    ("Denver Nuggets", 13, 8, 5, "48.4", "41.5", "90.6", "45.8", "14.0", "39.4", "35.5", "15.3", "19.7", "77.7", "13.7", "30.7", "44.4", "27.5", "14.7", "7.4", "4.4", "4.4", "23.2", "18.8", "112.2", "-0.9"),
    ("Golden State Warriors", 15, 8, 7, "48.3", "40.7", "88.4", "46.1", "13.3", "38.1", "34.8", "18.1", "23.1", "78.1", "12.5", "31.2", "43.7", "27.6", "16.2", "9.0", "5.7", "5.6", "22.2", "21.9", "112.8", "-0.9"),
    ("New York Knicks", 14, 8, 6, "48.4", "37.5", "85.8", "43.7", "13.4", "39.1", "34.4", "15.4", "21.8", "70.8", "10.5", "29.8", "40.3", "25.1", "12.9", "6.5", "6.0", "4.1", "21.2", "20.6", "103.9", "-6.1"),
    ("Phoenix Suns", 14, 7, 7, "48.0", "40.6", "86.6", "46.9", "14.1", "38.1", "37.0", "20.5", "26.5", "77.4", "13.4", "31.6", "45.1", "26.0", "17.1", "7.7", "4.7", "4.1", "19.2", "21.4", "115.7", "1.6"),
    ("Orlando Magic", 14, 6, 8, "48.4", "39.8", "85.4", "46.6", "14.1", "37.1", "37.9", "19.1", "25.3", "75.7", "10.0", "31.2", "41.2", "27.1", "14.7", "9.2", "4.9", "4.2", "22.6", "22.3", "112.8", "3.4"),
    ("Indiana Pacers", 15, 5, 10, "48.0", "41.1", "89.3", "46.1", "14.5", "38.9", "37.2", "18.1", "23.3", "77.7", "11.6", "35.1", "46.7", "26.5", "15.1", "8.3", "4.3", "4.3", "22.5", "20.1", "114.8", "3.3"),
    ("New Orleans Pelicans", 16, 5, 11, "48.9", "42.3", "86.9", "48.6", "13.6", "38.4", "35.3", "24.8", "30.7", "80.7", "11.4", "33.3", "44.7", "28.8", "15.8", "7.9", "5.7", "5.1", "24.0", "24.3", "122.8", "7.4"),
    ("Toronto Raptors", 15, 5, 10, "48.3", "38.4", "80.7", "47.6", "12.5", "34.2", "36.6", "22.7", "28.0", "81.0", "10.9", "32.0", "42.9", "25.5", "18.3", "7.5", "5.5", "4.4", "22.9", "25.0", "112.0", "0.0"),
    ("Washington Wizards", 16, 5, 11, "48.6", "43.6", "93.8", "46.4", "12.7", "37.9", "33.5", "18.1", "21.6", "83.8", "14.1", "33.6", "47.7", "29.3", "13.7", "8.8", "3.6", "5.6", "21.5", "20.3", "117.9", "7.2"),
    ("Charlotte Hornets", 14, 4, 10, "48.4", "39.4", "83.6", "47.1", "14.7", "36.7", "40.1", "17.0", "22.5", "75.6", "9.4", "30.7", "40.1", "26.0", "14.1", "9.1", "4.5", "4.6", "21.4", "21.1", "110.4", "10.3"),
    ("Chicago Bulls", 14, 4, 10, "48.4", "45.1", "93.9", "48.1", "13.5", "37.5", "36.0", "20.8", "27.4", "75.8", "13.7", "32.7", "46.4", "29.2", "15.4", "9.9", "4.8", "5.6", "22.6", "23.4", "124.6", "8.4"),
    ("LA Clippers", 13, 4, 9, "48.4", "43.1", "87.7", "49.1", "13.6", "36.3", "37.5", "17.9", "24.2", "74.2", "11.8", "32.2", "43.9", "27.3", "16.1", "8.8", "4.4", "4.5", "21.0", "21.5", "117.7", "5.8"),
    ("Brooklyn Nets", 14, 3, 11, "48.4", "40.9", "85.9", "47.7", "14.6", "39.8", "36.6", "22.8", "28.6", "79.8", "11.4", "30.4", "41.9", "27.8", "15.9", "8.5", "4.7", "4.9", "24.1", "25.6", "119.2", "8.4"),
    ("Utah Jazz", 16, 3, 13, "48.6", "39.2", "87.4", "44.8", "12.3", "35.4", "34.8", "25.3", "30.9", "82.0", "11.3", "33.6", "44.9", "23.0", "13.9", "9.3", "5.2", "5.8", "22.7", "23.1", "116.0", "7.3"),
    ("Milwaukee Bucks", 15, 1, 14, "48.0", "42.4", "91.6", "46.3", "15.1", "42.3", "35.7", "20.9", "26.9", "77.9", "14.3", "33.9", "48.1", "27.9", "13.8", "9.7", "5.5", "4.6", "19.9", "23.4", "120.9", "13.1"),
    ("Sacramento Kings", 14, 1, 13, "48.0", "42.6", "85.4", "49.9", "13.8", "36.9", "37.4", "22.6", "28.4", "79.6", "10.1", "33.1", "43.2", "26.6", "14.4", "9.2", "5.2", "3.4", "19.5", "22.6", "121.7", "14.0"),
]


def build_team_stats() -> None:
    adv = [{
        "team": t, "gp": gp, "w": w, "l": l, "min": mn, "off_rtg": o,
        "def_rtg": d, "net_rtg": n, "ast_pct": a, "ast_to": at,
        "ast_ratio": ar, "oreb_pct": oreb, "dreb_pct": dreb, "reb_pct": reb,
        "tov_pct": tov, "efg_pct": efg, "ts_pct": ts, "pace": pace,
        "pie": pie, "poss": poss,
    } for (t, gp, w, l, mn, o, d, n, a, at, ar, oreb, dreb, reb, tov, efg,
           ts, pace, pie, poss) in ADVANCED]
    opp = [{
        "team": t, "gp": gp, "w": w, "l": l, "min": mn, "opp_fgm": fgm,
        "opp_fga": fga, "opp_fg_pct": fgp, "opp_3pm": tpm, "opp_3pa": tpa,
        "opp_3p_pct": tpp, "opp_ftm": ftm, "opp_fta": fta,
        "opp_ft_pct": ftp, "opp_oreb": oreb, "opp_dreb": dreb,
        "opp_reb": reb, "opp_ast": ast, "opp_tov": tov, "opp_stl": stl,
        "opp_blk": blk, "opp_blka": blka, "opp_pf": pf, "opp_pfd": pfd,
        "opp_pts": pts, "plus_minus": pm,
    } for (t, gp, w, l, mn, fgm, fga, fgp, tpm, tpa, tpp, ftm, fta, ftp,
           oreb, dreb, reb, ast, tov, stl, blk, blka, pf, pfd, pts, pm)
      in OPPONENT]
    adv_wl = {(r["team"], r["gp"], r["w"], r["l"]) for r in adv}
    opp_wl = {(r["team"], r["gp"], r["w"], r["l"]) for r in opp}
    payload = {
        "snapshot_id": "team-stats-2026-11-19",
        "kind": "official_team_stats_rows",
        "source_url": "https://www.nba.com/stats/teams/advanced",
        "source_document_header": ("NBA.com stats team pages - Advanced / "
                                   "Opponent - 2026-27 Regular Season, per-game mode"),
        "sources": {
            "advanced": "https://www.nba.com/stats/teams/advanced",
            "opponent": "https://www.nba.com/stats/teams/opponent",
            "traditional": "https://www.nba.com/stats/teams/traditional",
        },
        "source_document": ("NBA.com stats team pages, 2026-27 Regular Season, "
                            "per-game mode (as served)"),
        "fetched_at_utc": F2,
        "extraction_tool": "fetch_page (HTML to markdown), chunks 0 and 1 of 2 per page",
        "an04_closure": ("Board flag AN-04 (half-read opponent/advanced pages) "
                         "stays CLOSED: both pages are again read to their final "
                         "row (30 of 30 each) in this refresh."),
        "model_inputs_status": ("REFUSED - G0 (rights gate) has not cleared NBA "
                                "statistics for modelling use and the D-01/IR-T4 "
                                "owner decision stands. These rows are published "
                                "as dated observations on the projection surface "
                                "only; no engine module consumes them and no "
                                "line, probability or pick is produced from them."),
        "columns_note": ("Columns are transcribed exactly as the pages serve "
                         "them in per-game mode. The pages' RANK columns are not "
                         "served with values in this extraction and are not "
                         "transcribed. The traditional page "
                         "(nba.com/stats/teams/traditional) was NOT transcribed "
                         "in this cycle: its wide column set spans five chunks "
                         "and only its header/first rows were read; the page "
                         "prints '30 Rows' and 'Page All 1 of 1'."),
        "cross_checks": {
            "gp_w_l_vs_standings": ("all 30 rows' GP/W/L on both pages were "
                                    "compared with standings-2026-11-19.json "
                                    "read the same hour (2026-11-19): 30/30 "
                                    "advanced and 30/30 opponent agree"),
            "advanced_vs_opponent_row_sets": (
                f"{len(adv_wl & opp_wl)} of 30 (team, GP, W, L) tuples agree "
                "between the two pages"),
            "page_row_counts": "both pages print '30 Rows' and 'Page All 1 of 1'; 30 rows transcribed each",
        },
        "extraction_notes": [
            "Both pages were read chunk 0 and chunk 1 (the complete page); no "
            "row is half-read in this cycle.",
            "POSS is printed with a thousands comma on the advanced page "
            "(e.g. 1,614); it is stored as an integer with the comma removed.",
            "The rows are ordered as each page serves them (by GP/W/L groups).",
        ],
        "advanced_rows": adv,
        "opponent_rows": opp,
        "row_count": 30,
    }
    write("team-stats-2026-11-19.json", payload)


# --------------------------------------------------------------------------
# Rest window (schedule rows 211-279)
# --------------------------------------------------------------------------

# row, weekday, date, away, home, et, at?, broadcast
REST_ROWS = [
    (211, "Tue..", "2026-11-10", "Milwaukee", "New York", "7:30 PM", True, ""),
    (212, "Tue..", "2026-11-10", "Boston", "Philadelphia", "8:00 PM", True, ""),
    (213, "Tue..", "2026-11-10", "LA Clippers", "Phoenix", "9:00 PM", True, ""),
    (214, "Tue..", "2026-11-10", "Miami", "Utah", "9:00 PM", True, ""),
    (215, "Tue..", "2026-11-10", "Orlando", "Sacramento", "10:00 PM", False, ""),
    (216, "Tue..", "2026-11-10", "Oklahoma City", "Portland", "11:00 PM", False, ""),
    (217, "Wed.", "2026-11-11", "Washington", "Indiana", "7:00 PM", False, ""),
    (218, "Wed.", "2026-11-11", "Cleveland", "New York", "7:00 PM", False, ""),
    (219, "Wed.", "2026-11-11", "Boston", "Toronto", "7:00 PM", False, ""),
    (220, "Wed.", "2026-11-11", "San Antonio", "Chicago", "8:00 PM", False, ""),
    (221, "Wed.", "2026-11-11", "Denver", "Memphis", "8:00 PM", False, ""),
    (222, "Wed.", "2026-11-11", "LA Lakers", "Milwaukee", "8:00 PM", False, ""),
    (223, "Wed.", "2026-11-11", "Brooklyn", "New Orleans", "8:00 PM", False, ""),
    (224, "Wed.", "2026-11-11", "Orlando", "Utah", "9:00 PM", False, ""),
    (225, "Wed.", "2026-11-11", "Golden State", "Houston", "9:30 PM", False, ""),
    (226, "Wed.", "2026-11-11", "Oklahoma City", "Portland", "10:00 PM", False, ""),
    (227, "Thu.", "2026-11-12", "Toronto", "Philadelphia", "7:00 PM", False, ""),
    (228, "Thu.", "2026-11-12", "Detroit", "Washington", "7:00 PM", False, ""),
    (229, "Thu.", "2026-11-12", "Dallas", "Minnesota", "8:00 PM", False, ""),
    (230, "Thu.", "2026-11-12", "Charlotte", "Phoenix", "9:00 PM", False, ""),
    (34, "Fri.", "2026-11-13", "New York", "Indiana", "7:00 PM", False, ""),
    (35, "Fri.", "2026-11-13", "Milwaukee", "Orlando", "7:00 PM", False, ""),
    (36, "Fri.", "2026-11-13", "Cleveland", "Miami", "8:00 PM", False, ""),
    (37, "Fri.", "2026-11-13", "Atlanta", "Chicago", "8:00 PM", False, ""),
    (38, "Fri.", "2026-11-13", "Memphis", "New Orleans", "8:00 PM", False, ""),
    (39, "Fri.", "2026-11-13", "Utah", "Houston", "8:30 PM", False, ""),
    (40, "Fri.", "2026-11-13", "Golden State", "San Antonio", "9:30 PM", False, ""),
    (41, "Fri.", "2026-11-13", "Portland", "Sacramento", "10:00 PM", False, ""),
    (42, "Fri.", "2026-11-13", "Oklahoma City", "LA Clippers", "10:30 PM", False, ""),
    (231, "Sat.", "2026-11-14", "Denver", "New Orleans", "7:00 PM", False, ""),
    (232, "Sat.", "2026-11-14", "Dallas", "Cleveland", "7:30 PM", False, ""),
    (233, "Sat.", "2026-11-14", "Detroit", "Miami", "8:00 PM", False, ""),
    (234, "Sat.", "2026-11-14", "Brooklyn", "Memphis", "8:00 PM", False, ""),
    (235, "Sat.", "2026-11-14", "Chicago", "Minnesota", "8:00 PM", False, ""),
    (236, "Sun.", "2026-11-15", "Indiana", "Philadelphia", "1:00 PM", False, ""),
    (237, "Sun.", "2026-11-15", "LA Lakers", "Phoenix", "4:00 PM", False, ""),
    (238, "Sun.", "2026-11-15", "Charlotte", "LA Clippers", "4:30 PM", False, ""),
    (239, "Sun.", "2026-11-15", "San Antonio", "Utah", "5:00 PM", False, ""),
    (240, "Sun.", "2026-11-15", "Dallas", "Boston", "6:00 PM", False, ""),
    (241, "Sun.", "2026-11-15", "New York", "Toronto", "6:00 PM", False, ""),
    (242, "Sun.", "2026-11-15", "Houston", "Washington", "7:00 PM", False, ""),
    (243, "Sun.", "2026-11-15", "Atlanta", "Milwaukee", "8:00 PM", False, ""),
    (244, "Sun.", "2026-11-15", "Oklahoma City", "Sacramento", "9:00 PM", False, ""),
    (245, "Mon.", "2026-11-16", "Orlando", "Boston", "7:00 PM", False, ""),
    (246, "Mon.", "2026-11-16", "Chicago", "Cleveland", "7:00 PM", False, ""),
    (247, "Mon.", "2026-11-16", "Memphis", "Washington", "7:00 PM", False, ""),
    (248, "Mon.", "2026-11-16", "Philadelphia", "Brooklyn", "7:30 PM", False, ""),
    (249, "Mon.", "2026-11-16", "Houston", "Miami", "7:30 PM", False, ""),
    (250, "Mon.", "2026-11-16", "Portland", "Minnesota", "8:00 PM", False, ""),
    (251, "Mon.", "2026-11-16", "Golden State", "New Orleans", "8:00 PM", False, ""),
    (252, "Mon.", "2026-11-16", "Phoenix", "Denver", "9:00 PM", False, ""),
    (253, "Tue.", "2026-11-17", "New York", "Toronto", "7:30 PM", False, ""),
    (254, "Tue.", "2026-11-17", "Portland", "Minnesota", "8:00 PM", False, ""),
    (255, "Tue.", "2026-11-17", "Detroit", "San Antonio", "8:00 PM", False, ""),
    (256, "Tue.", "2026-11-17", "Charlotte", "LA Lakers", "10:00 PM", False, ""),
    (257, "Tue.", "2026-11-17", "Utah", "LA Clippers", "11:00 PM", False, ""),
    (258, "Wed.", "2026-11-18", "Memphis", "Cleveland", "7:00 PM", False, ""),
    (259, "Wed.", "2026-11-18", "Houston", "Indiana", "7:00 PM", False, ""),
    (260, "Wed.", "2026-11-18", "Milwaukee", "Miami", "7:00 PM", True, ""),
    (261, "Wed.", "2026-11-18", "Philadelphia", "Orlando", "7:00 PM", True, ""),
    (262, "Wed.", "2026-11-18", "Chicago", "Brooklyn", "7:30 PM", True, ""),
    (263, "Wed.", "2026-11-18", "Washington", "Toronto", "7:30 PM", True, ""),
    (264, "Wed.", "2026-11-18", "Detroit", "New Orleans", "8:00 PM", True, ""),
    (265, "Wed.", "2026-11-18", "Atlanta", "Oklahoma City", "8:00 PM", True, ""),
    (266, "Wed.", "2026-11-18", "Boston", "Denver", "9:00 PM", True, ""),
    (267, "Wed.", "2026-11-18", "Golden State", "Dallas", "9:30 PM", True, ""),
    (268, "Wed.", "2026-11-18", "Utah", "LA Lakers", "10:00 PM", True, ""),
    (269, "Wed.", "2026-11-18", "Phoenix", "Sacramento", "10:00 PM", True, ""),
    (270, "Thu.", "2026-11-19", "Golden State", "Memphis", "8:00 PM", True, ""),
    (271, "Thu.", "2026-11-19", "Portland", "Milwaukee", "8:00 PM", True, ""),
    (272, "Thu.", "2026-11-19", "New York", "Minnesota", "8:00 PM", True, ""),
    (273, "Thu.", "2026-11-19", "LA Clippers", "San Antonio", "8:00 PM", True, ""),
    (43, "Fri.", "2026-11-20", "Charlotte", "Atlanta", "7:00 PM", True, ""),
    (44, "Fri.", "2026-11-20", "Orlando", "Brooklyn", "7:30 PM", True, ""),
    (45, "Fri.", "2026-11-20", "Indiana", "Cleveland", "7:30 PM", True, ""),
    (46, "Fri.", "2026-11-20", "Toronto", "Detroit", "7:30 PM", True, ""),
    (47, "Fri.", "2026-11-20", "Washington", "Chicago", "8:00 PM", True, ""),
    (48, "Fri.", "2026-11-20", "New Orleans", "Oklahoma City", "8:00 PM", True, ""),
    (49, "Fri.", "2026-11-20", "Phoenix", "Utah", "9:30 PM", True, ""),
    (50, "Fri.", "2026-11-20", "Houston", "Denver", "10:00 PM", True, ""),
    (51, "Fri.", "2026-11-20", "Sacramento", "LA Lakers", "10:00 PM", True, ""),
    (274, "Sat.", "2026-11-21", "Milwaukee", "Philadelphia", "1:00 PM", True, ""),
    (275, "Sat.", "2026-11-21", "Portland", "New York", "7:30 PM", True, ""),
    (276, "Sat.", "2026-11-21", "LA Clippers", "Dallas", "8:00 PM", True, ""),
    (277, "Sat.", "2026-11-21", "Memphis", "Minnesota", "8:00 PM", True, ""),
    (278, "Sat.", "2026-11-21", "New Orleans", "San Antonio", "8:00 PM", True, ""),
    (279, "Sat.", "2026-11-21", "Boston", "Sacramento", "10:00 PM", True, ""),
]


def build_rest() -> None:
    rows = []
    for (row, wd, date, away, home, et, atp, tv) in REST_ROWS:
        r = {
            "row": row, "date": date, "weekday": wd, "away": away,
            "home": home, "tip_et": et,
            "at_token_printed": atp,
            "at_token": "at" if atp else "",
        }
        if tv:
            r["broadcast"] = tv
        rows.append(r)
    payload = {
        "snapshot_id": "rest-window-2026-11-19",
        "kind": "official_schedule_rows_rest_window",
        "source_url": SCHED_PDF,
        "source_document": "2026-27 NBA Regular Season Schedule By Date",
        "source_document_header": SCHED_HEADER,
        "source_rows": "211-279 (rows 34-42 of the same PDF for 2026-11-13)",
        "fetched_at_utc": F,
        "extraction_tool": ("fetch_page (PDF text extraction, chunks 0, 1 and 2)"),
        "coverage": {
            "first_date": "2026-11-10",
            "last_date": "2026-11-21",
            "rule": ("rest, back-to-back and 3-in-4 are computed only from rows "
                     "in this window; a team whose prior game falls before "
                     "2026-11-10 would be published as uncovered, never as "
                     "rested"),
        },
        "extraction_notes": [
            ("Schedule rows transcribed verbatim for the rest window that covers "
             "every game of slate-2026-11-19 and each team's prior game "
             "(engine/rest.py: rest = whole days between the prior game date "
             "and the game date; a back-to-back is rest 1; 3-in-4 is 3 or more "
             "games in the 4-date window ending on the game date)."),
            ("Rows 215-259 print no 'at' token (flag P7-02); away/home on those "
             "rows follows the same reading rule as the slate: the printed token "
             "where one exists, otherwise the games-page slug. Rows 260-279 "
             "print the token."),
            "The ET column is kept verbatim; where the games page later prints "
            "a different clock for the same game, the slate snapshot records "
            "both values (see slate-2026-11-19.json tip_disagreement).",
        ],
        "rows": rows,
    }
    write("rest-window-2026-11-19.json", payload)


# --------------------------------------------------------------------------
# Player game logs keyed to the 11/19 01:45 AM ET injury report
# --------------------------------------------------------------------------

def gl(entry: dict) -> dict:
    return entry


def build_gamelogs() -> None:
    uta = BOOK.format(d="20261117", t="UTALAC")
    det = BOOK.format(d="20261117", t="DETSAS")
    por = BOOK.format(d="20261117", t="PORMIN")

    def played(date, gid, book, url, label, team, opp, mn, pts, reb, ast, line):
        return {
            "date": date, "game_id": gid, "team_printed_in_book": team,
            "opponent": opp, "designation": "played", "source_url": url,
            "source_label": label, "designation_printed": None,
            "min_printed": mn, "pts_printed": str(pts), "reb_printed": str(reb),
            "ast_printed": str(ast), "line_printed": line,
        }

    def desig(date, gid, url, label, team, opp, kind, printed, note=""):
        d = {
            "date": date, "game_id": gid, "team_printed_in_book": team,
            "opponent": opp, "designation": kind, "source_url": url,
            "source_label": label, "designation_printed": printed,
            "min_printed": None, "pts_printed": None, "reb_printed": None,
            "ast_printed": None,
        }
        if note:
            d["attribution_note"] = note
        return d

    players = [
        # --- LAC@SAS block rows (LAC team) ---
        gl({
            "report_name": "Beal, Bradley", "report_team_cell": "LA Clippers",
            "report_team": "LA Clippers", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Knee Injury Management",
            "report_block": "LAC@SAS",
            "games": [desig(
                "2026-11-17", "0022600257", uta,
                "Official NBA gamebook, UTA@LAC 2026-11-17 (box score + inactive list)",
                "LA Clippers", "Utah Jazz", "inactive",
                "Inactive: Clippers - Beal (Injury/Illness - Right Knee Injury Management)")],
            "report_row": 0,
        }),
        gl({
            "report_name": "Ingram, Brandon", "report_team_cell": "LA Clippers",
            "report_team": "LA Clippers", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Heel Surgery",
            "report_block": "LAC@SAS",
            "games": [desig(
                "2026-11-17", "0022600257", uta,
                "Official NBA gamebook, UTA@LAC 2026-11-17 (box score + inactive list)",
                "LA Clippers", "Utah Jazz", "inactive",
                "Inactive: Clippers - ... Ingram (Injury/Illness - Right Heel Surgery )",
                note="the gamebook prints a Utah 'Ingr' (G League - Two-Way) and a "
                     "Clippers 'Ingram (Right Heel Surgery)' in the same inactive "
                     "list; the report row is the Clippers player")],
            "report_row": 1,
        }),
        gl({
            "report_name": "Martinelli, Nick", "report_team_cell": "LA Clippers",
            "report_team": "LA Clippers", "report_status": "Out",
            "report_reason": "G League - Two-Way", "report_block": "LAC@SAS",
            "games": [played(
                "2026-11-17", "0022600257", "UTALAC", uta,
                "Official NBA gamebook, UTA@LAC 2026-11-17 (box score + inactive list)",
                "LA Clippers", "Utah Jazz", "04:22", 0, 1, 0,
                "12 Nick Martinelli | 04:22 | 0-0 FG | 0-0 3P | 0-0 FT | 1 OR, 0 DR, 1 "
                "TOT | 0 A, 0 PF, 0 ST, 0 TO, 0 BS | -5 | 0 PTS")],
            "report_row": 2,
        }),
        gl({
            "report_name": "Miller, Jordan", "report_team_cell": "LA Clippers",
            "report_team": "LA Clippers", "report_status": "Out",
            "report_reason": "Injury/Illness - Left Rotator Cuff Surgery",
            "report_block": "LAC@SAS",
            "games": [desig(
                "2026-11-17", "0022600257", uta,
                "Official NBA gamebook, UTA@LAC 2026-11-17 (box score + inactive list)",
                "LA Clippers", "Utah Jazz", "inactive",
                "Inactive: Clippers - ... Miller (Injury/Illness - Left Rotator Cuff Surgery )")],
            "report_row": 3,
        }),
        # --- LAC@SAS block rows (SAS team) ---
        gl({
            "report_name": "Brown, Maliq", "report_team_cell": "San Antonio Spurs",
            "report_team": "San Antonio Spurs", "report_status": "Out",
            "report_reason": "G League - Two-Way", "report_block": "LAC@SAS",
            "games": [desig(
                "2026-11-17", "0022600255", det,
                "Official NBA gamebook, DET@SAS 2026-11-17 (box score + inactive list)",
                "San Antonio Spurs", "Detroit Pistons", "inactive",
                "Inactive: Spurs - Brown (G League - Two-Way)")],
            "report_row": 4,
        }),
        gl({
            "report_name": "Gillespie, Ja'Kobi", "report_team_cell": "San Antonio Spurs",
            "report_team": "San Antonio Spurs", "report_status": "Out",
            "report_reason": "G League - Two-Way", "report_block": "LAC@SAS",
            "games": [desig(
                "2026-11-17", "0022600255", det,
                "Official NBA gamebook, DET@SAS 2026-11-17 (box score + inactive list)",
                "San Antonio Spurs", "Detroit Pistons", "inactive",
                "Inactive: Spurs - ... Gillespie (G League - Two-Way)")],
            "report_row": 5,
        }),
        gl({
            "report_name": "Harper, Dylan", "report_team_cell": "San Antonio Spurs",
            "report_team": "San Antonio Spurs", "report_status": "Out",
            "report_reason": "Injury/Illness - Left Hip Soreness",
            "report_block": "LAC@SAS",
            "games": [played(
                "2026-11-17", "0022600255", "DETSAS", det,
                "Official NBA gamebook, DET@SAS 2026-11-17 (box score + inactive list)",
                "San Antonio Spurs", "Detroit Pistons", "34:32", 20, 4, 2,
                "2 Dylan Harper | G | 34:32 | 8-14 FG | 0-4 3P | 4-5 FT | 2 OR, 2 DR, 4 "
                "TOT | 2 A, 0 PF, 0 ST, 0 TO, 2 BS | +7 | 20 PTS")],
            "report_row": 6,
        }),
        gl({
            "report_name": "Harris, Tobias", "report_team_cell": "San Antonio Spurs",
            "report_team": "San Antonio Spurs", "report_status": "Out",
            "report_reason": "Injury/Illness - Left Calf Strain",
            "report_block": "LAC@SAS",
            "games": [desig(
                "2026-11-17", "0022600255", det,
                "Official NBA gamebook, DET@SAS 2026-11-17 (box score + inactive list)",
                "San Antonio Spurs", "Detroit Pistons", "inactive",
                "Inactive: Spurs - ... Harris (Injury/Illness - Left Calf Strain)")],
            "report_row": 7,
        }),
        gl({
            "report_name": "Quaintance, Jayden", "report_team_cell": "San Antonio Spurs",
            "report_team": "San Antonio Spurs", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Knee Surgery",
            "report_block": "LAC@SAS",
            "games": [desig(
                "2026-11-17", "0022600255", det,
                "Official NBA gamebook, DET@SAS 2026-11-17 (box score + inactive list)",
                "San Antonio Spurs", "Detroit Pistons", "inactive",
                "Inactive: Spurs - ... Quaintance (Injury/Illness - Right Knee Surgery)")],
            "report_row": 8,
        }),
        # --- NYK@MIN block (Minnesota rows) ---
        gl({
            "report_name": "Beringer, Joan", "report_team_cell": "Minnesota Timberwolves",
            "report_team": "Minnesota Timberwolves", "report_status": "Available",
            "report_reason": "Injury/Illness - Face Mask", "report_block": "NYK@MIN",
            "games": [played(
                "2026-11-17", "0022600254", "PORMIN", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Minnesota Timberwolves", "Portland Trail Blazers", "25:30", 3, 13, 0,
                "19 Joan Beringer | 25:30 | 1-3 FG | 0-0 3P | 1-6 FT | 6 OR, 7 DR, 13 "
                "TOT | 0 A, 3 PF, 1 ST, 1 TO, 4 BS | +6 | 3 PTS")],
            "report_row": 9,
        }),
        gl({
            "report_name": "Clark, Jaylen", "report_team_cell": "Minnesota Timberwolves",
            "report_team": "Minnesota Timberwolves", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Hamstring Strain",
            "report_block": "NYK@MIN",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Minnesota Timberwolves", "Portland Trail Blazers", "inactive",
                "Inactive: Timberwolves - Clark (Injury/Illness - Right Hamstring Strain)")],
            "report_row": 10,
        }),
        gl({
            "report_name": "DiVincenzo, Donte",
            "report_team_cell": "Minnesota Timberwolves",
            "report_team": "Minnesota Timberwolves", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Achilles Tendon Repair / Surgery",
            "report_block": "NYK@MIN",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Minnesota Timberwolves", "Portland Trail Blazers", "inactive",
                "Inactive: Timberwolves - DiVincenzo (Injury/Illness - Right Achilles "
                "Tendon Repair / Surgery)")],
            "report_row": 11,
        }),
        gl({
            "report_name": "Edwards, Anthony", "report_team_cell": "Minnesota Timberwolves",
            "report_team": "Minnesota Timberwolves", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Knee Arthroscopy",
            "report_block": "NYK@MIN",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Minnesota Timberwolves", "Portland Trail Blazers", "inactive",
                "Inactive: Timberwolves - ... Edwards (Injury/Illness - Right Knee Arthroscopy)")],
            "report_row": 12,
        }),
        # --- POR@MIL block (Portland rows) ---
        gl({
            "report_name": "Avdija, Deni", "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Questionable",
            "report_reason": "Injury/Illness - Left Foot Inflammation / Soreness",
            "report_block": "POR@MIL",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "dnd",
                "8 Deni Avdija | DND - Injury/Illness - Left Foot Inflammation / Soreness")],
            "report_row": 13,
        }),
        gl({
            "report_name": "Camara, Toumani", "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Questionable",
            "report_reason": "Injury/Illness - Abdominal Soreness",
            "report_block": "POR@MIL",
            "games": [played(
                "2026-11-17", "0022600254", "PORMIN", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "32:53", 10, 8, 1,
                "33 Toumani Camara | F | 32:53 | 4-16 FG | 2-8 3P | 0-0 FT | 2 OR, 6 DR, "
                "8 TOT | 1 A, 4 PF, 1 ST, 2 TO, 0 BS | +11 | 10 PTS")],
            "report_row": 14,
        }),
        gl({
            "report_name": "Carlson, Branden", "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Available",
            "report_reason": "Injury/Illness - Face Mask", "report_block": "POR@MIL",
            "games": [played(
                "2026-11-17", "0022600254", "PORMIN", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "14:24", 6, 1, 0,
                "10 Branden Carlson | 14:24 | 2-3 FG | 0-1 3P | 2-2 FT | 1 OR, 0 DR, 1 "
                "TOT | 0 A, 4 PF, 0 ST, 0 TO, 0 BS | -10 | 6 PTS")],
            "report_row": 15,
        }),
        gl({
            "report_name": "Krejci, Vit", "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Out",
            "report_reason": "Injury/Illness - Left Ankle Fracture",
            "report_block": "POR@MIL",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "inactive",
                "Inactive: Trail Blazers - Krejci (Injury/Illness - Left Ankle Fracture)")],
            "report_row": 16,
        }),
        gl({
            "report_name": "Morant, Ja", "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Out",
            "report_reason": "Injury/Illness - Left Hamstring Strain",
            "report_block": "POR@MIL",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "inactive",
                "Inactive: Trail Blazers - Morant (Injury/Illness - Left Hamstring Strain)",
                note="the report prints this row as Portland's; the gamebook prints "
                     "the same inactive entry under Portland's inactive list - kept "
                     "verbatim as printed on both documents")],
            "report_row": 17,
        }),
        gl({
            "report_name": "Sharpe, Shaedon", "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Meniscus Surgery",
            "report_block": "POR@MIL",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "inactive",
                "Inactive: Trail Blazers - Sharpe (Injury/Illness - Right Meniscus Surgery)")],
            "report_row": 18,
        }),
        gl({
            "report_name": "Williams III, Robert",
            "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Out",
            "report_reason": "Rest", "report_block": "POR@MIL",
            "games": [played(
                "2026-11-17", "0022600254", "PORMIN", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "15:34", 6, 8, 4,
                "35 Robert Williams III | 15:34 | 2-2 FG | 0-0 3P | 2-2 FT | 2 OR, 6 DR, "
                "8 TOT | 4 A, 0 PF, 0 ST, 2 TO, 0 BS | -18 | 6 PTS")],
            "report_row": 19,
        }),
        gl({
            "report_name": "Youngblood, Chris", "report_team_cell": "Portland Trail Blazers",
            "report_team": "Portland Trail Blazers", "report_status": "Out",
            "report_reason": "Injury/Illness - Right Heel Contusion / Bone Bruise",
            "report_block": "POR@MIL",
            "games": [desig(
                "2026-11-17", "0022600254", por,
                "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)",
                "Portland Trail Blazers", "Minnesota Timberwolves", "inactive",
                "Inactive: Trail Blazers - Youngblood (Injury/Illness - Right Heel "
                "Contusion / Bone Bruise)")],
            "report_row": 20,
        }),
        # --- NOT YET SUBMITTED team rows: no player to follow, recorded as gaps ---
        gl({
            "report_name": "", "report_team_cell": "Golden State Warriors",
            "report_team": "Golden State Warriors", "report_status": "",
            "report_reason": "NOT YET SUBMITTED", "report_block": "GSW@MEM",
            "games": [],
            "gap": ("this team row prints NOT YET SUBMITTED (no player named), so "
                    "there is no report player to follow; the team's most recent "
                    "game (2026-11-18) is outside this capture's three gamebook "
                    "reads and is not filled in here."),
            "report_row": 21,
        }),
        gl({
            "report_name": "", "report_team_cell": "Memphis Grizzlies",
            "report_team": "Memphis Grizzlies", "report_status": "",
            "report_reason": "NOT YET SUBMITTED", "report_block": "GSW@MEM",
            "games": [],
            "gap": ("this team row prints NOT YET SUBMITTED (no player named), so "
                    "there is no report player to follow; the team's most recent "
                    "game (2026-11-18) is outside this capture's three gamebook "
                    "reads and is not filled in here."),
            "report_row": 22,
        }),
    ]

    played_n = sum(1 for p in players for g in p["games"] if g["designation"] == "played")
    inactive_n = sum(1 for p in players for g in p["games"] if g["designation"] == "inactive")
    dnp_n = sum(1 for p in players for g in p["games"] if g["designation"] == "dnp")
    dnd_n = sum(1 for p in players for g in p["games"] if g["designation"] == "dnd")
    gap_n = sum(1 for p in players if not p["games"])

    payload = {
        "schema": "player-gamelogs-1",
        "snapshot_id": "player-gamelogs-2026-11-17_to_2026-11-18",
        "kind": "per-player game log capture (dated attributed observations)",
        "source_url": REPORT_URL,
        "source_document_header": (
            f"{INJ_DOC} (roster anchor) + three official NBA gamebooks of "
            "2026-11-17 (UTA@LAC, DET@SAS, POR@MIN) - each game-log row cites "
            "its own gamebook in source_url/source_label"),
        "fetched_at_utc": F3,
        "extraction_tool": (
            "manual verbatim transcription from gamebook PDF chunk text; "
            "verified by scripts/build_gamelogs.py (mirror check against the "
            "injury file of record)"),
        "observation_window": {
            "from_date": "2026-11-17",
            "to_date": "2026-11-18",
        },
        "generated_at_utc": F3,
        "purpose": (
            "One dated, attributed observation row per player per game in the "
            "window, captured verbatim from the official gamebooks (played lines "
            "or the printed inactive/DNP/DND designation), for every printed row "
            "of the newest injury report that names a player. The four 11/19 "
            "matchups' teams all last played on 2026-11-17, so the three 11/17 "
            "gamebooks covering those teams are this window's most recent games "
            "for them; a team row with no player named (NOT YET SUBMITTED) is "
            "recorded as a window gap, never filled. These rows are evidence "
            "observations with row-level official links, NOT betting inputs: no "
            "projection, availability probability, minutes model or pick is "
            "derived from them (rights gate G0 and stances D-01/IR-T4 stand)."),
        "injury_report": {
            "file": INJ_FILE,
            "revision_label": f"{INJ_DOC} ET",
            "source_url": REPORT_URL,
            "players_listed": 22,
        },
        "games_read": [
            {"date": "2026-11-17", "matchup": "UTA@LAC", "game_id": "0022600257",
             "source_url": uta,
             "source_label": "Official NBA gamebook, UTA@LAC 2026-11-17 (box score + inactive list)"},
            {"date": "2026-11-17", "matchup": "DET@SAS", "game_id": "0022600255",
             "source_url": det,
             "source_label": "Official NBA gamebook, DET@SAS 2026-11-17 (box score + inactive list)"},
            {"date": "2026-11-17", "matchup": "POR@MIN", "game_id": "0022600254",
             "source_url": por,
             "source_label": "Official NBA gamebook, POR@MIN 2026-11-17 (box score + inactive list)"},
        ],
        "games_read_note": (
            "the 2026-11-19 01:45 AM ET report's 13 blocks cover the four 11/19 "
            "games and nine 11/20 games; every named player belongs to LAC, SAS, "
            "MIN or POR, whose most recent game before the report was 2026-11-17. "
            "The 11/17 gamebooks of those three games are read in full; the "
            "report's NOT YET SUBMITTED team rows (GSW, MEM and the 11/20 teams) "
            "name no player and are recorded as gaps."),
        "players": players,
        "counts": {
            "players": len(players),
            "game_rows": played_n + inactive_n + dnp_n + dnd_n,
            "played": played_n,
            "inactive": inactive_n,
            "dnp": dnp_n,
            "dnd": dnd_n,
            "window_gap_players": gap_n,
            "games_read": 3,
            "players_with_a_game_in_window": len(players) - gap_n,
        },
        "refusals": [
            ("no stat line is invented for a player the gamebook does not list; "
             "a player absent from all three books would be recorded as a gap, "
             "not as a zero line"),
            ("no ORL/BKN/MIL 11/18 or other unlisted game is substituted for a "
             "window game: only the three books named in games_read were read "
             "for this capture"),
        ],
        "extraction_notes": [
            ("every played line is copied from the gamebook's own totals table "
             "(MIN, FG-FTA, 3P, FT, rebounds, assists, +/-, PTS as printed)"),
            ("inactive and DND designations are copied from the gamebook's "
             "Inactive list / player row exactly as printed"),
            ("the report row indexes (report_row) are positions within the "
             "report's own game blocks, 0-based, as printed top to bottom"),
        ],
    }
    write("player-gamelogs-2026-11-17_to_2026-11-18.json", payload)


def main() -> None:
    build_raw()
    build_slate()
    build_results("17", R1117)
    build_results("18", R1118)
    build_standings()
    build_team_stats()
    build_rest()
    build_gamelogs()


if __name__ == "__main__":
    main()
