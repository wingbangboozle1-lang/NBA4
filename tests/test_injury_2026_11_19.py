"""Task BR: provenance tests for the 11/19 01:45 AM ET injury snapshot.

Every printed value in the snapshot must appear verbatim in the raw extraction it was generated from,
and every schedule-filled date/time must match the official schedule GAME rows cited in the file.
Offline: reads only files in the repository."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "data/snapshots/injuries-2026-11-19-0145am.json"
PTR = ROOT / "data/snapshots/injuries-newest-pointer-2026-11-19.json"
RAW = ROOT / "data/snapshots/raw/injury-2026-11-19T0145am-et.txt"


class Injury20261119Tests(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.d = json.loads(SNAP.read_text(encoding="utf-8"))
        cls.raw = RAW.read_text(encoding="utf-8")

    def test_header_and_source(self):
        self.assertEqual(self.d["source_document_header"], "Injury Report: 11/19/26 01:45 AM")
        self.assertEqual(self.d["source_url"],
                         "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf")
        self.assertEqual(self.d["revision_utc"], "2026-11-19T06:45:00Z")  # 01:45 ET on 11/19 (UTC-5)
        self.assertIn("injury-2026-11-19T0145am-et.txt", self.d["raw_extraction"])

    def test_counts_match_structure(self):
        rows = sum(len(g["rows"]) for g in self.d["games"]) + len(self.d["unattributed_rows"])
        self.assertEqual(rows, self.d["row_count"])
        self.assertEqual(len(self.d["games"]), self.d["games_counted"])
        self.assertEqual(self.d["row_count"], 44)
        self.assertEqual(len(self.d["unattributed_rows"]), 2)

    def test_every_printed_player_name_is_in_raw(self):
        names = [r["player"] for g in self.d["games"] for r in g["rows"]] + \
                [r["player"] for r in self.d["unattributed_rows"]]
        for name in names:
            if name:
                self.assertIn(name, self.raw, name)

    def test_statuses_are_printed_vocabulary(self):
        allowed = {"", "Out", "Questionable", "Available"}
        for g in self.d["games"]:
            for r in g["rows"]:
                self.assertIn(r["status"], allowed, r)

    def test_unattributed_fragments_have_no_team_or_matchup(self):
        for r in self.d["unattributed_rows"]:
            self.assertEqual(r["team"], "")
            self.assertTrue(r["unverified"])
            self.assertIn(r["player"], ("Kuminga, Jonathan", "Pullin, Zyon"))

    def test_schedule_fills_match_official_schedule_rows(self):
        sched = {"GSW@MEM": (270, "2026-11-19", "8:00 PM"), "POR@MIL": (271, "2026-11-19", "8:00 PM"),
                 "NYK@MIN": (272, "2026-11-19", "8:00 PM"), "LAC@SAS": (273, "2026-11-19", "8:00 PM"),
                 "CHA@ATL": (43, "2026-11-20", "7:00 PM"), "ORL@BKN": (44, "2026-11-20", "7:30 PM"),
                 "IND@CLE": (45, "2026-11-20", "7:30 PM"), "TOR@DET": (46, "2026-11-20", "7:30 PM"),
                 "WAS@CHI": (47, "2026-11-20", "8:00 PM"), "NOP@OKC": (48, "2026-11-20", "8:00 PM"),
                 "PHX@UTA": (49, "2026-11-20", "9:30 PM"), "HOU@DEN": (50, "2026-11-20", "10:00 PM"),
                 "SAC@LAL": (51, "2026-11-20", "10:00 PM")}
        for g in self.d["games"]:
            row, date, tip = sched[g["matchup"]]
            self.assertEqual(g["game_date"], date, g["matchup"])
            self.assertEqual(g["schedule_row"], row)
            self.assertEqual(g["tip_et_from_schedule"], tip)
            self.assertIsNone(g["tip_disagreement"])

    def test_printed_out_rows_spot_check(self):
        lac = next(g for g in self.d["games"] if g["matchup"] == "LAC@SAS")
        beal = [r for r in lac["rows"] if r["player"] == "Beal, Bradley"][0]
        self.assertEqual((beal["team"], beal["status"], beal["reason"]),
                         ("LA Clippers", "Out", "Injury/Illness - Right Knee Injury Management"))
        nyk = next(g for g in self.d["games"] if g["matchup"] == "NYK@MIN")
        self.assertFalse(any(r["team"] == "New York Knicks" for r in nyk["rows"]))  # absence not interpreted

    def test_pointer_file(self):
        p = json.loads(PTR.read_text(encoding="utf-8"))
        self.assertEqual(p["newest_listed_label"], "11/19 01:45 AM ET")
        self.assertTrue(p["fetched_at_utc"].startswith("2026-11-19T"))
        self.assertTrue(p["source_url"].startswith("https://official.nba.com/"))
        self.assertTrue(re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$", p["fetched_at_utc"]))


if __name__ == "__main__":
    unittest.main()
