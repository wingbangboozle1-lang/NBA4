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
    def test_latest_revision_has_44_rows_and_flags_the_gaps(self):
        data = load("injuries-2026-11-19-0145am.json")
        self.assertEqual(data["row_count"], 44)
        flagged = [r for r in data["rows"] if r["flags"]]
        self.assertEqual(len(flagged), 15)  # 2 page-break (IR-19-01), 6 no-status (IR-19-02), 7 position-placed continuation (IR-19-05)
        self.assertTrue(all(r["flags"][0].startswith("IR-19-") for r in flagged))

    def test_consecutive_diff_reports_no_changes_and_names_the_gap(self):
        diff = load("injuries-2026-11-19-0130-to-0145.diff.json")
        self.assertEqual(diff["counts"]["old_rows"], diff["counts"]["new_rows"], 44)
        self.assertEqual(diff["counts"]["status_changes"], 0)
        self.assertEqual(diff["counts"]["reason_changes"], 0)
        self.assertIn("unobserved gap", diff["consecutive_in_index"])

    def test_raw_extracts_have_seven_cells_per_row(self):
        for name in ("injury-2026-11-19T0130am-et.pipes", "injury-2026-11-19T0145am-et.pipes"):
            body = [l for l in (SNAP / "raw" / name).read_text(encoding="utf-8").splitlines() if l and not l.startswith("#") and "|" in l and not l.split("|")[0].startswith(("revision", "document", "source", "fetched", "extraction", "fields"))]
            self.assertEqual(len(body), 44, name)
            self.assertTrue(all(len(l.split("|")) == 7 for l in body), name)


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
