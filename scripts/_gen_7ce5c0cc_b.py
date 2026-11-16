#!/usr/bin/env python3
"""One-shot snapshot writer #2 for the 2026-11-16 refresh (session arena/7ce5c0cc-nba4).
Slate window 11/16-11/18, standings 11/16, results 11/15 finals, team stats 11/16.
All values transcribed verbatim from fetch_page extractions logged in
docs/verification-pass-7ce5c0cc.md. No fetching, no inference."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"

SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
GAMES_URL = "https://www.nba.com/games"
REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf"

ABBR = {"Denver":"DEN","New Orleans":"NOP","Dallas":"DAL","Cleveland":"CLE","Detroit":"DET",
        "Miami":"MIA","Brooklyn":"BKN","Memphis":"MEM","Chicago":"CHI","Minnesota":"MIN",
        "Indiana":"IND","Philadelphia":"PHI","LA Lakers":"LAL","Phoenix":"PHX","Charlotte":"CHA",
        "LA Clippers":"LAC","San Antonio":"SAS","Utah":"UTA","Boston":"BOS","New York":"NYK",
        "Toronto":"TOR","Houston":"HOU","Washington":"WAS","Atlanta":"ATL","Milwaukee":"MIL",
        "Oklahoma City":"OKC","Sacramento":"SAC","Orlando":"ORL","Golden State":"GSW","Portland":"POR"}

# row, weekday, away, home, tip_local, tip_et, at_token_printed, slug, gid, gp_tip_et, code, code_source
SLATE = [
 (245,"Mon.","Orlando","Boston","7:00 PM","7:00 PM",False,"orl-vs-bos","0022600245","7:00 PM ET","ORL@BOS","injury report 11/16 09:15 AM + games page 11/16"),
 (246,"Mon.","Chicago","Cleveland","7:00 PM","7:00 PM",False,"chi-vs-cle","0022600246","7:00 PM ET","CHI@CLE","injury report 11/16 09:15 AM + games page 11/16"),
 (247,"Mon.","Memphis","Washington","7:00 PM","7:00 PM",False,"mem-vs-was","0022600247","7:00 PM ET","MEM@WAS","injury report 11/16 09:15 AM + games page 11/16"),
 (248,"Mon.","Philadelphia","Brooklyn","7:30 PM","7:30 PM",False,"phi-vs-bkn","0022600248","7:30 PM ET","PHI@BKN","injury report 11/16 09:15 AM + games page 11/16"),
 (249,"Mon.","Houston","Miami","7:30 PM","7:30 PM",False,"hou-vs-mia","0022600249","7:30 PM ET","HOU@MIA","injury report 11/16 09:15 AM + games page 11/16"),
 (250,"Mon.","Portland","Minnesota","7:00 PM","8:00 PM",False,"por-vs-min","0022600250","8:00 PM ET","POR@MIN","injury report 11/16 09:15 AM; games-page card recorded 2026-11-15 in slate-2026-11-15.json"),
 (251,"Mon.","Golden State","New Orleans","7:00 PM","8:00 PM",False,"gsw-vs-nop","0022600251","8:00 PM ET","GSW@NOP","injury report 11/16 09:15 AM + games page 11/16"),
 (252,"Mon.","Phoenix","Denver","7:00 PM","9:00 PM",False,"phx-vs-den","0022600252","9:00 PM ET","PHX@DEN","injury report 11/16 09:15 AM; games-page card recorded 2026-11-15 in slate-2026-11-15.json"),
 (253,"Tue.","New York","Toronto","7:30 PM","7:30 PM",False,"nyk-vs-tor","0022600253","7:30 PM ET","NYK@TOR","injury report 11/16 09:15 AM + games page 11/17"),
 (254,"Tue.","Portland","Minnesota","7:00 PM","8:00 PM",False,"por-vs-min","0022600254","8:00 PM ET","POR@MIN","injury report 11/16 09:15 AM + games page 11/17"),
 (255,"Tue.","Detroit","San Antonio","7:00 PM","8:00 PM",False,"det-vs-sas","0022600255","8:00 PM ET","DET@SAS","injury report 11/16 09:15 AM + games page 11/17"),
 (256,"Tue.","Charlotte","LA Lakers","7:00 PM","10:00 PM",False,"cha-vs-lal","0022600256","11:00 PM ET","CHA@LAL","injury report 11/16 09:15 AM + games page 11/17"),
 (257,"Tue.","Utah","LA Clippers","8:00 PM","11:00 PM",False,"uta-vs-lac","0022600257","10:30 PM ET","UTA@LAC","injury report 11/16 09:15 AM + games page 11/17"),
 (258,"Wed.","Memphis","Cleveland","7:00 PM","7:00 PM",False,"mem-vs-cle","0022600258","7:00 PM ET","MEM@CLE","games page 11/18 (printed order; schedule rows 215-259 print no 'at')"),
 (259,"Wed.","Houston","Indiana","7:00 PM","7:00 PM",False,"hou-vs-ind","0022600259","7:00 PM ET","HOU@IND","games page 11/18 (printed order; schedule rows 215-259 print no 'at')"),
 (260,"Wed.","Milwaukee","Miami","7:00 PM","7:00 PM",True,"mil-vs-mia","0022600260","7:00 PM ET","MIL@MIA","schedule PDF prints 'at' + games page 11/18"),
 (261,"Wed.","Philadelphia","Orlando","7:00 PM","7:00 PM",True,"phi-vs-orl","0022600261","7:00 PM ET","PHI@ORL","schedule PDF prints 'at' + games page 11/18"),
 (262,"Wed.","Chicago","Brooklyn","7:30 PM","7:30 PM",True,"chi-vs-bkn","0022600262","7:30 PM ET","CHI@BKN","schedule PDF prints 'at' + games page 11/18"),
 (263,"Wed.","Washington","Toronto","7:30 PM","7:30 PM",True,"was-vs-tor","0022600263","7:30 PM ET","WAS@TOR","schedule PDF prints 'at' + games page 11/18"),
 (264,"Wed.","Detroit","New Orleans","7:00 PM","8:00 PM",True,"det-vs-nop","0022600264","8:00 PM ET","DET@NOP","schedule PDF prints 'at' + games page 11/18"),
 (265,"Wed.","Atlanta","Oklahoma City","7:00 PM","8:00 PM",True,"atl-vs-okc","0022600265","8:00 PM ET","ATL@OKC","schedule PDF prints 'at' + games page 11/18"),
 (266,"Wed.","Boston","Denver","7:00 PM","9:00 PM",True,"bos-vs-den","0022600266","9:30 PM ET","BOS@DEN","schedule PDF prints 'at' + games page 11/18"),
 (267,"Wed.","Golden State","Dallas","8:30 PM","9:30 PM",True,"gsw-vs-dal","0022600267","8:00 PM ET","GSW@DAL","schedule PDF prints 'at' + games page 11/18"),
 (268,"Wed.","Utah","LA Lakers","7:00 PM","10:00 PM",True,"uta-vs-lal","0022600268","10:00 PM ET","UTA@LAL","schedule PDF prints 'at' + games page 11/18"),
 (269,"Wed.","Phoenix","Sacramento","7:00 PM","10:00 PM",True,"phx-vs-sac","0022600269","10:00 PM ET","PHX@SAC","schedule PDF prints 'at' + games page 11/18"),
]

TIP_CONFLICTS = {
 256: "The August schedule PDF row 256 prints 10:00 PM ET; the nba.com games page (checked 2026-11-16) and the 09:15 AM injury report both print 11:00 PM ET. Both readings kept as printed; flagged AN-02 / P9-03.",
 257: "The August schedule PDF row 257 prints 11:00 PM ET; the nba.com games page (checked 2026-11-16) and the 09:15 AM injury report both print 10:30 PM ET. Both readings kept as printed; flagged AN-02 / P9-03.",
 266: "The August schedule PDF row 266 prints 9:00 PM ET; the nba.com games page (checked 2026-11-16) prints 9:30 PM ET. Both readings kept as printed; flagged P9-04 (new this pass).",
 267: "The August schedule PDF row 267 prints 9:30 PM ET (8:30 PM local); the nba.com games page (checked 2026-11-16) prints 8:00 PM ET. Both readings kept as printed; flagged P9-04 (new this pass).",
}

def write_slate():
    games = []
    for (row, wd, away, home, tl, te, at, slug, gid, gptip, code, csrc) in SLATE:
        date = "2026-11-16" if row <= 252 else ("2026-11-17" if row <= 257 else "2026-11-18")
        g = {
            "row": row, "date": date, "weekday": wd, "away": away, "home": home,
            "tip_et_col1": tl, "tip_et_col2": te, "code": code, "code_source": csrc,
            "games_page_slug": slug, "games_page_game_id": gid,
            "games_page_tip_et": gptip,
            "games_page_url": f"https://www.nba.com/game/{slug}-{gid}",
            "at_token_printed_in_schedule": at,
            "order_corroborated_by": (
                ["schedule PDF printed 'at' token (away team first)",
                 "games page URL slug 'away-vs-home'"]
                if at else
                ["games page URL slug 'away-vs-home'",
                 "schedule PDF printed order (first cell = away, per the games-page slug)"]
                + (["injury report AWAY@HOME code"] if row <= 257 else [])
            ),
            "tip_disagreement": TIP_CONFLICTS.get(row),
        }
        games.append(g)
    doc = {
        "snapshot_id": "slate-2026-11-16",
        "kind": "official_schedule_rows",
        "source_url": SCHEDULE_URL,
        "source_document": "2026-27 NBA Regular Season Schedule By Date",
        "source_document_header": "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE",
        "source_rows": "245-269",
        "fetched_at_utc": "2026-11-16T14:33:00Z",
        "extraction_tool": "fetch_page (PDF text extraction, chunks 1-2)",
        "window": {
            "start_utc": "2026-11-16T14:35:00Z",
            "end_utc": "2026-11-19T14:35:00Z",
            "rule": ("requested maximum horizon of 3 days from the observation time; the four games "
                     "of 2026-11-19 (rows 270-273) all tip after the window end and are excluded"),
        },
        "extraction_notes": [
            "The PDF text carries the column header \"LOCAL | ET\". tip_et_col1 is the local tip time "
            "at the home venue and tip_et_col2 is the Eastern Time column, exactly as printed.",
            "The extracted PDF text prints no \"at\" token on rows 215-259 (11/10 to 11/18 rows 258-259), "
            "while rows 260 onward print \"at\"; re-confirmed on the 2026-11-16 fetch (matches the pass "
            "6/7 finding). For rows 258-259 the away/home order is corroborated by the nba.com games-page "
            "slugs mem-vs-cle and hou-vs-ind (checked 2026-11-16).",
            "Corroboration (checked 2026-11-16): the 09:15 AM injury report prints 13 matchup codes that "
            "match window rows 245-257 one-for-one (8 games of 11/16, 5 games of 11/17). The nba.com games "
            "pages for 11/16, 11/17 and 11/18 were read on 2026-11-16 and every row's away/home slug and "
            "game id (0022600 + row number) was checked; rows 250 and 252 keep their 2026-11-15 games-page "
            "card readings recorded in slate-2026-11-15.json (the cards were not re-rendered in the "
            "2026-11-16 fetch view) and their tips are additionally corroborated by today's report codes.",
            "Four tip disagreements between the August schedule PDF and the current nba.com games pages "
            "(rows 256, 257, 266, 267) are kept as printed in both columns and flagged in each row "
            "(AN-02 and new flag P9-04). The PDF header itself says SUBJECT TO CHANGE.",
            "No venue, broadcast-independent status, odds, probability or pick is present in this file "
            "or taken from the PDF.",
        ],
        "basis": {
            "away_home_rule": ("Rows 260-269 print an explicit 'at' token (away first). Rows 245-259 print "
                               "no token; the away/home reading is corroborated by the games-page slug "
                               "('away-vs-home') on every row and, for rows 245-257, by the injury report's "
                               "AWAY@HOME code."),
            "games_this_window_with_injury_report_code": 13,
            "games_this_window_without_any_code": 11,
            "games_with_games_page_slug": 25,
            "games_order_corroborated": 25,
        },
        "corroborating_urls": {
            "injury_report": REPORT_URL,
            "games_11_16": f"{GAMES_URL}?date=2026-11-16",
            "games_11_17": f"{GAMES_URL}?date=2026-11-17",
            "games_11_18": f"{GAMES_URL}?date=2026-11-18",
            "injury_index": "https://official.nba.com/nba-injury-report-2026-27-season/",
        },
        "games": games,
    }
    (SNAP / "slate-2026-11-16.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc

# conf, seed, team, w, l, pct, gb, conf_rec, div_rec, home, road, neutral, ot, last10, streak
STANDINGS = [
 ("East",1,"Boston Celtics",11,2,".846","--","10-1","4-0","6-0","5-2","0-0","1-0","9-1","W 6"),
 ("East",2,"Philadelphia 76ers",11,3,".786","0.5","11-3","3-1","6-2","5-1","0-0","0-0","8-2","W 2"),
 ("East",3,"Detroit Pistons",8,4,".667","2.5","8-3","0-0","3-2","5-2","0-0","1-0","6-4","L 1"),
 ("East",4,"Atlanta Hawks",8,6,".571","3.5","8-2","4-1","3-3","5-3","0-0","0-1","6-4","W 1"),
 ("East",5,"Miami Heat",7,6,".538","4","4-2","1-1","3-3","4-3","0-0","1-0","7-3","W 4"),
 ("East",6,"New York Knicks",7,6,".538","4","7-6","2-3","4-3","3-3","0-0","1-0","7-3","W 1"),
 ("East",7,"Cleveland Cavaliers",7,7,".500","4.5","5-5","1-0","5-2","2-5","0-0","1-0","4-6","W 1"),
 ("East",8,"Orlando Magic",5,7,".417","5.5","3-4","0-2","1-4","4-3","0-0","0-1","5-5","W 3"),
 ("East",9,"Toronto Raptors",5,8,".385","6","4-4","0-3","2-4","3-4","0-0","0-1","3-7","L 4"),
 ("East",10,"Indiana Pacers",5,9,".357","6.5","3-6","0-1","2-4","3-4","0-1","0-0","3-7","L 1"),
 ("East",11,"Charlotte Hornets",4,9,".308","7","4-7","2-2","3-4","1-5","0-0","0-0","2-8","L 2"),
 ("East",12,"Washington Wizards",4,10,".286","7.5","4-8","2-3","2-4","2-6","0-0","0-1","2-8","L 7"),
 ("East",13,"Brooklyn Nets",3,9,".250","7.5","2-7","0-2","1-3","2-6","0-0","0-1","3-7","L 1"),
 ("East",14,"Chicago Bulls",3,9,".250","7.5","2-8","1-0","1-4","2-5","0-0","1-0","2-8","W 2"),
 ("East",15,"Milwaukee Bucks",1,13,".071","10.5","1-10","1-2","1-7","0-6","0-0","0-0","1-10","L 10"),
 ("West",1,"San Antonio Spurs",12,2,".857","--","11-2","2-1","5-2","7-0","0-0","1-0","10-0","W 12"),
 ("West",2,"Los Angeles Lakers",12,2,".857","--","7-2","5-1","5-1","7-1","0-0","0-0","9-1","W 8"),
 ("West",3,"Houston Rockets",11,3,".786","1","6-3","2-1","7-1","4-2","0-0","0-0","7-3","W 4"),
 ("West",4,"Portland Trail Blazers",9,3,".750","2","9-3","4-0","3-2","6-1","0-0","0-0","7-3","W 3"),
 ("West",5,"Minnesota Timberwolves",9,4,".692","2.5","5-2","1-0","5-2","4-2","0-0","0-1","6-4","L 1"),
 ("West",6,"Memphis Grizzlies",9,4,".692","2.5","7-3","1-1","3-4","6-0","0-0","0-1","6-4","W 2"),
 ("West",7,"Oklahoma City Thunder",9,5,".643","3","6-5","1-2","5-0","4-5","0-0","0-0","5-5","W 1"),
 ("West",8,"Denver Nuggets",7,4,".636","3.5","5-4","0-2","2-2","4-2","1-0","1-0","7-3","W 2"),
 ("West",9,"Golden State Warriors",8,5,".615","3.5","6-5","3-2","6-1","2-4","0-0","1-0","8-2","L 2"),
 ("West",10,"Dallas Mavericks",7,7,".500","5","3-5","1-3","5-2","2-5","0-0","0-0","5-5","L 3"),
 ("West",11,"Phoenix Suns",5,7,".417","6","3-7","2-2","5-4","0-3","0-0","0-0","4-6","L 1"),
 ("West",12,"LA Clippers",4,8,".333","7","3-6","1-4","4-3","0-5","0-0","0-1","3-7","W 2"),
 ("West",13,"New Orleans Pelicans",4,10,".286","8","3-8","1-1","3-6","1-4","0-0","2-1","4-6","L 6"),
 ("West",14,"Sacramento Kings",1,12,".077","10.5","1-10","0-2","0-8","1-4","0-0","0-0","1-9","L 6"),
 ("West",15,"Utah Jazz",1,13,".071","11","1-11","0-2","1-7","0-6","0-0","0-2","0-10","L 12"),
]

def write_standings():
    def gsplit(s):
        a, b = s.split("-")
        return int(a), int(b)
    rows = []
    lh = lr = ln = 0
    for (conf, seed, team, w, l, pct, gb, cr, dr, home, road, neutral, ot, l10, streak) in STANDINGS:
        hw, hl = gsplit(home); rw, rl = gsplit(road); nw, nl = gsplit(neutral)
        hg, rg, ng = hw + hl, rw + rl, nw + nl
        lh += hg; lr += rg; ln += ng
        rows.append({
            "conf": conf, "seed": seed, "team": team, "w": w, "l": l, "win_pct": pct, "gb": gb,
            "conf_rec": cr, "div_rec": dr, "home": home, "road": road, "neutral": neutral,
            "ot": ot, "last10": l10, "streak": streak,
            "games_played_from_w_plus_l": w + l, "home_games": hg, "road_games": rg,
            "neutral_games": ng, "split_sum": hg + rg + ng,
            "split_sum_equals_gp": hg + rg + ng == w + l,
            "last10_games": sum(gsplit(l10)),
            "last10_matches_gp_rule": sum(gsplit(l10)) == 10,
        })
    total_lines = sum(r["games_played_from_w_plus_l"] for r in rows)
    total_w = sum(r["w"] for r in rows)
    total_l = sum(r["l"] for r in rows)
    doc = {
        "snapshot_id": "standings-2026-11-16",
        "kind": "official_standings_rows",
        "source_url": "https://www.nba.com/standings",
        "source_document": "NBA 2026-27 Regular Season Standings (page heading as printed)",
        "source_document_header": ("Page heading as printed: 'NBA 2026-27 Regular Season Standings'; "
                                   "the table header row is recorded in column_header_as_printed"),
        "source_page_title": "NBA Team Standings & Stats | NBA.com",
        "fetched_at_utc": "2026-11-16T14:36:00Z",
        "extraction_tool": "fetch_page (HTML to markdown), chunks 0 and 1 of 2",
        "column_header_as_printed": "Team | w | L | WIN% | GB | CONF | DIV | HOME | ROAD | Neutral | OT | LAST10 | STREAK",
        "column_note": ("The standings table prints the wins column with a lower-case 'w' and the losses "
                        "column as 'L' in the page's own header text; every other header is upper case. "
                        "Recorded as printed."),
        "rows": rows,
        "consistency_checks": {
            "league_team_game_lines": total_lines,
            "league_home_games": lh,
            "league_road_games": lr,
            "league_neutral_games": ln,
            "splits_sum_to_gp_all_rows": all(r["split_sum_equals_gp"] for r in rows),
            "league_wins": total_w,
            "league_losses": total_l,
            "wins_equal_losses": total_w == total_l,
            "team_game_lines_even": total_lines % 2 == 0,
            "home_plus_road_plus_neutral_equals_lines": lh + lr + ln == total_lines,
            "cross_check_vs_team_stats_pages": (
                "the GP/W/L cells of all 30 rows were re-checked against the advanced and opponent "
                "team-stat pages read the same hour (nba.com/stats/teams/advanced and /opponent); "
                "30/30 agree"),
            "cross_check_vs_games_page_cards": (
                "the team records printed on the nba.com games-page cards for 11/16, 11/17 and 11/18 "
                "(48 card readings) were compared with these rows; all agree"),
        },
        "extraction_notes": [
            "All 30 rows transcribed verbatim from the two table chunks; the tie-break procedure text "
            "(Paragraphs L.2.a / L.2.b / L.2.c) is on the page and is cited, not reproduced here.",
            "No probability, line, price or pick is derived from these rows. The rows are a dated "
            "observation for the projection/evidence surface only.",
        ],
    }
    (SNAP / "standings-2026-11-16.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc

RESULTS_ROWS = [
 # gid, away, home, away_final, home_final, note
 ("0022600236","IND","PHI",124,131,""),
 ("0022600237","LAL","PHX",131,123,""),
 ("0022600238","CHA","LAC",105,113,""),
 ("0022600239","SAS","UTA",110,102,""),
 ("0022600240","DAL","BOS",94,131,""),
 ("0022600241","NYK","TOR",112,108,"Final/OT"),
 ("0022600242","HOU","WAS",147,119,""),
 ("0022600243","ATL","MIL",113,106,""),
 ("0022600244","OKC","SAC",125,103,""),
]

def write_results():
    rows = []
    for (gid, away, home, af, hf, note) in RESULTS_ROWS:
        slug = f"{away.lower()}-vs-{home.lower()}"
        rows.append([gid, "2026-11-15", "", "", away, home, "", af, "", hf,
                     away if af > hf else home, home if af > hf else away,
                     f"https://www.nba.com/game/{slug}-{gid}"])
    doc = {
        "snapshot_id": "results-2026-11-15",
        "kind": "official_per_game_results",
        "source_document": "NBA.com scoreboard page for Sun, Nov 15 (final scores printed on each game card)",
        "source_document_header": ("Scoreboard page prints the date filter 'Sun, Nov 15'; each card prints "
                                   "the two team records, the final score and the label Final (or Final/OT)"),
        "source_url": f"{GAMES_URL}?date=2026-11-15",
        "source_index_url": f"{GAMES_URL}?date=2026-11-15",
        "fetched_at_utc": "2026-11-16T14:34:00Z",
        "extraction_tool": "fetch_page (HTML to markdown), chunks 0 and 1 of 2",
        "row_format": ["game_id","date","tip_et","arena","away_abbr","home_abbr",
                       "away_q","away_final","home_q","home_final",
                       "winner_abbr","loser_abbr","source_url"],
        "row_format_note": ("row_format lists the positional columns of each row in `rows`. Quarter-score "
                            "cells (away_q, home_q), tip and arena cells are BLANK in this snapshot: the "
                            "scoreboard page does not print them and the per-game LINESCORES pages were not "
                            "read in this pass. Every blank is flagged in row_gaps; nothing is filled in."),
        "rows": rows,
        "row_gaps": {
            "quarters_not_transcribed": [r[0] for r in RESULTS_ROWS],
            "flag": ("P9-05: quarter scores for the 11/15 games are not transcribed in this pass. The brief's "
                     "row format requires Q1-Q4 per team; those cells are left blank and flagged rather than "
                     "reconstructed. The 11/14 snapshot (results-2026-11-14.json) keeps its quarter rows."),
        },
        "verification": {
            "finals_from_scoreboard": "9 of 9 games read from the printed game cards",
            "winner_derivation": "winner_abbr is arithmetic on the printed final scores only",
            "settlement_status": ("NOT SETTLED. Settlement stays blocked by the D-01/IR-T4 rights decision "
                                  "(owner decision pending) and by the quarter-score gap above; the brief "
                                  "requires verified final scores before settlement and the settlement stamp "
                                  "remains withheld."),
            "cross_check_vs_standings": ("each card prints the two teams' post-game records; all 18 readings "
                                         "agree with standings-2026-11-16.json (fetched the same hour)"),
        },
        "extraction_notes": [
            "The NYK@TOR card prints Final/OT. The overtime marker is recorded in this note; the row's "
            "quarter cells remain blank like every other row of this snapshot.",
            "Arena and city cells are blank: the scoreboard page does not print them and the game-summary "
            "pages were not read in this pass.",
            "No probability, line, price, pick or settlement is produced from these rows.",
        ],
        "superseded_snapshot": {
            "snapshot_id": "results-2026-11-14",
            "status": ("kept as dated history with its five fully transcribed rows (quarters included); "
                       "this file is the current feed row set but is quarter-incomplete"),
        },
    }
    (SNAP / "results-2026-11-15.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc

# advanced: team, gp, w, l, min, off, def, net, astp, astto, astr, oreb, dreb, reb, tov, efg, ts, pace, pie, poss
ADV = """Los Angeles Lakers|14|12|2|672.0|122.1|114.0|8.0|58.6|1.47|17.6|33.3|64.1|49.6|16.7|58.8|63.2|100.64|54.2|1408
San Antonio Spurs|14|12|2|677.0|119.2|106.6|12.6|65.4|2.28|19.4|33.3|71.8|52.7|12.3|53.5|57.7|98.77|56.9|1395
Boston Celtics|13|11|2|629.0|118.9|105.1|13.9|67.8|1.88|19.4|33.3|67.6|50.8|15.0|55.4|59.0|96.53|56.7|1263
Houston Rockets|14|11|3|672.0|121.2|110.7|10.5|65.5|1.92|19.5|35.9|68.1|52.7|14.8|55.9|60.1|97.68|56.5|1367
Philadelphia 76ers|14|11|3|672.0|112.3|110.3|2.0|65.5|2.06|18.7|27.5|71.4|49.4|12.7|52.6|56.7|100.21|50.8|1404
Memphis Grizzlies|13|9|4|629.0|119.0|110.4|8.5|66.2|1.76|19.1|34.2|70.6|52.9|15.6|55.8|60.2|100.46|53.9|1318
Minnesota Timberwolves|13|9|4|629.0|116.0|104.5|11.5|59.9|1.63|17.8|35.4|69.5|52.7|15.6|55.5|57.9|101.27|55.2|1326
Oklahoma City Thunder|14|9|5|672.0|113.4|108.4|5.1|54.7|1.70|16.5|32.1|68.7|51.0|13.5|51.9|55.9|98.82|53.8|1384
Portland Trail Blazers|12|9|3|576.0|118.8|111.1|7.7|63.7|1.55|17.9|33.3|70.2|52.4|16.2|56.3|60.9|100.67|53.3|1208
Atlanta Hawks|14|8|6|677.0|112.8|111.1|1.7|70.9|2.01|20.1|33.0|69.2|49.8|14.7|52.7|55.7|103.69|49.0|1462
Detroit Pistons|12|8|4|586.0|114.1|109.2|4.9|67.6|1.94|19.2|29.8|66.6|48.4|14.1|53.9|58.0|99.48|53.7|1217
Golden State Warriors|13|8|5|629.0|116.1|112.0|4.1|70.0|1.75|19.4|32.7|68.5|50.7|15.9|55.4|59.5|99.66|51.8|1307
Cleveland Cavaliers|14|7|7|677.0|116.9|115.4|1.6|64.8|2.01|19.1|29.1|68.1|49.4|13.4|55.8|59.1|99.72|51.2|1407
Dallas Mavericks|14|7|7|672.0|111.8|114.5|-2.7|64.3|1.63|18.3|32.9|66.0|49.3|16.0|53.2|56.9|100.18|48.6|1404
Denver Nuggets|11|7|4|533.0|116.0|114.7|1.3|66.9|2.07|19.7|30.2|67.7|49.8|13.5|55.0|59.2|97.67|52.9|1087
Miami Heat|13|7|6|629.0|114.7|116.2|-1.5|70.9|2.07|20.1|30.3|70.1|49.8|13.9|54.5|58.1|102.49|50.0|1345
New York Knicks|13|7|6|629.0|113.7|108.2|5.5|69.2|1.82|18.8|36.7|71.8|54.0|15.2|51.9|55.7|95.66|53.5|1257
Indiana Pacers|14|5|9|672.0|110.9|112.9|-2.0|67.9|1.92|19.7|24.6|68.5|47.1|14.3|53.8|57.4|101.25|49.6|1415
Orlando Magic|12|5|7|581.0|109.7|113.4|-3.7|67.7|1.55|18.5|31.7|70.2|50.7|17.0|52.8|56.6|98.23|47.6|1185
Phoenix Suns|12|5|7|576.0|114.3|118.5|-4.2|66.0|1.93|19.4|30.0|61.6|45.7|14.4|54.3|57.5|98.79|47.9|1183
Toronto Raptors|13|5|8|629.0|113.6|112.2|1.4|67.4|1.94|19.0|35.8|67.2|50.2|14.4|51.7|55.2|99.55|49.0|1302
Charlotte Hornets|13|4|9|624.0|102.5|113.6|-11.1|62.8|1.13|15.8|36.5|74.2|53.9|20.0|48.0|52.0|96.65|42.7|1256
LA Clippers|12|4|8|581.0|111.4|115.3|-3.9|69.3|1.54|19.2|29.6|66.0|48.1|17.6|55.1|59.0|100.05|48.3|1210
New Orleans Pelicans|14|4|10|687.0|111.3|120.0|-8.6|60.6|1.51|17.0|29.7|68.0|48.6|15.4|51.9|57.7|101.83|45.7|1457
Washington Wizards|14|4|10|682.0|109.4|116.5|-7.1|59.9|1.61|17.1|28.9|65.5|47.6|14.7|51.6|56.1|99.73|46.1|1416
Brooklyn Nets|12|3|9|581.0|109.8|116.0|-6.2|65.2|1.37|17.2|32.1|69.9|50.6|17.6|52.9|57.2|99.47|46.1|1204
Chicago Bulls|12|3|9|581.0|109.4|120.3|-10.9|67.4|1.55|18.2|30.7|65.1|47.9|16.5|51.7|56.1|103.81|44.9|1257
Milwaukee Bucks|14|1|13|672.0|105.4|118.9|-13.6|65.3|1.46|17.4|30.5|64.6|47.4|16.7|50.9|54.1|100.68|42.1|1410
Sacramento Kings|13|1|12|624.0|106.8|119.8|-13.0|64.4|1.44|18.0|28.4|68.8|47.9|17.3|52.7|56.2|101.08|42.6|1312
Utah Jazz|14|1|13|682.0|105.1|116.2|-11.1|63.5|1.46|17.2|29.0|69.3|48.6|16.3|50.8|54.8|100.22|45.0|1426"""

# opponent: team, gp, w, l, min, fgm, fga, fgp, 3pm, 3pa, 3pp, ftm, fta, ftp, oreb, dreb, reb, ast, tov, stl, blk, blka, pf, pfd, pts, pm
OPP = """Los Angeles Lakers|14|12|2|48.0|39.2|86.1|45.5|15.0|40.9|36.6|21.4|28.2|75.9|13.6|27.5|41.1|27.5|18.4|9.5|4.1|6.4|24.1|23.4|114.9|-7.9
San Antonio Spurs|14|12|2|48.4|38.9|89.2|43.6|12.8|33.5|38.2|15.4|19.1|80.6|10.9|31.7|42.6|25.0|14.5|6.5|4.9|7.1|20.9|19.4|105.9|-12.9
Boston Celtics|13|11|2|48.4|35.4|84.8|41.7|14.5|43.0|33.8|17.1|22.4|76.3|12.6|30.2|42.8|25.2|16.8|7.1|4.3|4.9|22.3|21.1|102.4|-13.2
Houston Rockets|14|11|3|48.0|39.6|87.5|45.3|12.5|38.4|32.5|16.4|22.4|73.2|12.1|28.1|40.3|23.6|15.0|8.2|4.4|5.9|22.1|20.0|108.2|-10.1
Philadelphia 76ers|14|11|3|48.0|40.1|87.5|45.8|12.0|36.4|32.9|18.3|24.1|76.0|11.0|35.0|46.0|25.4|14.8|6.5|5.6|4.2|20.9|20.9|110.4|-2.1
Memphis Grizzlies|13|9|4|48.4|40.5|90.0|45.0|12.4|37.5|33.0|18.2|24.2|75.5|12.0|29.7|41.7|25.0|14.2|7.7|7.2|5.1|21.6|23.7|111.7|-8.9
Minnesota Timberwolves|13|9|4|48.4|38.6|89.0|43.4|11.5|35.3|32.5|18.1|23.3|77.6|12.3|31.0|43.3|24.6|16.8|7.9|6.4|5.1|22.8|22.0|106.8|-11.5
Oklahoma City Thunder|14|9|5|48.0|37.3|88.9|41.9|14.8|43.6|33.9|17.7|21.9|80.8|12.0|31.4|43.4|24.7|14.9|6.5|5.1|5.1|21.2|19.4|107.1|-5.1
Portland Trail Blazers|12|9|3|48.0|38.8|87.1|44.5|11.4|35.3|32.3|22.9|27.6|83.1|11.5|29.8|41.3|23.5|14.0|8.7|4.2|5.1|24.4|22.3|111.8|-7.8
Atlanta Hawks|14|8|6|48.4|41.8|87.2|47.9|12.6|36.9|34.1|19.9|25.1|79.3|11.6|34.6|46.1|27.8|18.9|9.9|5.9|3.9|19.7|21.9|116.1|-1.7
Detroit Pistons|12|8|4|48.8|38.6|87.3|44.2|12.2|36.5|33.3|20.9|26.8|78.0|13.0|32.8|45.8|23.6|17.7|8.0|6.1|6.4|22.7|23.8|110.3|-5.4
Golden State Warriors|13|8|5|48.4|40.6|88.2|46.1|12.8|37.8|34.0|18.3|23.4|78.3|12.2|30.7|42.8|27.3|16.3|8.7|5.7|5.4|22.2|21.9|112.4|-4.3
Cleveland Cavaliers|14|7|7|48.4|41.6|92.5|44.9|14.0|39.8|35.2|18.7|23.5|79.6|12.7|32.4|45.1|27.3|12.6|6.7|3.6|5.3|20.3|21.6|115.9|-1.6
Dallas Mavericks|14|7|7|48.0|42.1|89.1|47.2|12.9|37.9|34.1|17.5|23.4|74.9|12.6|31.4|44.1|27.7|15.6|8.4|4.8|5.6|20.6|21.8|114.6|2.5
Denver Nuggets|11|7|4|48.5|41.5|90.2|46.0|14.1|39.3|35.9|15.8|19.9|79.5|12.9|30.7|43.6|28.2|14.4|7.1|4.5|4.5|23.2|19.0|112.8|-1.8
Miami Heat|13|7|6|48.4|43.1|89.5|48.1|15.8|40.8|38.9|17.8|23.1|77.3|11.4|33.7|45.1|29.7|16.7|8.1|5.2|5.5|25.1|21.1|119.8|1.2
New York Knicks|13|7|6|48.4|37.4|86.4|43.3|13.4|39.4|34.0|15.8|22.1|71.8|10.9|30.7|41.6|24.9|13.4|6.6|6.0|4.2|21.3|20.7|104.0|-5.9
Indiana Pacers|14|5|9|48.0|40.9|89.3|45.8|14.1|39.2|36.1|18.5|23.7|78.0|11.5|35.2|46.7|26.2|14.9|8.4|4.3|4.2|22.8|20.4|114.5|2.4
Orlando Magic|12|5|7|48.4|39.8|85.3|46.6|13.6|35.8|38.0|19.7|25.9|75.9|10.3|31.3|41.6|27.3|15.2|9.4|5.0|4.1|23.3|22.8|112.8|4.4
Phoenix Suns|12|5|7|48.0|40.6|86.8|46.8|14.5|38.6|37.6|21.7|28.1|77.2|14.0|32.3|46.3|26.1|17.2|7.8|5.0|4.4|19.1|22.1|117.3|4.7
Toronto Raptors|13|5|8|48.4|38.4|81.0|47.4|12.7|34.5|36.8|23.3|28.8|81.0|10.7|31.5|42.2|25.8|18.9|8.2|5.5|4.4|23.8|25.6|112.8|-1.0
Charlotte Hornets|13|4|9|48.0|39.2|82.5|47.6|14.5|35.7|40.5|16.9|22.0|76.9|8.6|30.7|39.3|26.4|14.2|9.2|4.6|4.6|21.5|20.6|109.8|10.8
LA Clippers|12|4|8|48.4|42.6|88.0|48.4|13.1|36.2|36.2|18.3|24.7|74.0|12.1|31.7|43.8|26.7|16.1|8.9|4.4|4.3|21.1|21.9|116.5|4.2
New Orleans Pelicans|14|4|10|49.1|43.4|87.9|49.3|13.5|38.3|35.3|24.7|31.0|79.7|11.4|33.4|44.8|29.3|15.7|8.1|5.6|5.3|23.9|24.6|124.9|9.1
Washington Wizards|14|4|10|48.7|43.2|93.9|46.0|12.4|38.1|32.5|19.2|22.5|85.4|14.3|33.9|48.1|28.5|13.7|9.0|3.5|5.6|21.2|20.7|118.0|7.4
Brooklyn Nets|12|3|9|48.4|39.6|84.6|46.8|14.2|39.7|35.7|23.1|29.2|79.1|10.7|30.4|41.1|27.3|16.3|8.4|4.8|4.8|24.1|26.1|116.4|6.3
Chicago Bulls|12|3|9|48.4|45.2|94.8|47.7|13.7|37.6|36.4|21.9|28.7|76.5|14.0|33.5|47.5|29.3|14.3|9.8|4.9|5.9|23.2|23.7|125.9|11.3
Milwaukee Bucks|14|1|13|48.0|42.6|92.4|46.1|14.6|41.9|34.9|19.9|25.6|77.7|14.6|34.4|48.9|27.9|13.4|9.9|5.5|4.6|19.5|22.6|119.7|13.6
Sacramento Kings|13|1|12|48.0|42.2|85.5|49.4|13.7|37.1|36.9|23.1|28.9|79.8|10.3|33.0|43.3|26.1|14.6|9.3|5.5|3.5|19.7|23.0|121.2|13.5
Utah Jazz|14|1|13|48.7|39.8|87.6|45.4|12.4|35.4|35.1|26.0|31.4|82.9|11.1|34.9|46.1|23.1|13.8|9.1|5.4|6.0|23.4|23.6|118.0|10.9"""

def write_team_stats():
    adv_rows = []
    for line in ADV.strip().splitlines():
        f = line.split("|")
        adv_rows.append({
            "team": f[0], "gp": int(f[1]), "w": int(f[2]), "l": int(f[3]), "min": f[4],
            "off_rtg": f[5], "def_rtg": f[6], "net_rtg": f[7], "ast_pct": f[8], "ast_to": f[9],
            "ast_ratio": f[10], "oreb_pct": f[11], "dreb_pct": f[12], "reb_pct": f[13],
            "tov_pct": f[14], "efg_pct": f[15], "ts_pct": f[16], "pace": f[17], "pie": f[18],
            "poss": int(f[19]),
        })
    opp_rows = []
    for line in OPP.strip().splitlines():
        f = line.split("|")
        opp_rows.append({
            "team": f[0], "gp": int(f[1]), "w": int(f[2]), "l": int(f[3]), "min": f[4],
            "opp_fgm": f[5], "opp_fga": f[6], "opp_fg_pct": f[7], "opp_3pm": f[8], "opp_3pa": f[9],
            "opp_3p_pct": f[10], "opp_ftm": f[11], "opp_fta": f[12], "opp_ft_pct": f[13],
            "opp_oreb": f[14], "opp_dreb": f[15], "opp_reb": f[16], "opp_ast": f[17],
            "opp_tov": f[18], "opp_stl": f[19], "opp_blk": f[20], "opp_blka": f[21],
            "opp_pf": f[22], "opp_pfd": f[23], "opp_pts": f[24], "plus_minus": f[25],
        })
    doc = {
        "snapshot_id": "team-stats-2026-11-16",
        "kind": "official_team_stats_rows",
        "source_url": "https://www.nba.com/stats/teams/advanced",
        "source_document_header": ("NBA.com stats team pages - Advanced / Opponent / Traditional - "
                                   "2026-27 Regular Season, per-game mode"),
        "sources": {
            "advanced": "https://www.nba.com/stats/teams/advanced",
            "opponent": "https://www.nba.com/stats/teams/opponent",
            "traditional": "https://www.nba.com/stats/teams/traditional",
        },
        "source_document": "NBA.com stats team pages, 2026-27 Regular Season, per-game mode (as served)",
        "fetched_at_utc": "2026-11-16T14:32:30Z",
        "extraction_tool": "fetch_page (HTML to markdown), chunks 0 and 1 of 2 per page",
        "an04_closure": (
            "Board flag AN-04 (half-read opponent/advanced pages) is CLOSED by this snapshot: both pages "
            "are now read to their final row (30 of 30 each). The 17 rows that pass 8b could not read are "
            "transcribed here from chunk 1 of each page."),
        "model_inputs_status": (
            "REFUSED - G0 (rights gate) has not cleared NBA statistics for modelling use and the D-01/IR-T4 "
            "owner decision stands. These rows are published as dated observations on the projection surface "
            "only; no engine module consumes them and no line, probability or pick is produced from them. "
            "The brief's 're-cut the model inputs' step is recorded as REFUSED, not silently performed."),
        "columns_note": (
            "Columns are transcribed exactly as the pages serve them in per-game mode. The pages' RANK "
            "columns are not served with values in this extraction and are not transcribed. The traditional "
            "page (nba.com/stats/teams/traditional) was re-checked on 2026-11-16: the extraction serves only "
            "its filter controls (its data rows render client-side and were not returned), so its wide "
            "column set is NOT transcribed and no row count is claimed for it - flagged P9-06. The decision-"
            "relevant columns are carried on the advanced and opponent rows instead (POSS, OffRtg, DefRtg, "
            "PACE from advanced; per-game opponent scoring from opponent)."),
        "cross_checks": {
            "gp_w_l_vs_standings": ("all 30 rows' GP/W/L were compared with standings-2026-11-16.json "
                                    "read the same hour; 30/30 agree (computed in scripts/_gen_7ce5c0cc_b.py "
                                    "run log, re-verified 2026-11-16 against a fresh standings page read: "
                                    "LAL 12-2, SAS 12-2, BOS 11-2 as printed)"),
            "def_rtg_vs_opp_pts": ("DefRtg (advanced) and Opp PTS (opponent) are different denominators - "
                                   "per 100 possessions vs per game - so exact equality is not expected and "
                                   "not claimed. Their best-five sets are the same five teams (DefRtg: MIN "
                                   "104.5, BOS 105.1, SAS 106.6, NYK 108.2, OKC 108.4; Opp PTS: BOS 102.4, "
                                   "NYK 104.0, SAS 105.9, MIN 106.8, OKC 107.1), only the order differs. "
                                   "Recorded as a sanity cross-check, not as a derived metric"),
        },
        "extraction_notes": [
            "The advanced page's Dallas Mavericks row spans the two extraction chunks; its cells were "
            "joined from the chunk boundary without alteration (AST/TO 1.63 onward).",
            "POSS is printed with a thousands comma on the page (e.g. 1,408); it is stored as an integer.",
            "No rate is recomputed, renormalized or blended; every cell is as printed.",
        ],
        "advanced_rows": adv_rows,
        "opponent_rows": opp_rows,
        "row_count": len(adv_rows) + len(opp_rows),
    }
    (SNAP / "team-stats-2026-11-16.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc

if __name__ == "__main__":
    s = write_slate()
    st = write_standings()
    r = write_results()
    t = write_team_stats()
    print("slate games:", len(s["games"]),
          "| standings rows:", len(st["rows"]),
          "| checks:", st["consistency_checks"]["splits_sum_to_gp_all_rows"],
          st["consistency_checks"]["wins_equal_losses"],
          st["consistency_checks"]["home_plus_road_plus_neutral_equals_lines"],
          "| results rows:", len(r["rows"]),
          "| team-stats rows:", t["row_count"])
