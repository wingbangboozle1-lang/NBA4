"""Tests for the official-snapshot data files and their rendered tables.

The site's slate and injury tables are generated from ``data/snapshots/*.json``
by ``scripts/build_snapshots.py``. These tests keep the data honest (provenance,
no invented values) and keep the published pages in sync with the data. The
current snapshots are the 2026-11-16 refresh (injury revisions 09:00 and 09:15 AM
ET, the 11/16-11/18 slate, the 11/15 result feed and the 11/16 standings); the
2026-11-15 and 2026-11-14 files are kept as dated historical snapshots and stay
covered by their own assertions.
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
# file name -> (expected game dates, expected row range, expected game count)
SLATE_FILES = {
    "slate-2026-11-16.json": ({"2026-11-16", "2026-11-17", "2026-11-18"}, 245, 269, 25),
    "slate-2026-11-15.json": ({"2026-11-15", "2026-11-16", "2026-11-17"}, 236, 257, 22),
    "slate-2026-11-14.json": ({"2026-11-14", "2026-11-15", "2026-11-16"}, 231, 252, 22),
}
# Slate files that carry the corroboration fields the later extraction added.
CORROBORATED_SLATE = "slate-2026-11-16.json"

CURRENT_SLATE_FILE = "slate-2026-11-16.json"
CURRENT_INJURY_FILE = "injuries-2026-11-16-0915am.cells.json"
PREVIOUS_INJURY_FILE = "injuries-2026-11-16-0900am.cells.json"
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
        for name, (_, row_min, row_max, _) in SLATE_FILES.items():
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
        for name, (dates, _, _, expected) in SLATE_FILES.items():
            with self.subTest(slate=name):
                self.assertEqual({game["date"] for game in load(name)["games"]}, dates)
                self.assertEqual(len(load(name)["games"]), expected)

    def test_no_model_output_is_stored(self) -> None:
        forbidden = ("line", "price", "probability", "pick", "edge")
        for name in SLATE_FILES:
            with self.subTest(slate=name):
                for game in load(name)["games"]:
                    for key in game:
                        self.assertNotIn(key, forbidden, f"model output stored for row {game['row']}")


class CurrentInjurySnapshotTests(unittest.TestCase):
    """The 2026-11-16 09:15 AM ET revision, checked cell by cell against the document."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(CURRENT_INJURY_FILE)
        cls.rows = injury_rows(CURRENT_INJURY_FILE)
        cls.previous = load(PREVIOUS_INJURY_FILE)

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("09:15 AM", self.data["source_document_header"])
        self.assertTrue(self.data["source_index_url"].startswith("https://"))
        self.assertEqual(self.data["revision_et_label"], "11/16/26 09:15 AM")

    def test_row_count_matches_the_document(self) -> None:
        # 72 = every printed row of the 09:15 AM document, including the 15
        # NOT YET SUBMITTED markers, which are printed rows, not absences.
        self.assertEqual(len(self.rows), 72)
        self.assertEqual(self.data["row_count"], 72)

    def test_status_cells_are_league_words_or_blank(self) -> None:
        for row in self.rows:
            if row["status"]:
                self.assertIn(row["status"], VALID_STATUSES)
                self.assertNotIn("NOT YET SUBMITTED", row["player"])

    def test_the_two_shapes_of_not_yet_submitted_are_both_published(self) -> None:
        # The document prints the marker as a reason cell for the slow teams and as
        # a player cell (blank status and reason) for the late 11/17 blocks.
        in_reason = [r for r in self.rows if r["reason"] == "NOT YET SUBMITTED"]
        in_player = [r for r in self.rows if r["player"] == "NOT YET SUBMITTED"]
        self.assertEqual(len(in_reason), 7)
        self.assertEqual(len(in_player), 8)
        self.assertEqual(len(in_reason) + len(in_player), 15)
        for row in in_player:
            self.assertEqual(row["status"], "")
            self.assertEqual(row["reason"], "")

    def test_page_break_rows_are_empty_and_flagged_never_reattributed(self) -> None:
        lost = [r for r in self.rows if not r["team"]]
        self.assertEqual(len(lost), 7)
        for row in lost:
            self.assertTrue(row["player"], "a page-break row must keep its player cell")
            self.assertTrue(row["unverified"])
            self.assertTrue(row["flag"])

    def test_known_players_are_verbatim_from_the_document(self) -> None:
        # Spot values read straight off the 09:15 AM text; a transcription change fails here.
        expected = {
            ("Chicago Bulls", "Smith, Jalen"): ("Questionable", "Injury/Illness - Left Finger Sprain"),
            ("Cleveland Cavaliers", "Mobley, Evan"): ("Out", "Injury/Illness - Left Great Toe Sprain"),
            ("Miami Heat", "Thompson, Klay"): ("Available", "Injury/Illness - Left Ankle Sprain"),
            ("New Orleans Pelicans", "Mathurin, Bennedict"): ("Out", "Injury/Illness - Left Plantar Fasciitis"),
            ("Minnesota Timberwolves", "Beringer, Joan"): ("Available", "Injury/Illness - Face Mask"),
            ("Denver Nuggets", "Strawther, Julian"): ("Out", "Injury/Illness - Left Knee Sprain"),
        }
        by_key = {(r["team"], r["player"]): r for r in self.rows}
        for key, (status, reason) in expected.items():
            with self.subTest(player=key[1]):
                self.assertIn(key, by_key)
                self.assertEqual(by_key[key]["status"], status)
                self.assertEqual(by_key[key]["reason"], reason)

    def test_reasons_that_the_document_leaves_blank_stay_blank(self) -> None:
        # Curry, Moody, Porzingis, Santos and Williams print an Out/Questionable
        # status with no reason cell. A filled-in reason would be an invention.
        blanks = [
            r for r in self.rows
            if r["team"] == "Golden State Warriors" and r["status"] and not r["reason"]
        ]
        self.assertEqual(len(blanks), 5)
        for row in blanks:
            self.assertEqual(row["reason"], "")

    def test_no_derived_or_model_values(self) -> None:
        for row in self.rows:
            for key in row:
                self.assertNotIn(key, ("probability", "minutes", "impact", "pick"), key)

    def test_the_two_revisions_have_equal_row_counts(self) -> None:
        self.assertEqual(len(self.rows), len(injury_rows(PREVIOUS_INJURY_FILE)))
        self.assertEqual(self.previous["row_count"], 72)


