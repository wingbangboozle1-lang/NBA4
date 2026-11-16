"""Tests for the official-snapshot data files and their rendered tables.

The site's slate and injury tables are generated from ``data/snapshots/*.json``
by ``scripts/build_snapshots.py``. These tests keep the data honest (provenance,
no invented values) and keep the published pages in sync with the data. The
current snapshot is the 2026-11-15 refresh; the 2026-11-14 files are kept as
dated historical snapshots and stay covered by their own assertions.
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

# file name -> (expected game dates, expected row range)
SLATE_FILES = {
    "slate-2026-11-16.json": ({"2026-11-16", "2026-11-17", "2026-11-18"}, 245, 269),
    "slate-2026-11-15.json": ({"2026-11-15", "2026-11-16", "2026-11-17"}, 236, 257),
    "slate-2026-11-14.json": ({"2026-11-14", "2026-11-15", "2026-11-16"}, 231, 252),
}

SLATE_GAME_COUNTS = {
    "slate-2026-11-16.json": 25,
    "slate-2026-11-15.json": 22,
    "slate-2026-11-14.json": 22,
}

CURRENT_INJURY_FILE = "injuries-2026-11-16-0915am.json"
HISTORICAL_INJURY_FILE = "injuries-2026-11-14-0430am.json"

VALID_STATUSES = {"Out", "Available", "Probable", "Questionable", "Doubtful"}


def load(name: str) -> dict:
    return json.loads((SNAPSHOTS / name).read_text(encoding="utf-8"))


def injury_rows(name: str) -> list[dict]:
    return [row for game in load(name)["games"] for row in game["rows"]]


class SlateSnapshotTests(unittest.TestCase):
    def test_provenance_present(self) -> None:
        for name in SLATE_FILES:
            with self.subTest(slate=name):
                data = load(name)
                for key in REQUIRED_PROVENANCE:
                    self.assertTrue(data[key], key)
                self.assertTrue(data["source_url"].startswith("https://"))
                self.assertIn("SUBJECT TO CHANGE", data["source_document_header"])

    def test_every_game_is_complete_and_sourced(self) -> None:
        for name, (_, row_min, row_max) in SLATE_FILES.items():
            with self.subTest(slate=name):
                for game in load(name)["games"]:
                    self.assertTrue(game["date"].startswith("2026-11-"))
                    self.assertIn(game["away"], build_snapshots.ABBR)
                    self.assertIn(game["home"], build_snapshots.ABBR)
                    self.assertTrue(game["tip_et_col1"].endswith(" PM"))
                    self.assertTrue(game["tip_et_col2"].endswith(" PM"))
                    self.assertGreaterEqual(game["row"], row_min)
                    self.assertLessEqual(game["row"], row_max)

    def test_window_is_within_three_days(self) -> None:
        for name, (dates, _, _) in SLATE_FILES.items():
            with self.subTest(slate=name):
                self.assertEqual({game["date"] for game in load(name)["games"]}, dates)
                self.assertEqual(len(load(name)["games"]), SLATE_GAME_COUNTS[name])

    def test_no_model_output_is_stored(self) -> None:
        forbidden = ("line", "price", "probability", "pick", "edge")
        for name in SLATE_FILES:
            with self.subTest(slate=name):
                for game in load(name)["games"]:
                    for key in game:
                        self.assertNotIn(key, forbidden, f"model output stored for row {game['row']}")


class CurrentInjurySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(CURRENT_INJURY_FILE)
        cls.rows = injury_rows(CURRENT_INJURY_FILE)

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("09:15 AM", self.data["source_document_header"])
        self.assertIn("supersede", self.data["supersession_note"])
        self.assertTrue(self.data["newest_report_listed_at_check"]["rows_transcribed"])

    def test_every_row_has_a_status_or_reports_not_submitted(self) -> None:
        for row in self.rows:
            if row["status"]:
                self.assertIn(row["status"], VALID_STATUSES)
            elif row["reason"] == "NOT YET SUBMITTED":
                continue
            else:
                # The Golden State block prints one status-or-reason cell per row; a row
                # with a printed reason but no status cell is kept blank and flagged.
                self.assertTrue(row["reason"], "a blank status needs a printed reason or NYS")
                self.assertTrue(row.get("unverified"))
                self.assertIn("no status", row.get("flag", ""))

    def test_row_count_and_lost_team_cells_are_empty_and_flagged(self) -> None:
        # 72 = every row the 09:15 AM document prints (57 player rows + 15 NOT YET SUBMITTED).
        self.assertEqual(len(self.rows), 72)
        lost = [row for row in self.rows if row["team"] == "__lost__"]
        self.assertEqual(len(lost), 7)
        for row in lost:
            self.assertTrue(row["player"], "lost-team row must keep the player name")
            self.assertTrue(row["unverified"])
            self.assertTrue(row["flag"])

    def test_gsw_block_blank_cells_are_flagged(self) -> None:
        butler = [row for row in self.rows if row["player"] == "Butler III, Jimmy"]
        self.assertEqual(len(butler), 1)
        self.assertEqual(butler[0]["status"], "")
        self.assertEqual(butler[0]["reason"], "Injury/Illness - Right ACL Repair / Surgery")
        self.assertTrue(butler[0]["unverified"])
        self.assertIn("no status", butler[0]["flag"])
        blank_reason = [
            row for row in self.rows
            if row["team"] == "Golden State Warriors" and not row["reason"]
        ]
        self.assertEqual(
            sorted(r["player"] for r in blank_reason),
            ["Curry, Stephen", "Moody, Moses", "Porzingis, Kristaps", "Santos, Gui", "Williams, Brandon"],
        )
        for row in blank_reason:
            self.assertTrue(row["unverified"])
            self.assertIn("no reason", row["flag"])

    def test_game_cells_come_from_the_report_and_match_the_slate(self) -> None:
        slate = {game["row"]: game for game in load("slate-2026-11-16.json")["games"]}

        def clock(value: str) -> str:
            hour, minute = value.split(":")
            minute_digits = "".join(ch for ch in minute if ch.isdigit())
            return f"{int(hour)}:{minute_digits}"

        for game in self.data["games"]:
            # every game block cites either the report's own printed cells or the
            # schedule PDF repair (never an inferred value); both are recorded verbatim
            self.assertTrue(
                game["cells_source"].startswith("report") or "schedule" in game["cells_source"],
                game["matchup"],
            )
            row = game["schedule_row"]
            self.assertIn(row, slate)
            printed = f'{slate[row]["tip_et_col1"]} / {slate[row]["tip_et_col2"]}'
            self.assertIn(game["tip_et_from_schedule"], printed)
            if not game["tip_et_from_report"]:
                # the block's time cell was lost at a page break; nothing is invented
                continue
            if slate[row]["tip_disagreement"]:
                # AN-02: report and games page agree with each other and disagree with
                # the schedule PDF. Both printed values are stored and dual-cited.
                self.assertEqual(
                    clock(game["tip_et_from_report"].replace(" (ET)", "")),
                    clock(slate[row]["games_page_tip_et"].replace(" ET", "")),
                    game["matchup"],
                )
                continue
            # The report's Game Time has no meridiem; the schedule's ET column is the
            # independent document the meridiem is inferred from. Clock values must agree.
            self.assertEqual(
                clock(game["tip_et_from_report"].replace(" (ET)", "")),
                clock(slate[row]["tip_et_col2"]),
                game["matchup"],
            )

    def test_no_derived_or_model_values(self) -> None:
        for row in self.rows:
            for key in row:
                self.assertNotIn(key, ("probability", "minutes", "impact", "pick"), key)


class HistoricalInjurySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(HISTORICAL_INJURY_FILE)
        cls.rows = injury_rows(HISTORICAL_INJURY_FILE)

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("04:30 AM", self.data["source_document_header"])
        self.assertIn("supersedes", self.data["supersession_note"])

    def test_lost_cells_are_empty_and_flagged(self) -> None:
        self.assertEqual(len(self.rows), 49)
        lost = [row for row in self.rows if row["team"] == "__lost__"]
        self.assertEqual(len(lost), 1)
        self.assertEqual(lost[0]["player"], "Traore, Nolan")
        self.assertTrue(lost[0]["unverified"])
        self.assertTrue(lost[0]["flag"])

    def test_schedule_repaired_times_match_the_slate_snapshot(self) -> None:
        slate = {game["row"]: game for game in load("slate-2026-11-14.json")["games"]}
        for game in self.data["games"]:
            row = game["schedule_row"]
            if row not in slate:
                continue
            printed = f'{slate[row]["tip_et_col1"]} / {slate[row]["tip_et_col2"]}'
            self.assertIn(game["tip_et_from_schedule"], printed)


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
        self.assertEqual(slate_html.count("<tr>"), 26)  # header + 25 games
        self.assertEqual(slate_html.count("NO PICK"), 25)
        self.assertEqual(slate_html.count(build_snapshots.SCHEDULE_URL), 25)

        injuries_html = build_snapshots.render_injuries()
        self.assertEqual(injuries_html.count(build_snapshots.REPORT_URL), 72)  # one per report row
        self.assertEqual(
            injuries_html.count(build_snapshots.SCHEDULE_URL),
            sum(
                1
                for game in load(CURRENT_INJURY_FILE)["games"]
                if "schedule" in game["cells_source"]
                for _ in game["rows"]
            ),
        )


class AwayHomeBasisTests(unittest.TestCase):
    """The slate page shows "at" where an official document prints the order: either the
    schedule row itself prints an explicit "at" cell (rows 260+), or the newest injury
    report prints the same AWAY@HOME code for the same game date. Code-only matching is
    not enough: POR@MIN appears in the 11/16 report as a 11/16 game and again as a 11/17
    NOT YET SUBMITTED row, which would falsely corroborate the wrong slate row."""

    def test_report_corroborated_rows_are_exactly_245_to_257(self) -> None:
        report_codes = {
            (g.get("game_date") or g.get("game_date_from_schedule", ""), g["matchup"])
            for g in load(CURRENT_INJURY_FILE)["games"]
        }
        corroborated = set()
        for game in load("slate-2026-11-16.json")["games"]:
            if (game["date"], f"{build_snapshots.ABBR[game['away']]}@{build_snapshots.ABBR[game['home']]}") in report_codes:
                corroborated.add(game["row"])
        self.assertEqual(corroborated, set(range(245, 258)))

    def test_rows_260_to_269_print_an_explicit_at_cell(self) -> None:
        for game in load("slate-2026-11-16.json")["games"]:
            if game["row"] >= 260:
                self.assertEqual(game["matchup_cell_layout"], "away_cell|at_cell|home_cell")
            else:
                self.assertEqual(game["matchup_cell_layout"], "away_cell|home_cell")

    def test_rendered_slate_marks_uncorroborated_order(self) -> None:
        html = build_snapshots.render_slate()
        # 13 report-corroborated rows + 10 rows whose PDF cells print "at"
        self.assertEqual(html.count("</strong> at <strong>"), 23)
        self.assertEqual(html.count("(order unverified)"), 2)
        self.assertEqual(html.count('prints no "at"'), 2)


class GameLogTests(unittest.TestCase):
    """Task BI: per-player game logs are dated attributed observations with
    row-level official links, never inferred values and never betting inputs."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_gamelogs", ROOT / "scripts" / "build_gamelogs.py"
        )
        cls.build_gamelogs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.build_gamelogs)
        cls.data = json.loads(
            (SNAPSHOTS / cls.build_gamelogs.GAMELOGS).read_text(encoding="utf-8")
        )

    def test_every_report_player_is_covered_exactly_once(self) -> None:
        injury_rows = {
            (game["matchup"], row["player"])
            for game in load(CURRENT_INJURY_FILE)["games"]
            for row in game["rows"]
            if row["player"]
        }
        covered = [(p["report_block"], p["report_name"]) for p in self.data["players"]]
        self.assertEqual(len(covered), len(set(covered)))
        self.assertEqual(set(covered), injury_rows)

    def test_mirrored_report_cells_match_the_file_of_record(self) -> None:
        # raises SystemExit on any disagreement
        self.assertIsNone(
            self.build_gamelogs.verify_against_injury_report(self.data)
        )

    def test_every_game_row_carries_a_source_and_printed_values(self) -> None:
        for p in self.data["players"]:
            for g in p["games"]:
                self.assertTrue(g["source_url"].startswith("https://"), g["source_url"])
                self.assertIn("gamebook", g["source_label"])
                if g["designation"] == "played":
                    for key in ("min_printed", "pts_printed", "reb_printed", "ast_printed", "line_printed"):
                        self.assertTrue(g[key], f"{p['report_name']}: {key} must be the printed cell")
                else:
                    self.assertTrue(g["designation_printed"], p["report_name"])
                    for key in ("min_printed", "pts_printed", "reb_printed", "ast_printed"):
                        self.assertIsNone(g[key], f"{p['report_name']}: no stat line may be invented")

    def test_gap_players_have_no_invented_games(self) -> None:
        gaps = [p for p in self.data["players"] if p.get("gap")]
        self.assertEqual(len(gaps), 14)  # ORL + GSW + POR, idle both window days
        for p in gaps:
            self.assertEqual(p["games"], [])

    def test_no_model_output_is_stored(self) -> None:
        forbidden = ("probability", "minutes_model", "impact", "pick", "projection")
        for p in self.data["players"]:
            for key in p:
                self.assertNotIn(key, forbidden, key)

    def test_rendered_block_is_in_sync(self) -> None:
        page = ROOT / "results.html"
        self.assertIsNone(
            build_snapshots.splice(page, "player-gamelogs", self.build_gamelogs.render_gamelogs()),
            "results.html is out of date; run python3 scripts/build_gamelogs.py",
        )


if __name__ == "__main__":
    unittest.main()
