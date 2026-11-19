"""Tests for the official-snapshot data files and their rendered tables.

The site's slate and injury tables are generated from ``data/snapshots/*.json``
by ``scripts/build_snapshots.py``. These tests keep the data honest (provenance,
no invented values) and keep the published pages in sync with the data. The
current snapshot is the 2026-11-19 refresh (injury file of record
``injuries-2026-11-19-0145am.json``); the 2026-11-17, 2026-11-16, 2026-11-15 and
2026-11-14 files are kept as dated historical snapshots and stay covered by
their own assertions.
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

# file name -> (expected game dates, expected row range, expected game count)
SLATE_FILES = {
    "slate-2026-11-17.json": ({"2026-11-17", "2026-11-18", "2026-11-19"}, 253, 273, 21),
    "slate-2026-11-16.json": ({"2026-11-16", "2026-11-17", "2026-11-18"}, 245, 269, 25),
    "slate-2026-11-15.json": ({"2026-11-15", "2026-11-16", "2026-11-17"}, 236, 257, 22),
    "slate-2026-11-14.json": ({"2026-11-14", "2026-11-15", "2026-11-16"}, 231, 252, 22),
}

CURRENT_INJURY_FILE = "injuries-2026-11-19-0145am.json"
INJURY_20261117_FILE = "injuries-2026-11-17-1030am.json"
INJURY_20261116_FILE = "injuries-2026-11-16-1000am.json"
PREVIOUS_INJURY_FILE = "injuries-2026-11-15-0615am.json"
HISTORICAL_INJURY_FILE = "injuries-2026-11-14-0430am.json"
CURRENT_SLATE_FILE = "slate-2026-11-17.json"
GAMELOGS = "player-gamelogs-2026-11-15_to_2026-11-16.json"

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
        for name, (dates, _, _, count) in SLATE_FILES.items():
            with self.subTest(slate=name):
                self.assertEqual({game["date"] for game in load(name)["games"]}, dates)
                self.assertEqual(len(load(name)["games"]), count)

    def test_slate_is_rows_253_to_273_in_three_dates(self) -> None:
        # folded from the parallel BM session (arena/4326c586-nba4, PR #70)
        games = load(CURRENT_SLATE_FILE)["games"]
        self.assertEqual([g["row"] for g in games], list(range(253, 274)))
        self.assertEqual({g["date"] for g in games}, {"2026-11-17", "2026-11-18", "2026-11-19"})

    def test_every_slate_row_matches_its_verbatim_raw_line(self) -> None:
        # folded from the parallel BM session: the published games must equal the
        # verbatim raw schedule transcription cell for cell (tip column depends on
        # whether the printed row carries an "at" token)
        raw = (ROOT / "data/snapshots/raw/schedule-2026-11-17-window-rows-253-273.txt").read_text(encoding="utf-8")
        by_row = {}
        for line in raw.splitlines():
            if line and not line.startswith("#"):
                by_row[int(line.split("|", 1)[0])] = line
        for g in load(CURRENT_SLATE_FILE)["games"]:
            cells = by_row[g["row"]].split("|")
            self.assertEqual(g["tip_et_col1"], cells[5] if cells[4] != "at" else cells[6], g["row"])

    def test_no_model_output_is_stored(self) -> None:
        forbidden = ("line", "price", "probability", "pick", "edge")
        for name in SLATE_FILES:
            with self.subTest(slate=name):
                for game in load(name)["games"]:
                    for key in game:
                        self.assertNotIn(key, forbidden, f"model output stored for row {game['row']}")

    def test_current_slate_games_page_ids_and_tip_agreement(self) -> None:
        data = load(CURRENT_SLATE_FILE)
        disagreeing = set(data["games_page_corroboration"]["tip_disagreements_kept_as_printed"])
        self.assertEqual(disagreeing, {256, 257, 266, 267})
        matches = 0
        for game in data["games"]:
            # verified live on the games pages: row 253 -> 0022600253, row 273 -> 0022600273
            self.assertEqual(
                game["games_page_game_id"], "00226002" + str(game["row"] - 200), game["row"]
            )
            self.assertTrue(game["games_page_url"].startswith("https://www.nba.com/game/"))
            if game["tip_disagreement"]:
                self.assertIn(game["row"], disagreeing)
                # both printed values are kept: the games-page value and the schedule value
                self.assertIn(game["games_page_tip_et"].replace(" ET", ""), game["tip_disagreement"])
                self.assertIn(game["tip_et_col2"], game["tip_disagreement"])
            else:
                self.assertNotIn(game["row"], disagreeing)
                self.assertEqual(game["games_page_tip_et"], game["tip_et_col2"] + " ET")
                matches += 1
        self.assertEqual(matches, data["games_page_corroboration"]["rows_where_tip_matches_games_page"])
        self.assertEqual(matches, 17)


class InjurySnapshot20261117Tests(unittest.TestCase):
    """The 2026-11-17 10:30 AM snapshot is historical after the 2026-11-19 refresh;
    its own assertions stay."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(INJURY_20261117_FILE)
        cls.rows = injury_rows(INJURY_20261117_FILE)

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("10:30 AM", self.data["source_document_header"])
        self.assertIn("supersede", self.data["supersession_note"])
        self.assertTrue(self.data["newest_report_listed_at_check"]["rows_transcribed"])

    def test_every_row_has_a_status_or_reports_not_submitted(self) -> None:
        for row in self.rows:
            if row["status"]:
                self.assertIn(row["status"], VALID_STATUSES)
            else:
                # blank status is allowed only for NOT YET SUBMITTED rows or for rows
                # whose status cell was lost at a page break (flagged, never filled in)
                if row["reason"] != "NOT YET SUBMITTED":
                    self.assertTrue(row["unverified"], row)
                    self.assertTrue(row["flag"], row)

    def test_row_count_and_lost_team_cells_are_empty_and_flagged(self) -> None:
        # 60 = every row the 10:30 AM document prints (2026-11-17 refresh).
        self.assertEqual(len(self.rows), 60)
        lost = [row for row in self.rows if row["team"] == "__lost__"]
        self.assertEqual(len(lost), 2)  # the 'Soreness' fragment and the Reaves row
        for row in lost:
            self.assertTrue(row["player"], "lost-team row must keep the printed player cell")
            self.assertTrue(row["unverified"])
            self.assertTrue(row["flag"])

    def test_page_break_rows_are_recorded_as_extracted(self) -> None:
        # Minnesota row: the printed row lost its date/time/matchup cells; the team
        # cell is printed and must stay.
        minnesota = [row for row in self.rows if row["player"] == "" and row["team"] == "Minnesota Timberwolves"]
        self.assertEqual(len(minnesota), 1)
        self.assertEqual(minnesota[0]["status"], "")
        self.assertTrue(minnesota[0]["unverified"])
        self.assertIn("page break", minnesota[0]["flag"])
        # 'Soreness' fragment: the printed row carries only that word.
        fragment = [row for row in self.rows if row["player"] == "Soreness"]
        self.assertEqual(len(fragment), 1)
        self.assertEqual(fragment[0]["status"], "")
        self.assertEqual(fragment[0]["reason"], "")
        self.assertTrue(fragment[0]["unverified"])
        # Reaves row: player/status/reason printed, date/time/matchup/team lost.
        reaves = [row for row in self.rows if row["player"] == "Reaves, Austin"]
        self.assertEqual(len(reaves), 1)
        self.assertEqual(reaves[0]["status"], "Out")
        self.assertEqual(reaves[0]["reason"], "Injury/Illness - Left Heel Contusion / Bone Bruise")
        self.assertEqual(reaves[0]["team"], "__lost__")
        self.assertTrue(reaves[0]["unverified"])
        # The eight five-cell NOT YET SUBMITTED rows of the 11/18 block keep the
        # marker in the reason cell and no player/status is inferred.
        five_cell = [row for row in self.rows if row.get("flag", "").startswith("the printed row carries five cells")]
        self.assertEqual(len(five_cell), 8)
        for row in five_cell:
            self.assertEqual(row["reason"], "NOT YET SUBMITTED")
            self.assertEqual(row["player"], "")
            self.assertEqual(row["status"], "")

    def test_report_revision_is_the_1030_document(self) -> None:
        # folded from the parallel BM session (adapted: this file records the
        # revision in the printed header, not a separate revision label field)
        self.assertIn("10:30 AM", load(INJURY_20261117_FILE)["source_document_header"])
        self.assertEqual(
            self.data["source_url"],
            "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf",
        )

    def test_lost_team_rows_are_kept_not_unattributed(self) -> None:
        # folded from the parallel BM session (adapted to this extraction, which
        # keeps both printed page-break rows inside their blocks with a blank
        # lost team cell rather than a separate unattributed_rows list — the
        # printed 'Soreness' fragment would be unpublished otherwise)
        self.assertEqual(len(self.rows), 60)
        lost = [row for row in self.rows if row["team"] == "__lost__"]
        self.assertEqual([row["player"] for row in lost], ["Soreness", "Reaves, Austin"])
        for row in lost:
            self.assertTrue(row["unverified"])
            self.assertTrue(row["flag"])

    def test_block_position_rows_are_unverified(self) -> None:
        # folded from the parallel BM session (adapted): any row whose printed
        # matchup cell was lost, so the game attachment rests on block position
        # alone, must carry unverified
        for game in self.data["games"]:
            for row in game["rows"]:
                if row["team"] == "__lost__" or (
                    row["player"] == "" and row["reason"] != "NOT YET SUBMITTED"
                ):
                    self.assertTrue(row["unverified"], row)
        minnesota = [g for g in self.data["games"] if g["matchup"] == "POR@MIN"]
        self.assertEqual(len(minnesota), 1)

    def test_not_yet_submitted_rows_are_reporting_states(self) -> None:
        nys = [row for row in self.rows if row["reason"] == "NOT YET SUBMITTED"]
        # 24 future matchup rows on 11/18 + the POR@MIN reporting rows (Portland's
        # own row and the Minnesota fragment row that carries the marker)
        self.assertEqual(len(nys), 26)
        for row in nys:
            self.assertEqual(row["player"], "")
            self.assertEqual(row["status"], "")

    def test_nyk_tor_block_prints_raptors_rows_only(self) -> None:
        block = [g for g in self.data["games"] if g["matchup"] == "NYK@TOR"]
        self.assertEqual(len(block), 1)
        teams = {r["team"] for r in block[0]["rows"]}
        self.assertEqual(teams, {"Toronto Raptors"})

    def test_game_cells_come_from_the_report_and_match_the_slate(self) -> None:
        slate = {game["row"]: game for game in load(CURRENT_SLATE_FILE)["games"]}

        def clock(value: str) -> str:
            hour, minute = value.split(":")
            minute_digits = "".join(ch for ch in minute if ch.isdigit())
            return f"{int(hour)}:{minute_digits}"

        for game in self.data["games"]:
            self.assertTrue(game["cells_source"].startswith("report"), game["matchup"])
            row = game["schedule_row"]
            self.assertIn(row, slate)
            printed = f'{slate[row]["tip_et_col1"]} / {slate[row]["tip_et_col2"]}'
            self.assertIn(game["tip_et_from_schedule"], printed)
            if game.get("tip_disagreement"):
                # both clocks are printed by official documents; the report's own clock
                # must be the one named in the disagreement note, never overwritten
                self.assertIn(
                    game["tip_et_from_report"].replace(" (ET)", ""), game["tip_disagreement"]
                )
                self.assertIn(slate[row]["tip_et_col2"], game["tip_disagreement"])
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

    def test_cross_check_against_the_independent_extraction_is_complete(self) -> None:
        cells = load("injuries-2026-11-17-1030am.cells.json")
        check = cells["cross_check"]
        self.assertEqual(check["rows_in_this_extraction"], 60)
        self.assertEqual(check["rows_in_the_counterpart"], 60)
        self.assertEqual(check["rows_matching_row_for_row"], 60)
        self.assertEqual(check["only_in_this_extraction"], [])
        self.assertEqual(check["only_in_the_counterpart"], [])


