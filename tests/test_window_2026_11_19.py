"""Regression tests for the 2026-11-19 refresh (task BR, session arena/76f88812-nba4).

Stdlib unittest only. They read the committed snapshot files and rendered pages; they never fetch the web.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"


def load(name):
    return json.loads((SNAP / name).read_text(encoding="utf-8"))


class FinalsSettlementTests(unittest.TestCase):
    def test_every_team_line_adds_to_its_printed_final(self):
        for name, games in (("results-2026-11-17.json", 5), ("results-2026-11-18.json", 12)):
            data = load(name)
            self.assertEqual(len(data["rows"]), games, name)
            for row in data["rows"]:
                gid, _date, _tip, _arena, _city, away, home, aq, af, hq, hf, winner, loser, url, aot, hot = row
                self.assertEqual(sum(aq) + sum(aot), af, (gid, away))
                self.assertEqual(sum(hq) + sum(hot), hf, (gid, home))
                self.assertTrue(url.startswith("https://www.nba.com/game/"), url)
                self.assertIn(winner, (away, home))
                self.assertEqual(winner, away if af > hf else home)
            self.assertIn("SETTLEMENT_ELIGIBLE for every team line", data["verification"]["settlement_status"])

    def test_overtime_game_is_the_only_one_with_ot_periods(self):
        ot_games = [r[0] for r in load("results-2026-11-17.json")["rows"] + load("results-2026-11-18.json")["rows"] if r[14] or r[15]]
        self.assertEqual(ot_games, ["0022600256"])


class InjuryRevisionTests(unittest.TestCase):
    """The 01:45 AM ET file of record is owned by PR #84 (session 639c095c); these tests only read it."""

    def test_latest_revision_has_44_rows_and_flags_the_gaps(self):
        data = load("injuries-2026-11-19-0145am.json")
        rows = [r for g in data["games"] for r in g["rows"]] + data["unattributed_rows"]
        self.assertEqual(len(rows), data["row_count"], 44)
        self.assertEqual(len(rows), 44)
        flagged = [r for r in rows if r.get("flag")]
        self.assertEqual(len(flagged), 15)
        self.assertEqual(len(data["unattributed_rows"]), 2)

    def test_eleven_twenty_games_match_the_schedule_rows_43_to_51(self):
        data = load("injuries-2026-11-19-0145am.json")
        nov20 = {g["matchup"] for g in data["games"] if g["game_date"] == "2026-11-20"}
        self.assertEqual(len(nov20), 9)
        raw = (SNAP / "raw" / "schedule-2026-11-20-11-21-rows-43-51-274-279.txt").read_text(encoding="utf-8").splitlines()
        game_rows = [l.split("|") for l in raw if l and not l.startswith("#")]
        self.assertEqual([r[0] for r in game_rows if r[2] == "11/20/26"], [str(n) for n in range(43, 52)])
        self.assertEqual([r[0] for r in game_rows if r[2] == "11/21/26"], [str(n) for n in range(274, 280)])
        self.assertEqual(len(game_rows), 15)

    def test_consecutive_diff_reports_no_changes_and_names_the_gap(self):
        diff = load("injuries-2026-11-19-0130-to-0145.diff.json")
        self.assertEqual(diff["counts"]["old_rows"], diff["counts"]["new_rows"], 44)
        self.assertEqual(diff["counts"]["status_changes"], 0)
        self.assertEqual(diff["counts"]["reason_changes"], 0)
        self.assertEqual(diff["counts"]["team_changes"], 0)
        self.assertIn("unobserved gap", diff["consecutive_in_index"])

    def test_raw_extracts_have_seven_cells_per_row(self):
        for name in ("injury-2026-11-19T0130am-et.pipes", "injury-2026-11-19T0145am-et.pipes"):
            body = [l for l in (SNAP / "raw" / name).read_text(encoding="utf-8").splitlines() if l and not l.startswith("#") and "|" in l and not l.startswith(("revision", "document", "source", "fetched", "extraction", "fields"))]
            self.assertEqual(len(body), 44, name)
            self.assertTrue(all(len(l.split("|")) == 7 for l in body), name)

    def test_both_raw_extracts_agree_cell_for_cell(self):
        def body(name):
            return [l for l in (SNAP / "raw" / name).read_text(encoding="utf-8").splitlines() if l and not l.startswith("#") and "|" in l and not l.startswith(("revision", "document", "source", "fetched", "extraction", "fields"))]
        self.assertEqual(body("injury-2026-11-19T0130am-et.pipes"), body("injury-2026-11-19T0145am-et.pipes"))


class BuildAndPagesTests(unittest.TestCase):
    def test_generated_outputs_are_current(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_window_2026_11_19.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_pages_carry_the_refresh_banners(self):
        injuries = (ROOT / "injuries.html").read_text(encoding="utf-8")
        results = (ROOT / "results.html").read_text(encoding="utf-8")
        slate = (ROOT / "slate.html").read_text(encoding="utf-8")
        self.assertIn("01:45 AM ET", injuries)
        self.assertIn("retrieved 19 Nov 2026 in the 06:59–07:07 UTC session window", injuries)
        self.assertIn("BEGIN SNAPSHOT:injuries-latest", injuries)
        self.assertIn("Settlement stamp, 19 Nov 2026", results)
        self.assertIn("Freshness flag BR-S1", slate)


if __name__ == "__main__":
    unittest.main()
