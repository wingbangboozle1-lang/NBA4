"""Tests for the official-snapshot data files and their rendered tables.

The site's slate and injury tables are generated from ``data/snapshots/*.json``
by ``scripts/build_snapshots.py``. These tests keep the data honest (provenance,
no invented values) and keep the published pages in sync with the data. The
current snapshot is the 2026-11-19 refresh; the 2026-11-17, 2026-11-16,
2026-11-15 and 2026-11-14 files are kept as dated historical snapshots and
stay covered by their own assertions.
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
    "slate-2026-11-19.json": ({"2026-11-19", "2026-11-20", "2026-11-21"}, 43, 279, 19),
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
CURRENT_SLATE_FILE = "slate-2026-11-19.json"
GAMELOGS = "player-gamelogs-2026-11-17_to_2026-11-18.json"

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

    def test_current_slate_is_exact_rows_and_three_dates(self) -> None:
        # 2026-11-19 cycle: date-window rows 270-279 (11/19 and 11/21) plus the
        # nine NBA Cup rows 43-51 of 11/20 - 19 games on non-contiguous rows
        games = load(CURRENT_SLATE_FILE)["games"]
        self.assertEqual(
            [g["row"] for g in games], sorted([*range(43, 52), *range(270, 280)])
        )
        self.assertEqual(
            {g["date"] for g in games}, {"2026-11-19", "2026-11-20", "2026-11-21"}
        )
        self.assertEqual(sum(1 for g in games if g["nba_cup_flag_as_printed"]), 9)

    def test_every_slate_row_matches_its_verbatim_raw_line(self) -> None:
        # folded from the parallel BM session: the published games must equal the
        # verbatim raw schedule transcription cell for cell (tip column depends on
        # whether the printed row carries an "at" token)
        raw = (ROOT / "data/snapshots/raw/schedule-2026-11-19-window-rows-43-51-270-279.txt").read_text(encoding="utf-8")
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
        self.assertEqual(disagreeing, {49})  # PHX@UTA: games page 9:00 vs PDF+report 9:30
        matches = 0
        for game in data["games"]:
            # verified live on the games pages: Cup rows 43-51 -> 0022600043-0022600051,
            # date-window rows 270-279 -> 0022600270-0022600279
            row = game["row"]
            expected = (
                "00226000" + str(row).zfill(2) if row < 100 else "0022600" + str(row)
            )
            self.assertEqual(game["games_page_game_id"], expected, row)
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
        self.assertEqual(matches, 18)


class CurrentInjurySnapshotTests(unittest.TestCase):
    """The 2026-11-19 01:45 AM ET report: the file of record for this cycle."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(CURRENT_INJURY_FILE)
        cls.rows = injury_rows(CURRENT_INJURY_FILE)

    def test_provenance_present(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("01:45 AM", self.data["source_document_header"])
        self.assertIn("supersede", self.data["supersession_note"])
        self.assertIn("01:45", self.data["newest_report_listed_at_check"]["label"])

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

    def test_row_count_and_unattributed_rows(self) -> None:
        # 42 printed rows in 13 game blocks + 2 continuation-page fragments kept
        # unattributed = the 44 rows the document prints (row_count)
        self.assertEqual(len(self.rows), 42)
        self.assertEqual(self.data["row_count"], 44)
        self.assertEqual(len(self.data["games"]), 13)
        unattr = self.data["unattributed_rows"]
        self.assertEqual([r["player"] for r in unattr], ["Kuminga, Jonathan", "Pullin, Zyon"])
        for row in unattr:
            self.assertTrue(row["unverified"])
            self.assertTrue(row["flag"])
            self.assertEqual(row["team"], "")
        # no block row lost its team cell this cycle
        lost = [row for row in self.rows if row["team"] == "__lost__" or not row["team"]]
        self.assertEqual(lost, [])

    def test_page_break_rows_are_recorded_as_extracted(self) -> None:
        # rows whose printed cells were lost at the PDF's page breaks keep blank
        # cells and a named flag; nothing is repaired
        broken = [row for row in self.rows if row["unverified"]]
        self.assertEqual(len(broken), 13)
        for row in broken:
            self.assertTrue(row["flag"])
        # the seven continuation-page NOT YET SUBMITTED rows keep the marker in
        # the reason cell and no player/status is inferred
        nys_broken = [row for row in broken if row["reason"] == "NOT YET SUBMITTED"]
        self.assertEqual(len(nys_broken), 7)
        for row in nys_broken:
            self.assertEqual(row["player"], "")
            self.assertEqual(row["status"], "")

    def test_report_revision_is_the_0145_document(self) -> None:
        self.assertIn("01:45 AM", self.data["source_document_header"])
        self.assertEqual(self.data["source_url"], build_snapshots.REPORT_URL)
        self.assertEqual(self.data["revision_utc"], "2026-11-19T06:45:00Z")

    def test_block_position_rows_are_unverified(self) -> None:
        # any row whose printed matchup cell was lost, so the game attachment
        # rests on block position alone, must carry unverified
        for game in self.data["games"]:
            self.assertTrue(game["matchup"])
            for row in game["rows"]:
                if row["player"] == "" and row["reason"] != "NOT YET SUBMITTED":
                    self.assertTrue(row["unverified"], row)

    def test_not_yet_submitted_rows_are_reporting_states(self) -> None:
        nys = [row for row in self.rows if row["reason"] == "NOT YET SUBMITTED"]
        # 11/19: GSW+MEM; 11/20: both teams of CHA@ATL, IND@CLE, ORL@BKN plus
        # MIL and the six second-team markers on the continuation page
        self.assertEqual(len(nys), 15)
        for row in nys:
            self.assertEqual(row["player"], "")
            self.assertEqual(row["status"], "")

    def test_nyk_min_block_prints_timberwolves_rows_only(self) -> None:
        block = [g for g in self.data["games"] if g["matchup"] == "NYK@MIN"]
        self.assertEqual(len(block), 1)
        teams = {r["team"] for r in block[0]["rows"]}
        self.assertEqual(teams, {"Minnesota Timberwolves"})

    def test_game_cells_come_from_the_report_and_match_the_slate(self) -> None:
        slate = {game["row"]: game for game in load(CURRENT_SLATE_FILE)["games"]}

        def clock(value: str) -> str:
            hour, minute = value.split(":")
            minute_digits = "".join(ch for ch in minute if ch.isdigit())
            return f"{int(hour)}:{minute_digits}"

        for game in self.data["games"]:
            source = game.get("cells_source") or game.get("game_date_source", "")
            self.assertTrue(source.startswith(("report", "schedule")), game["matchup"])
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
            # blocks whose rows printed their own Game Time must agree with the
            # schedule's ET column; continuation rows that lost the time cell
            # carry an empty tip_et_from_report and rest on the schedule alone
            if game["tip_et_from_report"]:
                self.assertEqual(
                    clock(game["tip_et_from_report"].replace(" (ET)", "")),
                    clock(slate[row]["tip_et_col2"]),
                    game["matchup"],
                )
            else:
                self.assertEqual(
                    game["tip_et_from_schedule"], slate[row]["tip_et_col2"], game["matchup"]
                )

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


class InjurySnapshot20261117Tests(unittest.TestCase):
    """The 2026-11-17 10:30 AM snapshot is historical; its own assertions stay."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(INJURY_20261117_FILE)
        cls.rows = injury_rows(INJURY_20261117_FILE)

    def test_provenance_and_row_count(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertIn("10:30 AM", self.data["source_document_header"])
        self.assertIn("supersede", self.data["supersession_note"])
        self.assertEqual(len(self.rows), 60)

    def test_lost_team_rows_are_kept_not_unattributed(self) -> None:
        # this extraction keeps both printed page-break rows inside their blocks
        # with a blank lost team cell rather than a separate unattributed_rows
        # list - the printed 'Soreness' fragment would be unpublished otherwise
        lost = [row for row in self.rows if row["team"] == "__lost__"]
        self.assertEqual([row["player"] for row in lost], ["Soreness", "Reaves, Austin"])
        for row in lost:
            self.assertTrue(row["unverified"])
            self.assertTrue(row["flag"])

    def test_page_break_rows_are_recorded_as_extracted(self) -> None:
        minnesota = [
            row for row in self.rows
            if row["player"] == "" and row["team"] == "Minnesota Timberwolves"
        ]
        self.assertEqual(len(minnesota), 1)
        self.assertEqual(minnesota[0]["status"], "")
        self.assertTrue(minnesota[0]["unverified"])
        self.assertIn("page break", minnesota[0]["flag"])
        fragment = [row for row in self.rows if row["player"] == "Soreness"]
        self.assertEqual(len(fragment), 1)
        self.assertEqual(fragment[0]["status"], "")
        self.assertEqual(fragment[0]["reason"], "")
        self.assertTrue(fragment[0]["unverified"])
        reaves = [row for row in self.rows if row["player"] == "Reaves, Austin"]
        self.assertEqual(len(reaves), 1)
        self.assertEqual(reaves[0]["status"], "Out")
        self.assertEqual(reaves[0]["reason"], "Injury/Illness - Left Heel Contusion / Bone Bruise")
        self.assertEqual(reaves[0]["team"], "__lost__")
        self.assertTrue(reaves[0]["unverified"])
        five_cell = [
            row for row in self.rows
            if row.get("flag", "").startswith("the printed row carries five cells")
        ]
        self.assertEqual(len(five_cell), 8)
        for row in five_cell:
            self.assertEqual(row["reason"], "NOT YET SUBMITTED")
            self.assertEqual(row["player"], "")
            self.assertEqual(row["status"], "")

    def test_not_yet_submitted_rows_are_reporting_states(self) -> None:
        nys = [row for row in self.rows if row["reason"] == "NOT YET SUBMITTED"]
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
        slate = {game["row"]: game for game in load("slate-2026-11-17.json")["games"]}

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
                self.assertIn(
                    game["tip_et_from_report"].replace(" (ET)", ""), game["tip_disagreement"]
                )
                self.assertIn(slate[row]["tip_et_col2"], game["tip_disagreement"])
                continue
            self.assertEqual(
                clock(game["tip_et_from_report"].replace(" (ET)", "")),
                clock(slate[row]["tip_et_col2"]),
                game["matchup"],
            )

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
        cls.rest = load("rest-window-2026-11-19.json")
        cls.slate = load(CURRENT_SLATE_FILE)

    def test_coverage_rule_is_declared(self) -> None:
        self.assertEqual(self.rest["coverage"]["first_date"], "2026-11-10")
        self.assertEqual(self.rest["coverage"]["last_date"], "2026-11-21")
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
        self.assertEqual(slate_html.count("<tr>"), 20)  # header + 19 games
        self.assertEqual(slate_html.count("NO PICK"), 19)
        self.assertEqual(slate_html.count(build_snapshots.SCHEDULE_URL), 19)

        injuries_html = build_snapshots.render_injuries()
        # one report link per printed row: 42 block rows + 2 unattributed rows
        self.assertEqual(injuries_html.count(build_snapshots.REPORT_URL), 44)
        self.assertEqual(
            injuries_html.count(build_snapshots.SCHEDULE_URL),
            sum(
                1
                for game in load(CURRENT_INJURY_FILE)["games"]
                if (game.get("cells_source") or game.get("game_date_source", "")).startswith("schedule")
                for _ in game["rows"]
            ),
        )


class TeamStatsSnapshotTests(unittest.TestCase):
    """Mirror of scripts/check_site.py audit_team_stats for the current file."""

    TEAM_STATS = "team-stats-2026-11-19.json"
    STANDINGS = "standings-2026-11-19.json"

    def test_thirty_unique_team_rows_without_rank_columns(self) -> None:
        data = load(self.TEAM_STATS)
        for section in ("advanced_rows", "opponent_rows"):
            rows = data.get(section, [])
            teams = [r.get("team") for r in rows]
            self.assertEqual(len(rows), 30, section)
            self.assertEqual(len(set(teams)), 30, section)
            for r in rows:
                rank_keys = [k for k in r if k.lower().startswith("rank")]
                self.assertEqual(rank_keys, [], f"{section} {r.get('team')}")

    def test_gp_w_l_agree_between_pages_and_with_standings(self) -> None:
        data = load(self.TEAM_STATS)
        standings = {r["team"]: (r["w"] + r["l"], r["w"], r["l"]) for r in load(self.STANDINGS)["rows"]}
        adv = {r["team"]: (r["gp"], r["w"], r["l"]) for r in data["advanced_rows"]}
        opp = {r["team"]: (r["gp"], r["w"], r["l"]) for r in data["opponent_rows"]}
        for team in sorted(set(adv) | set(opp)):
            self.assertEqual(adv.get(team), opp.get(team), team)
            self.assertEqual(adv.get(team), standings.get(team), team)

    def test_model_inputs_stay_refused(self) -> None:
        data = load(self.TEAM_STATS)
        self.assertIn("REFUSED", data["model_inputs_status"])
        self.assertIn("G0", data["model_inputs_status"])


class AwayHomeBasisTests(unittest.TestCase):
    """The slate page shows "at" only where an official document confirms the order:
    the injury report's own matchup code for the same game date, or the schedule's
    printed "at" token. Code-only matching is not enough: POR@MIN appears as an
    11/17 report block and again as the 11/18 slate row 264."""

    def test_code_corroborated_rows_are_the_report_blocks(self) -> None:
        report_codes = {
            (g.get("game_date") or g.get("game_date_from_schedule", ""), g["matchup"])
            for g in load(CURRENT_INJURY_FILE)["games"]
        }
        corroborated = set()
        for game in load(CURRENT_SLATE_FILE)["games"]:
            if (game["date"], f"{build_snapshots.ABBR[game['away']]}@{build_snapshots.ABBR[game['home']]}") in report_codes:
                corroborated.add(game["row"])
        # all four 11/19 games and all nine 11/20 games have a report block;
        # the six 11/21 games tip after the report's horizon
        self.assertEqual(corroborated, {270, 271, 272, 273, *range(43, 52)})

    def test_every_window_row_is_corroborated(self) -> None:
        html = build_snapshots.render_slate()
        # every window row prints the schedule's "at" token and the games-page
        # slug agrees, so all 19 games show away-at-home; none shows printed
        # order alone
        self.assertEqual(html.count("</strong> at <strong>"), 19)
        self.assertEqual(html.count("(order unverified)"), 0)
        self.assertEqual(html.count('prints no "at"'), 0)

    def test_at_token_rows_are_not_flagged(self) -> None:
        data = load(CURRENT_SLATE_FILE)
        at_rows = {g["row"] for g in data["games"] if g.get("at_token_printed")}
        self.assertEqual(at_rows, {*range(43, 52), *range(270, 280)})


class GameLogTests(unittest.TestCase):
    """Task BI (arena/dab321e7-nba4): per-player game logs are dated attributed
    observations with row-level official links, never inferred values and never
    betting inputs. Merged into this suite at the third parallel collision."""

    GAMELOGS = "player-gamelogs-2026-11-17_to_2026-11-18.json"
    INJURY_1116 = "injuries-2026-11-19-0145am.json"

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
        covered = [
            (p["report_block"], p["report_name"])
            for p in self.data["players"]
            if p["report_name"]
        ]
        self.assertEqual(len(covered), len(set(covered)))
        self.assertEqual(set(covered), injury_rows)
        # NOT YET SUBMITTED team rows name no player: recorded as gaps, never
        # given an invented name, and each mirrors a team row of the report
        team_rows = {
            (game["matchup"], row["team"])
            for game in load(self.INJURY_1116)["games"]
            for row in game["rows"]
            if not row["player"] and row["team"]
        }
        blanks = [p for p in self.data["players"] if not p["report_name"]]
        self.assertEqual(len(blanks), 2)
        for p in blanks:
            self.assertIn((p["report_block"], p["report_team"]), team_rows)
            self.assertEqual(p["report_reason"], "NOT YET SUBMITTED")

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
        # the two NOT YET SUBMITTED team rows of GSW@MEM name no player to follow
        self.assertEqual(len(gaps), 2)
        for p in gaps:
            self.assertEqual(p["games"], [])
            self.assertEqual(p["report_reason"], "NOT YET SUBMITTED")
            self.assertIn("no report player to follow", p["gap"])

    def test_every_game_date_falls_inside_the_observation_window(self) -> None:
        window = self.data["observation_window"]
        self.assertEqual(window["from_date"], "2026-11-17")
        self.assertEqual(window["to_date"], "2026-11-18")
        for p in self.data["players"]:
            for g in p["games"]:
                self.assertGreaterEqual(g["date"], window["from_date"], p["report_name"])
                self.assertLessEqual(g["date"], window["to_date"], p["report_name"])

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


class ResultsSnapshot20261117Tests(unittest.TestCase):
    """2026-11-17 finals: five games, every team line checked against the gamebook."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("results-2026-11-17.json")

    def test_provenance_and_shape(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertEqual(len(self.data["rows"]), 5)
        self.assertEqual(len(self.data["row_format"]), 16)
        self.assertIn("away_ot", self.data["row_format"])

    def test_every_period_sum_equals_the_printed_final(self) -> None:
        checks = self.data["verification"]["quarter_sum_check"]
        self.assertEqual(len(checks), 10)  # 5 games x 2 team lines
        for check in checks:
            periods = check[2:-2]
            final = check[-2]
            agrees = check[-1]
            self.assertTrue(agrees, check)
            self.assertEqual(sum(periods), final, check)

    def test_winner_loser_and_source_urls(self) -> None:
        for row in self.data["rows"]:
            away, home, af, hf = row[5], row[6], row[8], row[10]
            winner, loser = (away, home) if af > hf else (home, away)
            self.assertEqual(row[11], winner, row[0])
            self.assertEqual(row[12], loser, row[0])
            self.assertTrue(row[13].startswith("https://"), row[13])
            self.assertIn("nba.com", row[13])
            # both official documents printed the same finals for every game
            self.assertEqual(
                self.data["verification"]["finals_cross_check"][
                    "games_whose_two_documents_agree_on_both_finals"
                ],
                5,
            )

    def test_no_row_invents_venue_cells(self) -> None:
        for row in self.data["rows"]:
            self.assertEqual(row[3], "", row[0])  # arena not printed by the sources
            self.assertEqual(row[4], "", row[0])  # city not printed by the sources
            # away_q/home_q hold the four regulation quarters; away_ot/home_ot
            # hold printed overtime periods only (empty when there were none)
            self.assertEqual(len(row[7]), 4, row[0])
            self.assertEqual(len(row[9]), 4, row[0])
            self.assertEqual(sum(row[7]) + sum(row[14]), row[8], row[0])
            self.assertEqual(sum(row[9]) + sum(row[15]), row[10], row[0])
        self.assertIn("away_ot", self.data["row_format_note"])

    def test_the_one_overtime_game_keeps_its_ot_periods(self) -> None:
        ot_rows = [row for row in self.data["rows"] if row[14] or row[15]]
        self.assertEqual([row[0] for row in ot_rows], ["0022600256"])  # CHA@LAL
        row = ot_rows[0]
        self.assertEqual(row[14], [3])
        self.assertEqual(row[15], [7])
        self.assertEqual(sum(row[7]) + sum(row[14]), row[8])  # 111 + 3 = 114
        self.assertEqual(sum(row[9]) + sum(row[15]), row[10])  # 111 + 7 = 118


class ResultsSnapshot20261118Tests(unittest.TestCase):
    """2026-11-18 finals: twelve games, 24 team lines, no overtime."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("results-2026-11-18.json")

    def test_provenance_and_shape(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        self.assertEqual(len(self.data["rows"]), 12)
        self.assertEqual(len(self.data["row_format"]), 16)

    def test_every_period_sum_equals_the_printed_final(self) -> None:
        checks = self.data["verification"]["quarter_sum_check"]
        self.assertEqual(len(checks), 24)  # 12 games x 2 team lines
        for check in checks:
            periods = check[2:-2]
            final = check[-2]
            agrees = check[-1]
            self.assertTrue(agrees, check)
            self.assertEqual(sum(periods), final, check)

    def test_no_game_of_the_date_went_to_overtime(self) -> None:
        ot_rows = [
            row for row in self.data["rows"] if len(row[7]) > 4 or len(row[9]) > 4 or row[14] or row[15]
        ]
        self.assertEqual(ot_rows, [])

    def test_finals_cross_check_agrees_for_every_game(self) -> None:
        fc = self.data["verification"]["finals_cross_check"]
        self.assertEqual(fc["games_checked"], 12)
        self.assertEqual(fc["games_whose_two_documents_agree_on_both_finals"], 12)

    def test_winner_loser_and_source_urls(self) -> None:
        for row in self.data["rows"]:
            away, home, af, hf = row[5], row[6], row[8], row[10]
            winner, loser = (away, home) if af > hf else (home, away)
            self.assertEqual(row[11], winner, row[0])
            self.assertEqual(row[12], loser, row[0])
            self.assertTrue(row[13].startswith("https://"), row[13])
            self.assertIn("nba.com", row[13])


class StandingsSnapshot20261119Tests(unittest.TestCase):
    """The 2026-11-19 standings page: 30 rows, splits summing to league totals."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load("standings-2026-11-19.json")

    def test_thirty_rows_split_fifteen_fifteen(self) -> None:
        for key in REQUIRED_PROVENANCE:
            self.assertTrue(self.data[key], key)
        rows = self.data["rows"]
        self.assertEqual(len(rows), 30)
        self.assertEqual(len({r["team"] for r in rows}), 30)
        self.assertEqual(sum(1 for r in rows if r["conf"] == "East"), 15)
        self.assertEqual(sum(1 for r in rows if r["conf"] == "West"), 15)

    def test_league_wins_equal_losses(self) -> None:
        rows = self.data["rows"]
        self.assertEqual(sum(r["w"] for r in rows), 222)
        self.assertEqual(sum(r["l"] for r in rows), 222)
        checks = self.data["consistency_checks"]
        self.assertTrue(checks["league_wins_equal_losses"])
        self.assertEqual(checks["league_team_game_lines"], 444)
        # 221 HOME + 221 ROAD + 2 NEUTRAL (DEN 1-0 and IND 0-1)
        self.assertEqual(checks["league_home_games"], 221)
        self.assertEqual(checks["league_road_games"], 221)
        self.assertEqual(checks["league_neutral_games"], 2)

    def test_every_row_split_sums_to_its_games_played(self) -> None:
        checks = self.data["consistency_checks"]
        self.assertEqual(checks["rows_checked"], 30)
        self.assertEqual(checks["rows_whose_splits_sum_to_its_games_played"], 30)
        for row in self.data["rows"]:
            self.assertTrue(row["split_sum_equals_gp"], row["team"])
            home_w, home_l = (int(x) for x in row["home"].split("-"))
            road_w, road_l = (int(x) for x in row["road"].split("-"))
            neut_w, neut_l = (int(x) for x in row["neutral"].split("-"))
            self.assertEqual(home_w + home_l, row["home_games"], row["team"])
            self.assertEqual(road_w + road_l, row["road_games"], row["team"])
            self.assertEqual(neut_w + neut_l, row["neutral_games"], row["team"])
            self.assertEqual(home_w + road_w + neut_w, row["w"], row["team"])
            self.assertEqual(home_l + road_l + neut_l, row["l"], row["team"])

    def test_no_rank_columns_or_model_values(self) -> None:
        for row in self.data["rows"]:
            for key in row:
                self.assertFalse(key.lower().startswith("rank"), key)
                self.assertNotIn(key, ("rest", "b2b", "prob", "pick", "line"), key)


class InjuryDiff20261119Tests(unittest.TestCase):
    """11/17 10:30 AM -> 11/19 01:45 AM: a day-apart revision diff, no hand-pairing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.diff = load("injuries-2026-11-17-1030-to-1119-0145.diff.json")

    def test_counts_and_labels(self) -> None:
        counts = self.diff["counts"]
        self.assertEqual(counts["old_rows"], 60)
        self.assertEqual(counts["new_rows"], 42)
        self.assertEqual(counts["status_changes"], 0)
        self.assertEqual(counts["reason_changes"], 0)
        self.assertEqual(counts["team_changes"], 0)
        self.assertEqual(counts["printing_variances"], 0)
        self.assertEqual(counts["realigned"], 102)
        self.assertEqual(self.diff["old"]["revision_label"], "11/17/26 10:30 AM")
        self.assertEqual(self.diff["new"]["revision_label"], "11/19/26 01:45 AM")

    def test_day_apart_revisions_produce_only_removals_and_additions(self) -> None:
        # the matchup is part of the match key, so cross-day rows never pair:
        # every old row is REMOVED and every new row ADDED_OR_REALIGNED
        kinds = {}
        for change in self.diff["changes"]:
            kinds[change["kind"]] = kinds.get(change["kind"], 0) + 1
        self.assertEqual(kinds.get("REMOVED_OR_REALIGNED"), 60)
        self.assertEqual(kinds.get("ADDED_OR_REALIGNED"), 42)
        # no change event may claim a status or reason difference
        for change in self.diff["changes"]:
            self.assertIn(
                change["kind"], ("REMOVED_OR_REALIGNED", "ADDED_OR_REALIGNED")
            )


class Aggregates20261119Tests(unittest.TestCase):
    """The 2026-11-19 aggregates: home court, settlement feed, injury load, slate."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.agg = load("aggregates-2026-11-19.json")

    def test_home_court_rate_is_arithmetic_on_the_standings(self) -> None:
        hc = self.agg["home_court"]
        self.assertEqual((hc["home_wins"], hc["home_losses"]), (111, 110))
        self.assertEqual(hc["home_games"], 221)
        self.assertEqual(hc["measured_home_win_rate"], 0.5023)
        self.assertEqual((hc["neutral_wins"], hc["neutral_losses"]), (1, 1))

    def test_pin_matches_the_engine_conversion(self) -> None:
        import sys as _sys

        _sys.path.insert(0, str(ROOT))
        from engine.homerate import pin_home_advantage

        standings = load("standings-2026-11-19.json")
        pin = pin_home_advantage(standings["rows"], source_url=standings["source_url"])
        self.assertEqual(self.agg["home_court"]["pin"]["home_advantage_points"], round(pin.points, 3))
        self.assertFalse(pin.authorized)

    def test_result_feed_is_settlement_eligible(self) -> None:
        rf = self.agg["result_feed"]
        self.assertEqual(rf["games"], 12)
        self.assertEqual(rf["team_lines_checked"], 24)
        self.assertEqual(rf["lines_that_disagree"], 0)
        self.assertTrue(rf["settlement_eligible"])

    def test_standings_consistency_uses_the_neutral_column(self) -> None:
        sc = self.agg["standings_consistency"]
        self.assertEqual((sc["league_wins"], sc["league_losses"]), (222, 222))
        self.assertTrue(sc["wins_equal_losses"])
        self.assertEqual(sc["home_plus_road_plus_neutral"], 444)

    def test_injury_load_counts_match_the_file_of_record(self) -> None:
        load_ = self.agg["injury_load"]
        self.assertEqual(load_["revision"], "11/19/26 01:45 AM")
        self.assertEqual(load_["rows"], 42)
        self.assertEqual(load_["rows_with_a_status"], 21)
        self.assertEqual(load_["not_yet_submitted_rows"], 15)
        self.assertEqual(load_["unverified_rows_after_page_breaks"], 13)
        self.assertEqual(sum(load_["status_counts"].values()), 42)

    def test_slate_and_inputs_point_at_this_cycle(self) -> None:
        self.assertEqual(self.agg["slate"]["games"], 19)
        self.assertEqual(self.agg["inputs"]["standings"], "standings-2026-11-19.json")
        self.assertIn("0145am", self.agg["inputs"]["injuries"])
        self.assertIn("slate-2026-11-19", self.agg["inputs"]["slate"])


if __name__ == "__main__":
    unittest.main()