class InjurySnapshot20261116Tests(unittest.TestCase):
    """The 2026-11-16 10:00 AM snapshot is historical; its own assertions stay."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(INJURY_20261116_FILE)
        cls.rows = injury_rows(INJURY_20261116_FILE)

    def test_provenance_and_row_count(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("10:00 AM", self.data["source_document_header"])
        self.assertEqual(len(self.rows), 72)

    def test_golden_state_column_loss_is_flagged_not_repaired(self) -> None:
        butler = [row for row in self.rows if row["player"] == "Butler III, Jimmy"]
        self.assertEqual(len(butler), 1)
        self.assertEqual(butler[0]["status"], "")
        self.assertEqual(butler[0]["reason"], "Injury/Illness - Right ACL Repair / Surgery")
        self.assertTrue(butler[0]["unverified"])
        for name in ("Curry, Stephen", "Moody, Moses", "Porzingis, Kristaps", "Santos, Gui", "Williams, Brandon"):
            rows = [row for row in self.rows if row["player"] == name]
            self.assertEqual(len(rows), 1, name)
            self.assertTrue(rows[0]["status"], name)
            self.assertEqual(rows[0]["reason"], "", name)
            self.assertTrue(rows[0]["unverified"], name)
            self.assertIn("reason cell not printed", rows[0]["flag"], name)

    def test_cross_check_against_the_independent_extraction_is_complete(self) -> None:
        cells = load("injuries-2026-11-16-1000am.cells.json")
        check = cells["cross_check"]
        self.assertEqual(check["rows_in_this_extraction"], 72)
        self.assertEqual(check["rows_in_the_counterpart"], 72)
        self.assertEqual(check["rows_matching_row_for_row"], 72)
        self.assertEqual(check["only_in_this_extraction"], [])
        self.assertEqual(check["only_in_the_counterpart"], [])


class PreviousInjurySnapshotTests(unittest.TestCase):
    """The 2026-11-15 06:15 AM snapshot is historical; its own assertions stay."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(PREVIOUS_INJURY_FILE)
        cls.rows = injury_rows(PREVIOUS_INJURY_FILE)

    def test_row_count_is_unchanged(self) -> None:
        self.assertEqual(len(self.rows), 101)
        self.assertIn("06:15 AM", self.data["source_document_header"])

    def test_sorber_reason_cell_is_a_verbatim_page_break_join(self) -> None:
        sorber = [row for row in self.rows if row["player"] == "Sorber, Thomas"]
        self.assertEqual(len(sorber), 1)
        self.assertEqual(sorber[0]["reason"], "Injury/Illness - Right Knee Surgery")
        self.assertTrue(sorber[0]["unverified"])
        self.assertIn("page boundary", sorber[0]["flag"])


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


