#!/usr/bin/env python3
"""Generate the 2026-11-19 refresh files for the 11/17 and 11/18 official finals and the 11/19 injury revisions.

Task BR (session ``arena/76f88812-nba4``, eleventh daily refresh cycle). Stdlib only.

Inputs (transcribed by hand from official pages, recorded here so the build is reproducible):

* ``FINALS`` below: for every final of 2026-11-17 and 2026-11-18, the printed LINESCORES table of the
  official nba.com game summary page (team, Q1-Q4, OT columns, Final) and the printed GAME INFO
  (tip time, arena, city). ``GAMES_PAGE_FINALS`` holds the Final totals printed on the nba.com
  scoreboard for the same date; the build asserts they equal the linescore finals.
* ``data/snapshots/raw/injury-2026-11-19T0130am-et.pipes`` and ``...0145am-et.pipes``: verbatim
  extracts of the two 11/19/26 injury revisions (blank = not printed).

Outputs:

* ``data/snapshots/results-2026-11-17.json``, ``data/snapshots/results-2026-11-18.json``
* ``data/snapshots/injuries-2026-11-19-0130-to-0145.diff.json`` (the consecutive 01:30 -> 01:45 AM ET diff)

The 01:45 AM ET injury file of record (``injuries-2026-11-19-0145am.json``), its newest pointer and the
schedule rows are owned by the other 11/19 session (merged in PR #84) and are not written here.

Every settlement rule is applied in code: a team line is SETTLEMENT_ELIGIBLE only when its printed
period scores (including any printed overtime) add to its printed final and the scoreboard final agrees.
Run: ``python3 scripts/build_window_2026_11_19.py`` (``--check`` fails if any output would change).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
RAW = SNAP / "raw"

FETCHED = "2026-11-19 (session window 06:59Z-07:07Z; per-document time not logged)"
INDEX = "https://official.nba.com/nba-injury-report-2026-27-season/"
EXTRACTION = "fetch_page (web page extraction of the nba.com game summary LINESCORES and GAME INFO tables; scoreboard totals from the games page)"

# (game_id, date, tip_et, arena, city, away, home, away_q, away_final, home_q, home_final, away_ot, home_ot, page_slug)
FINALS_1117 = [
    ("0022600253", "2026-11-17", "7:30 PM", "Scotiabank Arena", "Toronto, ON", "NYK", "TOR", [23, 31, 26, 31], 111, [29, 21, 33, 19], 102, [], [], "nyk-vs-tor-0022600253"),
    ("0022600254", "2026-11-17", "8:00 PM", "Target Center", "Minneapolis, MN", "POR", "MIN", [17, 31, 31, 26], 105, [29, 20, 30, 27], 106, [], [], "por-vs-min-0022600254"),
    ("0022600255", "2026-11-17", "8:00 PM", "Frost Bank Center", "San Antonio, TX", "DET", "SAS", [26, 29, 23, 27], 105, [33, 21, 18, 21], 93, [], [], "det-vs-sas-0022600255"),
    ("0022600256", "2026-11-17", "11:00 PM", "Crypto.com Arena", "Los Angeles, CA", "CHA", "LAL", [34, 32, 28, 17], 114, [30, 29, 22, 30], 118, [3], [7], "cha-vs-lal-0022600256"),
    ("0022600257", "2026-11-17", "10:30 PM", "Intuit Dome", "Inglewood, CA", "UTA", "LAC", [35, 23, 30, 44], 132, [29, 33, 24, 21], 107, [], [], "uta-vs-lac-0022600257"),
]
FINALS_1118 = [
    ("0022600258", "2026-11-18", "7:00 PM", "Rocket Arena", "Cleveland, OH", "MEM", "CLE", [30, 41, 29, 24], 124, [37, 35, 27, 22], 121, [], [], "mem-vs-cle-0022600258"),
    ("0022600259", "2026-11-18", "7:00 PM", "Gainbridge Fieldhouse", "Indianapolis, IN", "HOU", "IND", [39, 23, 31, 26], 119, [28, 18, 30, 28], 104, [], [], "hou-vs-ind-0022600259"),
    ("0022600260", "2026-11-18", "7:00 PM", "Kaseya Center", "Miami, FL", "MIL", "MIA", [23, 25, 38, 44], 130, [34, 40, 38, 25], 137, [], [], "mil-vs-mia-0022600260"),
    ("0022600261", "2026-11-18", "7:00 PM", "Kia Center", "Orlando, FL", "PHI", "ORL", [27, 37, 28, 29], 121, [40, 29, 28, 19], 116, [], [], "phi-vs-orl-0022600261"),
    ("0022600262", "2026-11-18", "7:30 PM", "Barclays Center", "Brooklyn, NY", "CHI", "BKN", [37, 39, 35, 26], 137, [21, 30, 26, 30], 107, [], [], "chi-vs-bkn-0022600262"),
    ("0022600263", "2026-11-18", "7:30 PM", "Scotiabank Arena", "Toronto, ON", "WAS", "TOR", [29, 20, 29, 25], 103, [23, 24, 32, 20], 99, [], [], "was-vs-tor-0022600263"),
    ("0022600264", "2026-11-18", "8:00 PM", "Smoothie King Center", "New Orleans, LA", "DET", "NOP", [31, 36, 25, 30], 122, [31, 29, 26, 23], 109, [], [], "det-vs-nop-0022600264"),
    ("0022600265", "2026-11-18", "8:00 PM", "Paycom Center", "Oklahoma City, OK", "ATL", "OKC", [31, 33, 19, 34], 117, [29, 22, 32, 29], 112, [], [], "atl-vs-okc-0022600265"),
    ("0022600266", "2026-11-18", "9:30 PM", "Ball Arena", "Denver, CO", "BOS", "DEN", [30, 31, 19, 21], 101, [24, 25, 31, 25], 105, [], [], "bos-vs-den-0022600266"),
    ("0022600267", "2026-11-18", "8:00 PM", "American Airlines Center", "Dallas, TX", "GSW", "DAL", [25, 24, 23, 22], 94, [35, 27, 30, 24], 116, [], [], "gsw-vs-dal-0022600267"),
    ("0022600268", "2026-11-18", "10:00 PM", "Crypto.com Arena", "Los Angeles, CA", "UTA", "LAL", [29, 27, 22, 31], 109, [34, 20, 22, 21], 97, [], [], "uta-vs-lal-0022600268"),
    ("0022600269", "2026-11-18", "10:00 PM", "Golden 1 Center", "Sacramento, CA", "PHX", "SAC", [36, 29, 34, 29], 128, [31, 29, 24, 23], 107, [], [], "phx-vs-sac-0022600269"),
]
# Final totals as printed on the nba.com scoreboard (games page) for the same date, keyed by game id.
GAMES_PAGE_FINALS = {
    "0022600253": (111, 102), "0022600254": (105, 106), "0022600255": (105, 93), "0022600256": (114, 118), "0022600257": (132, 107),
    "0022600258": (124, 121), "0022600259": (119, 104), "0022600260": (130, 137), "0022600261": (121, 116), "0022600262": (137, 107),
    "0022600263": (103, 99), "0022600264": (122, 109), "0022600265": (117, 112), "0022600266": (101, 105), "0022600267": (94, 116),
    "0022600268": (109, 97), "0022600269": (128, 107),
}
GAMEBOOK_NOTE = "The gamebook PDF link printed on each game summary page was not readable from the fetch tool in this cycle (statsdmz.nba.com returned errors, including for the 11/16 book read earlier); the game summary LINESCORES table was used instead."


def results_doc(date, finals, page_date_label):
    rows, checks, all_ok = [], [], True
    for gid, d, tip, arena, city, away, home, aq, af, hq, hf, aot, hot, slug in finals:
        url = f"https://www.nba.com/game/{slug}"
        winner, loser = (away, home) if af > hf else (home, away)
        rows.append([gid, d, tip, arena, city, away, home, aq, af, hq, hf, winner, loser, url, aot, hot])
        gp_away, gp_home = GAMES_PAGE_FINALS[gid]
        for team, quarters, final, ot in ((away, aq, af, aot), (home, hq, hf, hot)):
            total = sum(quarters) + sum(ot)
            ok = total == final
            all_ok = all_ok and ok
            checks.append([gid, team, quarters, ot, total, final, ok])
        if (gp_away, gp_home) != (af, hf):
            raise SystemExit(f"scoreboard final mismatch for {gid}: {(gp_away, gp_home)} vs {(af, hf)}")
    games_page = f"https://www.nba.com/games?date={date}"
    return {
        "snapshot_id": f"results-{date}",
        "kind": "official_finals_observation",
        "source_document": "official nba.com game summary pages (LINESCORES and GAME INFO) for every game of the date; scoreboard totals from the games page",
        "source_document_header": "LINESCORES / GAME INFO as printed on each official game summary page; Final totals on the scoreboard",
        "source_url": "https://www.nba.com/game/<game slug> (one per row; see column 14)",
        "source_index_url": games_page,
        "fetched_at_utc": FETCHED,
        "extraction_tool": EXTRACTION,
        "row_format": ["game_id", "date", "tip_et", "arena", "city", "away", "home", "away_q", "away_final", "home_q", "home_final", "winner", "loser", "source_url", "away_ot", "home_ot"],
        "row_format_note": "away_q/home_q hold the four printed regulation periods; any printed overtime period sits in away_ot/home_ot (the 2026-11-16 schema). The total used for the check is the regulation periods plus the printed OT periods. The tip is the GAME INFO start time as printed.",
        "rows": rows,
        "verification": {
            "quarter_sum_rule": "For every row the printed periods (regulation, plus any printed OT) were added and compared with the printed Final.",
            "quarter_sum_check": checks,
            "agreement": f"{sum(1 for c in checks if c[6])} of {len(checks)} team lines agree; scoreboard Final equals the linescore Final for all {len(rows)} games.",
            "settlement_status": "SETTLEMENT_ELIGIBLE for every team line" if all_ok else "BLOCKED on at least one line",
        },
        "extraction_notes": [
            f"One row per game of {date}; {len(rows)} games on the scoreboard for this date.",
            "Overtime: " + ("CHA@LAL went to one overtime period (CHA 3, LAL 7 printed in the OT1 column)." if any(r[14] or r[15] for r in rows) else "none."),
            GAMEBOOK_NOTE,
        ],
        "secondary_sources": {
            "games_page": games_page,
            "game_pages": {r[0]: r[13] for r in rows},
            "gamebook_links_printed_not_read": [f"https://statsdmz.nba.com/pdfs/{date.replace('-', '')}/{date.replace('-', '')}_{r[5]}{r[6]}_book.pdf" for r in rows],
        },
    }


def parse_pipes(path: Path):
    meta, rows = {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        if line.startswith(("revision_et_label:", "document_header:", "source_url:", "source_index_url:", "fetched_at_utc:", "extraction_tool:", "fields:")):
            k, v = line.split(":", 1)
            meta[k] = v.strip()
            continue
        cells = line.split("|")
        if len(cells) != 7:
            raise SystemExit(f"{path}: expected 7 cells, got {len(cells)}: {line}")
        rows.append(dict(zip(["game_date", "game_time_et", "matchup", "team", "player", "status", "reason"], cells)))
    return meta, rows


def key(r):
    return (r["matchup"], r["team"], r["player"])


def injury_outputs():
    m45, r45 = parse_pipes(RAW / "injury-2026-11-19T0145am-et.pipes")
    m30, r30 = parse_pipes(RAW / "injury-2026-11-19T0130am-et.pipes")
    changes, status_changes, reason_changes, team_changes = [], 0, 0, 0
    for a, b in zip(r30, r45):  # the two revisions are aligned by printed position (both 44 rows)
        if key(a) != key(b):
            team_changes += 1
            changes.append({"type": "identity", "old": a, "new": b})
        if a["status"] != b["status"]:
            status_changes += 1
            changes.append({"type": "status", "old": a["status"], "new": b["status"], "row": key(b)})
        if a["reason"] != b["reason"]:
            reason_changes += 1
            changes.append({"type": "reason", "old": a["reason"], "new": b["reason"], "row": key(b)})
    rev_url = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf"
    prev_url = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_30AM.pdf"
    diff = {
        "diff_id": "injuries-2026-11-19-0130-to-0145.diff",
        "kind": "official_injury_report_consecutive_diff",
        "old": {"revision_label": "11/19/26 01:30 AM", "document": "Injury Report: 11/19/26 01:30 AM", "source_url": prev_url, "retrieved_utc": FETCHED, "raw_extract": "data/snapshots/raw/injury-2026-11-19T0130am-et.pipes"},
        "new": {"revision_label": "11/19/26 01:45 AM", "document": "Injury Report: 11/19/26 01:45 AM", "source_url": rev_url, "retrieved_utc": FETCHED, "raw_extract": "data/snapshots/raw/injury-2026-11-19T0145am-et.pipes"},
        "alignment": "position-aligned: both revisions print 44 rows in the same order; identity cells compared row by row",
        "changes": changes,
        "counts": {"old_rows": len(r30), "new_rows": len(r45), "status_changes": status_changes, "reason_changes": reason_changes, "team_changes": team_changes, "printing_variances": 0, "realigned": 0},
        "consecutive_in_index": "1:30 a.m. and 1:45 a.m. ET are consecutive entries of the official index listing (12:00 a.m. through 1:45 a.m. ET). The stored predecessor 11/17 11:15 AM is NOT consecutive: the index listing read in this session shows 11/19 entries only from 12:00 a.m. to 1:45 a.m. ET; no 11/18 entries were transcribed, so 11/17 11:15 AM to 11/19 12:00 AM is an unobserved gap (flag IR-19-04).",
        "source_url": rev_url,
        "source_document_header": "Injury Report: 11/19/26 01:45 AM",
        "fetched_at_utc": FETCHED,
        "extraction_tool": "scripts/build_window_2026_11_19.py (stdlib comparison of the two verbatim extracts)",
        "source_index_url": INDEX,
    }
    return diff


def outputs():
    out = {}
    out["results-2026-11-17.json"] = results_doc("2026-11-17", FINALS_1117, "11/17")
    out["results-2026-11-18.json"] = results_doc("2026-11-18", FINALS_1118, "11/18")
    out["injuries-2026-11-19-0130-to-0145.diff.json"] = injury_outputs()
    return {k: json.dumps(v, indent=2, ensure_ascii=False) + "\n" for k, v in out.items()}


def main(argv):
    check = "--check" in argv
    changed = False
    for name, text in outputs().items():
        path = SNAP / name
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old == text:
            print(f"unchanged {name}")
            continue
        changed = True
        if check:
            print(f"OUT OF DATE {name}")
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {name}")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