class StatusChangeDiffTests(unittest.TestCase):
    """The 09:00 -> 09:15 AM diff: no status changed inside fifteen minutes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("injuries-2026-11-16-0900-to-0915.diff.json")

    def test_counts_are_published_and_consistent(self) -> None:
        counts = self.data["counts"]
        self.assertEqual(counts["old_rows"], 72)
        self.assertEqual(counts["new_rows"], 72)
        self.assertEqual(counts["status_changes"], 0)
        self.assertEqual(counts["reason_changes"], 0)
        self.assertEqual(counts["printing_variances"], 1)

    def test_the_one_variance_is_a_name_cell_only(self) -> None:
        changes = self.data["changes"]
        self.assertEqual(len(changes), 1)
        change = changes[0]
        self.assertEqual(change["kind"], "PRINTING_VARIANCE")
        self.assertEqual(change["old"], "Mathurin, Benedict")
        self.assertEqual(change["new"], "Mathurin, Bennedict")
        self.assertIn("not a status change", change["note"])
        self.assertEqual(change["team"], "New Orleans Pelicans")


class ResultFeedAndStandingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = load("results-2026-11-15.json")
        cls.standings = load("standings-2026-11-16.json")
        cls.aggregates = load("aggregates-2026-11-16.json")

    def test_every_team_line_adds_up_including_overtime(self) -> None:
        # Row layout: [id, date, tip, arena, city, away, home, away_q, away_final,
        # home_q, home_final, winner, loser, url, ot_away, ot_home]. An overtime score
        # is carried BOTH as the fifth period of the quarter list and in the trailing
        # ot cells (NYK@TOR, 0022600241); it is counted once, never twice.
        self.assertEqual(len(self.results["rows"]), 9)
        for row in self.results["rows"]:
            away_q, away_final, home_q, home_final = row[7], row[8], row[9], row[10]
            for team, periods, final in (("away", away_q, away_final), ("home", home_q, home_final)):
                total = sum(periods)
                if total != final:
                    total = sum(periods[:4]) + row[14 if team == "away" else 15]
                self.assertEqual(total, final, f"{row[0]} {team}")

    def test_one_game_went_to_overtime_and_both_sides_carry_it(self) -> None:
        ot = [
            row[0]
            for row in self.results["rows"]
            if len(row) > 15 and row[14] is not None and row[15] is not None
        ]
        self.assertEqual(ot, ["0022600241"])
        game = next(r for r in self.results["rows"] if r[0] == "0022600241")
        self.assertEqual(len(game[7]), 5)  # four quarters plus the overtime period
        self.assertEqual(len(game[9]), 5)

    def test_standings_splits_reconcile(self) -> None:
        self.assertEqual(len(self.standings["rows"]), 30)
        for row in self.standings["rows"]:
            self.assertEqual(row["w"] + row["l"], row["games_played_from_w_plus_l"])
            self.assertTrue(row["split_sum_equals_gp"], row["team"])
        sc = self.aggregates["standings_consistency"]
        self.assertTrue(sc["wins_equal_losses"])
        self.assertEqual(sc["league_wins"] + sc["league_losses"], 394)

    def test_measured_home_rate_is_arithmetic_on_the_printed_splits(self) -> None:
        hc = self.aggregates["home_court"]
        self.assertEqual(hc["home_wins"] + hc["home_losses"], hc["home_games"])
        self.assertAlmostEqual(
            hc["measured_home_win_rate"], round(hc["home_wins"] / hc["home_games"], 4), places=4
        )

    def test_team_stat_rows_are_stored_with_provenance_only(self) -> None:
        stats = load("team-stats-2026-11-16.json")
        self.assertEqual(len(stats["rows"]), 30)
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(stats[key], key)
        self.assertFalse(stats["model_input_recut"]["applied"])


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

    def test_availability_and_rest_tables_are_source_linked(self) -> None:
        availability = build_snapshots.render_availability()
        self.assertEqual(availability.count(build_snapshots.REPORT_URL), availability.count("<tr>") - 1)
        rest = build_snapshots.render_rest()
        # 50 team-entries across the 25 games of the window.
        self.assertEqual(rest.count("<tr>"), 51)
        self.assertEqual(rest.count(build_snapshots.SCHEDULE_URL), 50)

    def test_ledger_and_status_tables_carry_no_published_pick(self) -> None:
        ledger = build_snapshots.render_ledger()
        self.assertIn("[EMPTY]", ledger)
        self.assertNotIn("SETTLED", ledger)
        status = build_snapshots.render_status_changes()
        self.assertIn("cannot be measured", status)


class AwayHomeBasisTests(unittest.TestCase):
    """The slate page shows "at" only where an official document prints the same matchup
    code or games-page slug for the same game date. Printed order alone is not enough."""

    def test_every_row_carries_a_games_page_slug_or_a_flagged_gap(self) -> None:
        games = load(CURRENT_SLATE_FILE)["games"]
        self.assertEqual(len(games), 25)
        for game in games:
            self.assertTrue(
                game.get("games_page_slug") or game.get("order_corroborated_by"),
                f"row {game['row']} has no corroborating source for away/home",
            )

    def test_tip_disagreements_are_published_not_resolved(self) -> None:
        basis = load(CURRENT_SLATE_FILE)["basis"]
        self.assertEqual(basis["rows_with_tip_disagreement"], [256, 257, 266, 267])
        for game in load(CURRENT_SLATE_FILE)["games"]:
            if game["row"] in (256, 257, 266, 267):
                self.assertTrue(game["tip_disagreement"], game["row"])
                # both printed values survive; neither is corrected
                self.assertIn("games page", game["tip_disagreement"])
                self.assertTrue(game["tip_et_col1"] and game["tip_et_col2"])

    def test_rendered_slate_marks_every_game_with_its_sources(self) -> None:
        html = build_snapshots.render_slate()
        self.assertEqual(html.count("</strong> at <strong>"), 25)
        self.assertEqual(html.count(build_snapshots.REPORT_URL), 13)  # rows the report corroborates


if __name__ == "__main__":
    unittest.main()
