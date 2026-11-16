#!/usr/bin/env python3
"""One-shot derived-aggregates writer for the 2026-11-16 refresh.
Derived arithmetic on the dated snapshots only; performs no fetching. Every
input cell is named in `derived_from` / `inputs`."""
from __future__ import annotations
import json
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"

st = json.loads((SNAP / "standings-2026-11-16.json").read_text(encoding="utf-8"))
inj = json.loads((SNAP / "injuries-2026-11-16-0915am.json").read_text(encoding="utf-8"))
diff = json.loads((SNAP / "injuries-2026-11-16-0900-to-0915.diff.json").read_text(encoding="utf-8"))
res = json.loads((SNAP / "results-2026-11-15.json").read_text(encoding="utf-8"))

rows = st["rows"]
home_w = sum(int(r["home"].split("-")[0]) for r in rows)
home_l = sum(int(r["home"].split("-")[1]) for r in rows)
rate = home_w / (home_w + home_l)
pts = 12.0 * NormalDist().inv_cdf(rate)

inj_rows = [r for g in inj["games"] for r in g["rows"]]
nys = sum(1 for r in inj_rows if r.get("reason") == "NOT YET SUBMITTED")
with_status = sum(1 for r in inj_rows if r.get("player") and r.get("status"))
lost = sum(1 for r in inj_rows if r.get("team") == "__lost__")

cc = st["consistency_checks"]

agg = {
    "aggregate_id": "aggregates-2026-11-16",
    "kind": "derived_from_official_snapshots",
    "source_url": "https://www.nba.com/standings",
    "source_document_header": st["source_document_header"],
    "fetched_at_utc": "2026-11-16T14:36:00Z",
    "extraction_tool": "scripts/_gen_7ce5c0cc_c.py (derived; performs no fetching)",
    "derived_from": {
        "results": res["source_url"],
        "standings": st["source_url"],
        "injuries": inj["source_url"],
        "slate": "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf",
    },
    "derived_at_utc": "2026-11-16T14:58:00Z",
    "inputs": {
        "results": "results-2026-11-15.json",
        "standings": "standings-2026-11-16.json",
        "injuries": "injuries-2026-11-16-0915am.json",
        "injuries_diff": "injuries-2026-11-16-0900-to-0915.diff.json",
    },
    "home_court": {
        "measured_home_win_rate": round(rate, 4),
        "rate_exact": f"{home_w}/{home_w + home_l}",
        "home_wins": home_w,
        "home_losses": home_l,
        "home_games": home_w + home_l,
        "neutral_team_lines_held_out": cc["league_neutral_games"],
        "point_value_proposed": round(pts, 3),
        "point_value_note": (
            "points = MARGIN_SD_DEFAULT x Phi^-1(rate) = 12.0 x "
            f"{NormalDist().inv_cdf(rate):.4f}; the exact inverse of ratings.win_probability. "
            "PROPOSED, NOT APPLIED: ratings.HOME_ADVANTAGE_POINTS stays 0.0 until pre-registration "
            "and rights gate G0 clear; the normal-margin mapping remains UNVALIDATED."),
    },
    "result_feed": {
        "games": len(res["rows"]),
        "team_lines_checked": 0,
        "lines_where_quarter_sum_equals_printed_final": 0,
        "lines_that_disagree": 0,
        "settlement_eligible": False,
        "settlement_blocked_reasons": [
            "quarter scores not transcribed for the 11/15 games (flag P9-05); the quarter-sum check cannot run",
            "D-01/IR-T4 rights decision stands: no settlement stamp is issued",
        ],
        "finals_recorded": len(res["rows"]),
    },
    "injury_load": {
        "rows": len(inj_rows),
        "rows_with_a_status": with_status,
        "not_yet_submitted_rows": nys,
        "unaligned_rows_after_page_breaks": lost,
        "source_url": inj["source_url"],
    },
    "standings_consistency": {
        "league_wins": cc["league_wins"],
        "league_losses": cc["league_losses"],
    },
    "consecutive_revision": {
        "status_changes": diff["counts"]["status_changes"],
        "reason_changes": diff["counts"]["reason_changes"],
        "printing_variances": diff["counts"]["printing_variances"],
        "summary": (
            f'0 status changes, {diff["counts"]["printing_variances"]} name-spelling variance between '
            "09:00 and 09:15 AM ET"),
    },
    "feed_delay": {
        "value": "[NO INPUT]",
        "retrieval_lag_hours_after_last_printed_tip": 13.57,
        "note": (
            "the results document prints no game-end clock; no end time is invented. The lag is measured "
            "from the schedule-printed 9:00 PM ET tip of the last 11/15 game (2026-11-16T01:00Z) to the "
            "14:34 UTC scoreboard fetch."),
    },
}
(SNAP / "aggregates-2026-11-16.json").write_text(json.dumps(agg, indent=1) + "\n", encoding="utf-8")
print("home rate:", agg["home_court"]["rate_exact"], "=", round(rate, 4),
      "| proposed pts:", agg["home_court"]["point_value_proposed"],
      "| injury rows:", len(inj_rows), "| results:", len(res["rows"]))