class ResultsSnapshot20261116Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("results-2026-11-16.json")

    def test_provenance_and_shape(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertEqual(len(self.data["rows"]), 8)
        self.assertEqual(len(self.data["row_format"]), 16)

    def test_every_period_sum_equals_the_printed_final(self) -> None:
        checks = self.data["verification"]["quarter_sum_check"]
        self.assertEqual(len(checks), 16)
        for check in checks:
            periods = check[2:-2]
            final = check[-2]
            agrees = check[-1]
            self.assertTrue(agrees, check)
            self.assertEqual(sum(periods), final, check)

    def test_no_game_of_the_date_went_to_overtime(self) -> None:
        ot_rows = [row for row in self.data["rows"] if len(row[7]) > 4 or len(row[9]) > 4 or row[14] or row[15]]
        self.assertEqual(ot_rows, [])
        # all eight finals agree with the official games page for the date
        self.assertEqual(self.data["verification"]["finals_cross_check"]["games_whose_two_documents_agree_on_both_finals"], 8)
        # the Houston quarter line comes from the game summary page, recorded as an irregularity
        self.assertIn("game summary", self.data["verification"]["irregularity"])

    def test_houston_quarter_line_matches_the_summary_page_capture(self) -> None:
        row = [r for r in self.data["rows"] if r[0] == "0022600249"][0]
        self.assertEqual(row[5], "HOU")
        self.assertEqual(row[7], [15, 31, 35, 29])
        self.assertEqual(row[8], 110)
        self.assertEqual(row[9], [29, 33, 39, 27])
        self.assertEqual(row[10], 128)
        self.assertEqual(row[13], "https://www.nba.com/game/hou-vs-mia-0022600249")


class ResultsSnapshot20261115Tests(unittest.TestCase):
    """The 2026-11-15 results snapshot is historical; its own assertions stay."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("results-2026-11-15.json")

    def test_provenance_and_shape(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertEqual(len(self.data["rows"]), 9)
        self.assertEqual(len(self.data["row_format"]), 14)

    def test_every_period_sum_equals_the_printed_final(self) -> None:
        checks = self.data["verification"]["quarter_sum_check"]
        self.assertEqual(len(checks), 18)
        for check in checks:
            periods = check[2:-2]
            final = check[-2]
            agrees = check[-1]
            self.assertTrue(agrees, check)
            self.assertEqual(sum(periods), final, check)

    def test_overtime_game_carries_its_printed_ot_period(self) -> None:
        ot_rows = [row for row in self.data["rows"] if len(row[7]) > 4 or len(row[9]) > 4]
        self.assertEqual(len(ot_rows), 1)
        row = ot_rows[0]
        self.assertEqual(row[0], "0022600241")
        self.assertEqual(row[7], [23, 24, 20, 28, 17])
        self.assertEqual(row[9], [17, 26, 31, 21, 13])
        self.assertEqual(sum(row[7][:4]), 95)
        self.assertEqual(sum(row[7]), row[8])
        self.assertEqual(sum(row[9]), row[10])
        self.assertIn("0022600241", self.data["verification"]["overtime_games"])


class Aggregates20261117Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.agg = load("aggregates-2026-11-17.json")

    def test_home_court_rate_is_arithmetic_on_the_standings(self) -> None:
        hc = self.agg["home_court"]
        self.assertEqual((hc["home_wins"], hc["home_losses"]), (106, 98))
        self.assertEqual(hc["home_games"], 204)
        self.assertEqual(hc["measured_home_win_rate"], 0.5196)

    def test_pin_matches_the_engine_conversion(self) -> None:
        import sys as _sys

        _sys.path.insert(0, str(ROOT))
        from engine.homerate import pin_home_advantage

        standings = load("standings-2026-11-17.json")
        pin = pin_home_advantage(standings["rows"], source_url=standings["source_url"])
        self.assertEqual(self.agg["home_court"]["pin"]["home_advantage_points"], round(pin.points, 3))
        self.assertFalse(pin.authorized)

    def test_result_feed_is_settlement_eligible(self) -> None:
        rf = self.agg["result_feed"]
        self.assertEqual(rf["team_lines_checked"], 16)
        self.assertEqual(rf["lines_that_disagree"], 0)
        self.assertTrue(rf["settlement_eligible"])

    def test_standings_consistency_uses_the_neutral_column(self) -> None:
        sc = self.agg["standings_consistency"]
        self.assertEqual((sc["league_wins"], sc["league_losses"]), (205, 205))
        self.assertTrue(sc["wins_equal_losses"])
        self.assertEqual(sc["home_plus_road_plus_neutral"], 410)

    def test_consecutive_revision_diff_counts(self) -> None:
        diff = load("injuries-2026-11-17-1015-to-1030.diff.json")
        counts = diff["counts"]
        self.assertEqual(counts["old_rows"], 60)
        self.assertEqual(counts["new_rows"], 60)
        self.assertEqual(counts["status_changes"], 0)
        self.assertEqual(counts["reason_changes"], 0)
        self.assertEqual(counts["printing_variances"], 0)
        self.assertEqual(diff["old"]["revision_label"], "11/17/26 10:15 AM")
        self.assertEqual(diff["new"]["revision_label"], "11/17/26 10:30 AM")
        # the two same-morning revisions matched row for row: no observed change
        self.assertEqual(diff["changes"], [])
        self.assertIn("60 of 60", diff["alignment"])


class Aggregates20261116Tests(unittest.TestCase):
    """The 2026-11-16 aggregates are historical; their own assertions stay."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.agg = load("aggregates-2026-11-16.json")

    def test_home_court_rate_is_arithmetic_on_the_standings(self) -> None:
        hc = self.agg["home_court"]
        self.assertEqual((hc["home_wins"], hc["home_losses"]), (102, 94))
        self.assertEqual(hc["home_games"], 196)
        self.assertEqual(hc["measured_home_win_rate"], 0.5204)

    def test_pin_matches_the_engine_conversion(self) -> None:
        import sys as _sys

        _sys.path.insert(0, str(ROOT))
        from engine.homerate import pin_home_advantage

        standings = load("standings-2026-11-16.json")
        pin = pin_home_advantage(standings["rows"], source_url=standings["source_url"])
        self.assertEqual(self.agg["home_court"]["pin"]["home_advantage_points"], round(pin.points, 3))
        self.assertFalse(pin.authorized)

    def test_result_feed_is_settlement_eligible(self) -> None:
        rf = self.agg["result_feed"]
        self.assertEqual(rf["team_lines_checked"], 18)
        self.assertEqual(rf["lines_that_disagree"], 0)
        self.assertTrue(rf["settlement_eligible"])

    def test_consecutive_revision_diff_counts(self) -> None:
        diff = load("injuries-2026-11-16-0945-to-1000.diff.json")
        counts = diff["counts"]
        self.assertEqual(counts["old_rows"], 72)
        self.assertEqual(counts["new_rows"], 72)
        self.assertEqual(counts["status_changes"], 0)
        self.assertEqual(counts["reason_changes"], 0)
        self.assertEqual(counts["printing_variances"], 1)
        self.assertEqual(diff["old"]["revision_label"], "11/16/26 09:45 AM")
        self.assertEqual(diff["new"]["revision_label"], "11/16/26 10:00 AM")
        variance = [c for c in diff["changes"] if c["kind"] == "PRINTING_VARIANCE"]
        self.assertEqual(len(variance), 1)
        self.assertEqual(variance[0]["old"], "Mathurin, Bennedict")
        self.assertEqual(variance[0]["new"], "Mathurin, Benedict")


class RestWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rest = load("rest-window-2026-11-17.json")
        cls.slate = load(CURRENT_SLATE_FILE)

    def test_coverage_rule_is_declared(self) -> None:
        self.assertEqual(self.rest["coverage"]["first_date"], "2026-11-10")
        self.assertEqual(self.rest["coverage"]["last_date"], "2026-11-19")
        self.assertIn("uncovered", self.rest["coverage"]["rule"])

    def test_every_window_team_has_a_prior_game_inside_the_window(self) -> None:
        by_team: dict[str, set[str]] = {}
        for row in self.rest["rows"]:
            for team in (row["away"], row["home"]):
                by_team.setdefault(team, set()).add(row["date"])
        for game in self.slate["games"]:
            for team in (game["away"], game["home"]):
                priors = [d for d in by_team.get(team, ()) if d < game["date"]]
                self.assertTrue(priors, f"row {game['row']} {team} has no prior game in the rest window")
                # rest is whole days between the prior game date and the game date
                latest = max(priors)
                self.assertGreaterEqual(
                    (date_from(game["date"]) - date_from(latest)).days, 1, (team, game["date"])
                )

    def test_window_rows_carry_no_model_values(self) -> None:
        for row in self.rest["rows"]:
            for key in row:
                self.assertNotIn(key, ("rest", "b2b", "prob", "pick", "line"), key)


def date_from(value: str):
    from datetime import date

    y, m, d = value.split("-")
    return date(int(y), int(m), int(d))


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
        self.assertEqual(slate_html.count("<tr>"), 22)  # header + 21 games
        self.assertEqual(slate_html.count("NO PICK"), 21)
        self.assertEqual(slate_html.count(build_snapshots.SCHEDULE_URL), 21)

        injuries_html = build_snapshots.render_injuries()
        self.assertEqual(injuries_html.count(build_snapshots.REPORT_URL), 44)  # one per report row
        self.assertEqual(
            injuries_html.count(build_snapshots.SCHEDULE_URL),
            sum(
                1
                for game in load(CURRENT_INJURY_FILE)["games"]
                if game["cells_source"].startswith("schedule") or game["cells_source"] == "report-context"
                for _ in game["rows"]
            ),
        )


class TeamStatsSnapshotTests(unittest.TestCase):
    """Mirror of scripts/check_site.py audit_team_stats for the current file
    (the checker still pins the 2026-11-16 file; the repoint request is logged)."""

    def test_thirty_unique_team_rows_without_rank_columns(self) -> None:
        data = load("team-stats-2026-11-17.json")
        for section in ("advanced_rows", "opponent_rows"):
            rows = data.get(section, [])
            teams = [r.get("team") for r in rows]
            self.assertEqual(len(rows), 30, section)
            self.assertEqual(len(set(teams)), 30, section)
            for r in rows:
                rank_keys = [k for k in r if k.lower().startswith("rank")]
                self.assertEqual(rank_keys, [], f"{section} {r.get('team')}")

    def test_gp_w_l_agree_between_pages_and_with_standings(self) -> None:
        data = load("team-stats-2026-11-17.json")
        standings = {r["team"]: (r["w"] + r["l"], r["w"], r["l"]) for r in load("standings-2026-11-17.json")["rows"]}
        adv = {r["team"]: (r["gp"], r["w"], r["l"]) for r in data["advanced_rows"]}
        opp = {r["team"]: (r["gp"], r["w"], r["l"]) for r in data["opponent_rows"]}
        for team in sorted(set(adv) | set(opp)):
            self.assertEqual(adv.get(team), opp.get(team), team)
            self.assertEqual(adv.get(team), standings.get(team), team)


class AwayHomeBasisTests(unittest.TestCase):
    """The slate page shows "at" only where an official document confirms the order:
    the current injury report's own matchup code for the same game date, or the
    schedule's printed "at" token. Code-only matching is not enough: POR@MIN appears
    as an 11/17 report block and again as the 11/18 slate row 264.

    After the 2026-11-19 refresh the file of record covers the 11/19 slate only, so
    the 11/17-11/18 rows are corroborated by the schedule's printed "at" token where
    it exists (rows 260-269) and fall back to flagged printed order otherwise
    (rows 253-259) - never to an inferred order."""

    def test_report_code_corroborated_rows_are_exactly_the_1119_slate(self) -> None:
        # The file of record covers 11/19 and 11/20 game blocks. Only the 11/19
        # blocks carry the schedule rows in the 3-day window; the 11/20 blocks
        # are the next slate and are outside slate-2026-11-17.json (rows 253-273),
        # so they corroborate no current slate row.
        report_codes = {
            (g.get("game_date") or g.get("game_date_from_schedule", ""), g["matchup"])
            for g in load(CURRENT_INJURY_FILE)["games"]
            if g.get("schedule_row") is not None
        }
        corroborated = set()
        for game in load(CURRENT_SLATE_FILE)["games"]:
            if (game["date"], f"{build_snapshots.ABBR[game['away']]}@{build_snapshots.ABBR[game['home']]}") in report_codes:
                corroborated.add(game["row"])
        self.assertEqual(corroborated, {270, 271, 272, 273})

    def test_window_rows_are_corroborated_by_report_code_or_at_token(self) -> None:
        html = build_snapshots.render_slate()
        # 4 report-code rows (11/19) + 10 rows with the schedule's "at" token
        # (11/18 rows 260-269) show "at"; the 7 rows 253-259 print no "at" token and
        # no current-report code, so they show flagged printed order, never an
        # inferred order
        self.assertEqual(html.count("</strong> at <strong>"), 14)
        self.assertEqual(html.count("(order unverified)"), 7)
        self.assertEqual(html.count('prints no "at"'), 7)

    def test_at_token_rows_are_not_flagged(self) -> None:
        data = load(CURRENT_SLATE_FILE)
        at_rows = {g["row"] for g in data["games"] if g.get("at_token_printed")}
        self.assertEqual(at_rows, set(range(260, 274)))


class GameLogTests(unittest.TestCase):
    """Task BI (arena/dab321e7-nba4): per-player game logs are dated attributed
    observations with row-level official links, never inferred values and never
    betting inputs. Merged into this suite at the third parallel collision."""

    GAMELOGS = "player-gamelogs-2026-11-15_to_2026-11-16.json"
    INJURY_1116 = "injuries-2026-11-17-1030am.json"

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_gamelogs", ROOT / "scripts" / "build_gamelogs.py"
        )
        cls.build_gamelogs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.build_gamelogs)
        cls.data = json.loads((SNAPSHOTS / cls.GAMELOGS).read_text(encoding="utf-8"))

    def test_every_report_player_is_covered_exactly_once(self) -> None:
        injury_rows = {
            (game["matchup"], row["player"])
            for game in load(self.INJURY_1116)["games"]
            for row in game["rows"]
            if row["player"]
        }
        covered = [(p["report_block"], p["report_name"]) for p in self.data["players"]]
        self.assertEqual(len(covered), len(set(covered)))
        self.assertEqual(set(covered), injury_rows)

    def test_mirrored_report_cells_match_the_file_of_record(self) -> None:
        self.assertIsNone(self.build_gamelogs.verify_against_injury_report(self.data))

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
        self.assertEqual(len(gaps), 8)  # Detroit idle both window days + the 'Soreness' fragment
        for p in gaps:
            self.assertEqual(p["games"], [])
        fragment = [p for p in gaps if p["report_name"] == "Soreness"]
        self.assertEqual(len(fragment), 1)
        self.assertIn("not a player row", fragment[0]["gap"])

    def test_kessler_row_is_a_dated_observation_pair(self) -> None:
        kessler = [p for p in self.data["players"] if p["report_name"] == "Kessler, Walker"][0]
        self.assertEqual(kessler["report_status"], "Out")
        self.assertEqual(kessler["games"][0]["designation"], "played")
        self.assertEqual(kessler["games"][0]["min_printed"], "32:26")

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


