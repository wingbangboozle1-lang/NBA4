"""Tests for the official-snapshot data files and their rendered tables.

The site's slate and injury tables are generated from ``data/snapshots/*.json``
by ``scripts/build_snapshots.py``. These tests keep the data honest (provenance,
no invented values) and keep the published pages in sync with the data.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_snapshots  # noqa: E402

SNAPSHOTS = ROOT / "data" / "snapshots"
REQUIRED_PROVENANCE = ("source_url", "source_document_header", "fetched_at_utc", "extraction_tool")


def load(name: str) -> dict:
    return json.loads((SNAPSHOTS / name).read_text(encoding="utf-8"))


class SlateSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("slate-2026-11-14.json")

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertTrue(self.data["source_url"].startswith("https://"))
        self.assertIn("SUBJECT TO CHANGE", self.data["source_document_header"])

    def test_every_game_is_complete_and_sourced(self) -> None:
        for game in self.data["games"]:
            self.assertTrue(game["date"].startswith("2026-11-"))
            self.assertIn(game["away"], build_snapshots.ABBR)
            self.assertIn(game["home"], build_snapshots.ABBR)
            self.assertTrue(game["tip_et_col1"].endswith(" PM"))
            self.assertTrue(game["tip_et_col2"].endswith(" PM"))
            self.assertGreaterEqual(game["row"], 231)
            self.assertLessEqual(game["row"], 252)

    def test_window_is_within_three_days(self) -> None:
        dates = {game["date"] for game in self.data["games"]}
        self.assertEqual(dates, {"2026-11-14", "2026-11-15", "2026-11-16"})
        self.assertEqual(len(self.data["games"]), 22)

    def test_no_model_output_is_stored(self) -> None:
        forbidden = ("line", "price", "probability", "pick", "edge")
        for game in self.data["games"]:
            for key in game:
                self.assertNotIn(key, forbidden, f"model output stored for row {game['row']}")


class InjurySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("injuries-2026-11-14-0430am.json")
        cls.rows = [row for game in cls.data["games"] for row in game["rows"]]

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("04:30 AM", self.data["source_document_header"])
        self.assertIn("supersedes", self.data["supersession_note"])

    def test_every_row_has_a_status_or_reports_not_submitted(self) -> None:
        for row in self.rows:
            if row["status"]:
                self.assertIn(
                    row["status"], {"Out", "Available", "Probable", "Questionable"}
                )
            else:
                self.assertEqual(row["reason"], "NOT YET SUBMITTED")

    def test_lost_cells_are_empty_and_flagged(self) -> None:
        lost = [row for row in self.rows if row["team"] == "__lost__"]
        self.assertEqual(len(lost), 1)
        self.assertEqual(lost[0]["player"], "Traore, Nolan")
        self.assertTrue(lost[0]["unverified"])
        self.assertTrue(lost[0]["flag"])

        repaired = [
            game for game in self.data["games"] if game["cells_source"].startswith("schedule")
        ]
        for game in repaired:
            self.assertIn("game_date_from_schedule", game)
            self.assertIn("tip_et_from_schedule", game)
            self.assertIsNotNone(game["schedule_row"])

    def test_schedule_repaired_times_match_the_slate_snapshot(self) -> None:
        slate = {
            game["row"]: game for game in load("slate-2026-11-14.json")["games"]
        }
        for game in self.data["games"]:
            row = game["schedule_row"]
            if row not in slate:
                continue
            printed = f'{slate[row]["tip_et_col1"]} / {slate[row]["tip_et_col2"]}'
            self.assertIn(game["tip_et_from_schedule"], printed)

    def test_no_derived_or_model_values(self) -> None:
        for row in self.rows:
            for key in row:
                self.assertNotIn(
                    key, ("probability", "minutes", "impact", "pick"), key
                )


class RenderedPageTests(unittest.TestCase):
    def test_pages_are_in_sync_with_the_snapshots(self) -> None:
        for block_id, (page_name, render) in build_snapshots.BLOCKS.items():
            page = ROOT / page_name
            self.assertIsNone(
                build_snapshots.splice(page, block_id, render()),
                f"{page_name} is out of date; run python3 scripts/build_snapshots.py",
            )

    def test_every_rendered_row_cites_an_official_document(self) -> None:
        slate_html = build_snapshots.render_slate()
        self.assertEqual(slate_html.count("<tr>"), 23)  # header + 22 games
        self.assertEqual(slate_html.count("NO PICK"), 22)
        self.assertEqual(slate_html.count(build_snapshots.SCHEDULE_URL), 22)

        injuries_html = build_snapshots.render_injuries()
        self.assertEqual(injuries_html.count(build_snapshots.REPORT_URL), 49)  # one per report row
        self.assertEqual(
            injuries_html.count(build_snapshots.SCHEDULE_URL),
            sum(
                1
                for game in load("injuries-2026-11-14-0430am.json")["games"]
                if game["cells_source"].startswith("schedule")
                for _ in game["rows"]
            ),
        )


if __name__ == "__main__":
    unittest.main()