class CurrentInjurySnapshot20261119Tests(unittest.TestCase):
    """Task CA (session arena/edfbc063-nba4): the 2026-11-19 1:45 AM ET revision is
    the injury file of record after the 2026-11-19 refresh."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(CURRENT_INJURY_FILE)
        cls.rows = injury_rows(CURRENT_INJURY_FILE)

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("01:45 AM", self.data["source_document_header"])
        self.assertIn("supersede", self.data["supersession_note"])
        self.assertTrue(self.data["newest_report_listed_at_check"]["rows_transcribed"])

    def test_file_of_record_matches_the_build_constants(self) -> None:
        self.assertEqual(self.data["source_url"], build_snapshots.REPORT_URL)
        self.assertEqual(build_snapshots.REPORT_URL,
                         "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf")
        self.assertEqual(build_snapshots.INJ_NEW, "injuries-2026-11-19-0145am.cells.json")
        self.assertEqual(build_snapshots.INJ_DIFF, "injuries-2026-11-19-0130am-to-0145am.diff.json")

    def test_row_count_and_game_blocks(self) -> None:
        # 44 = every row the 1:45 AM document prints: the 11/19 slate (23 player
        # rows + GSW/MEM/MIL NOT YET SUBMITTED team rows) plus the 11/20 next-slate
        # NOT YET SUBMITTED blocks. Mirrors the 11/17 file of record, which keeps
        # every block the report prints. 13 game blocks total.
        self.assertEqual(len(self.rows), 44)
        self.assertEqual(self.data["row_count"], 44)
        self.assertEqual(self.data["games_counted"], 13)
        self.assertEqual(self.data["player_rows_counted"], 23)
        # The 11/19 slate (the four blocks the 3-day window covers) and the
        # 11/20 next-slate blocks.
        self.assertEqual(
            {g["matchup"] for g in self.data["games"] if g["schedule_row"] is not None},
            {"GSW@MEM", "LAC@SAS", "NYK@MIN", "POR@MIL"},
        )
        self.assertEqual(
            {g["matchup"] for g in self.data["games"] if g["schedule_row"] is None},
            {"CHA@ATL", "IND@CLE", "ORL@BKN", "TOR@DET", "NOP@OKC", "WAS@CHI",
             "PHX@UTA", "HOU@DEN", "SAC@LAL"},
        )

    def test_schedule_rows_are_270_to_273(self) -> None:
        sched = {g["matchup"]: g["schedule_row"] for g in self.data["games"] if g["schedule_row"] is not None}
        self.assertEqual(sched, {"GSW@MEM": 270, "POR@MIL": 271, "NYK@MIN": 272, "LAC@SAS": 273})

    def test_page_break_rows_are_unverified_not_repaired(self) -> None:
        unverified = [row for row in self.rows if row["unverified"]]
        self.assertEqual([row["player"] for row in unverified], ["Kuminga, Jonathan", "Pullin, Zyon"])
        for row in unverified:
            self.assertEqual(row["team"], "")
            self.assertIn("page break", row["flag"])
            self.assertIn("not asserted", row["flag"])

    def test_every_row_has_a_status_or_reports_not_submitted(self) -> None:
        for row in self.rows:
            if row["status"]:
                self.assertIn(row["status"], VALID_STATUSES)
            else:
                self.assertEqual(row["reason"], "NOT YET SUBMITTED", row)

    def test_not_yet_submitted_rows_are_reporting_states(self) -> None:
        nys = [row for row in self.rows if row["reason"] == "NOT YET SUBMITTED"]
        # 3 on the 11/19 slate (GSW, MEM, MIL team rows) + 18 on the 11/20 next
        # slate (2 team rows per block × 9 blocks) = 21
        self.assertEqual(len(nys), 21)
        for row in nys:
            self.assertEqual(row["player"], "")
            self.assertEqual(row["status"], "")

    def test_por_mil_block_is_report_context(self) -> None:
        # the POR@MIL rows print no date cell; the date comes from the report's
        # same-date grouping (report context), corroborated by schedule row 271.
        # The schema mirrors the 11/17 file of record: cells_source "report", and
        # the date set from report context - never inferred.
        por = [g for g in self.data["games"] if g["matchup"] == "POR@MIL"]
        self.assertEqual(len(por), 1)
        self.assertEqual(por[0]["cells_source"], "report")
        self.assertEqual(por[0]["game_date"], "2026-11-19")
        self.assertEqual(por[0]["schedule_row"], 271)

    def test_tip_disagreements_are_flagged_not_resolved(self) -> None:
        # the schedule PDF prints two tip times (7:00 PM / 8:00 PM) for 11/19; the
        # report and games page print 8:00 PM ET; both are published, neither overwritten
        for game in self.data["games"]:
            self.assertTrue(game["tip_disagreement"], game["matchup"])
            if game["schedule_row"] is not None:
                self.assertIn("7:00 PM", game["tip_disagreement"])

    def test_no_derived_or_model_values(self) -> None:
        for row in self.rows:
            for key in row:
                self.assertNotIn(key, ("probability", "minutes", "impact", "pick"), key)

    def test_cross_check_against_the_independent_extraction_is_complete(self) -> None:
        cells = load("injuries-2026-11-19-0145am.cells.json")
        check = cells["cross_check"]
        self.assertEqual(check["rows_in_this_extraction"], 44)
        self.assertEqual(check["rows_in_the_counterpart"], 44)
        self.assertEqual(check["rows_matching_row_for_row"], 44)
        self.assertEqual(check["only_in_this_extraction"], [])
        self.assertEqual(check["only_in_the_counterpart"], [])


class InjuryChain20261119Tests(unittest.TestCase):
    """The 2026-11-19 revision chain: eight dated revisions, seven consecutive
    diffs, one boundary diff across the 11/18 gap, and the newest pointer."""

    REVISIONS = [
        "1200am", "1215am", "1230am", "1245am",
        "0100am", "0115am", "0130am", "0145am",
    ]

    def test_every_revision_is_transcribed_with_provenance(self) -> None:
        for clock in self.REVISIONS:
            data = load(f"injuries-2026-11-19-{clock}.json")
            for key in REQUIRED_PROVENANCE:
                self.assertTrue(data[key], (clock, key))
            self.assertEqual(data["player_rows_counted"], 23, clock)
            # The 12:30 AM revision prints the 11/20 BKN/TOR/DET rows as ONE merged
            # cell row, so it carries 42 printed rows instead of 44 - a printing
            # variance kept verbatim, not a data change.
            expected_rows = 42 if clock == "1230am" else 44
            self.assertEqual(data["row_count"], expected_rows, clock)
            raw = SNAPSHOTS / "raw" / f"injury-2026-11-19T{clock}-et.pipes"
            self.assertTrue(raw.exists(), raw)
            self.assertIn("Injury Report: 11/19/26", raw.read_text(encoding="utf-8"))

    def test_consecutive_diffs_report_no_status_changes(self) -> None:
        for i in range(len(self.REVISIONS) - 1):
            a, b = self.REVISIONS[i], self.REVISIONS[i + 1]
            diff = load(f"injuries-2026-11-19-{a}-to-{b}.diff.json")
            self.assertEqual(diff["kind"], "official_injury_report_consecutive_diff")
            self.assertEqual(diff["counts"]["status_changes"], 0, (a, b))
            self.assertEqual(diff["counts"]["reason_changes"], 0, (a, b))
            self.assertEqual(diff["counts"]["team_changes"], 0, (a, b))
            # The 12:30 revision prints the 11/20 BKN/TOR/DET rows as one merged
            # cell row (a printing variance); every other consecutive pair aligns
            # row-for-row with zero unaligned rows.
            if (a, b) == ("1215am", "1230am") or (a, b) == ("1230am", "1245am"):
                self.assertTrue(diff.get("printing_variance_note"), (a, b))
            else:
                self.assertEqual(diff["counts"]["old_rows"], 44, (a, b))
                self.assertEqual(diff["counts"]["new_rows"], 44, (a, b))
                self.assertEqual(diff["old"]["unaligned_rows"], 0, (a, b))
                self.assertEqual(diff["new"]["unaligned_rows"], 0, (a, b))

    def test_boundary_diff_across_the_1118_gap_is_flagged_not_filled(self) -> None:
        diff = load("injuries-2026-11-17-1115-to-2026-11-19-1200.diff.json")
        self.assertEqual(diff["kind"], "official_injury_report_boundary_diff")
        self.assertEqual(diff["old"]["rows"], 60)
        self.assertEqual(diff["new"]["rows"], 44)
        self.assertEqual(diff["counts"]["status_changes"], 0)
        self.assertIn("no 11/18 revisions", diff["alignment"])

    def test_newest_pointer_names_the_145_revision_and_the_gap(self) -> None:
        pointer = load("injuries-newest-pointer-2026-11-19.json")
        self.assertEqual(pointer["newest_listed"]["label"], "11/19 1:45 a.m. ET report")
        self.assertEqual(len(pointer["chain_transcribed"]), 8)
        self.assertIn("no 11/18", pointer["gap_note"])
        self.assertTrue(pointer["newest_listed"]["rows_transcribed"])


if __name__ == "__main__":
    unittest.main()
