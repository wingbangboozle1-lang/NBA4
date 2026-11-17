"""Tests for the official-snapshot data files and their rendered tables.

The site's slate and injury tables are generated from ``data/snapshots/*.json``
by ``scripts/build_snapshots.py``. These tests keep the data honest (provenance,
no invented values) and keep the published pages in sync with the data. The
current snapshot is the 2026-11-17 refresh; the 2026-11-16, 2026-11-15 and
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

CURRENT_INJURY_FILE = "injuries-2026-11-17-1030am.json"
PREVIOUS_INJURY_FILE = "injuries-2026-11-15-0615am.json"
HISTORICAL_INJURY_FILE = "injuries-2026-11-14-0430am.json"
CURRENT_SLATE_FILE = "slate-2026-11-17.json"
GAMELOGS = "player-gamelogs-2026-11-14_to_2026-11-15.json"

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
            # verified live on the games pages: row 245 -> 0022600245, row 269 -> 0022600269
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


class CurrentInjurySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load(CURRENT_INJURY_FILE)
        cls.rows = injury_rows(CURRENT_INJURY_FILE)

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
        # 59 = every row the 10:30 AM document prints (2026-11-17 refresh).
        self.assertEqual(len(self.rows), 59)
        lost = [row for row in self.rows if row["team"] == "__lost__"]
        self.assertEqual(len(lost), 1)
        for row in lost:
            self.assertTrue(row["player"], "lost-team row must keep the player name")
            self.assertTrue(row["unverified"])
            self.assertTrue(row["flag"])

    def test_the_lost_team_row_is_the_reaves_row_and_is_never_inferred(self) -> None:
        reaves = [row for row in self.rows if row["player"] == "Reaves, Austin"]
        self.assertEqual(len(reaves), 1)
        self.assertEqual(reaves[0]["team"], "__lost__")
        self.assertEqual(reaves[0]["status"], "Out")
        self.assertEqual(reaves[0]["reason"], "Injury/Illness - Left Heel Contusion / Bone Bruise")
        self.assertTrue(reaves[0]["unverified"])
        self.assertIn("team cell lost at PDF page break", reaves[0]["flag"])
        # no status/reason column loss this cycle: every non-lost, non-NOT-YET-SUBMITTED
        # row keeps both a status and a reason cell
        for row in self.rows:
            if row["team"] == "__lost__" or row["reason"] == "NOT YET SUBMITTED":
                continue
            self.assertTrue(row["status"], row)
            self.assertTrue(row["reason"], row)

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
        self.assertEqual(check["rows_in_this_extraction"], 59)
        self.assertEqual(check["rows_in_the_counterpart"], 59)
        self.assertEqual(check["rows_matching_row_for_row"], 59)
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


class ResultsSnapshotTests(unittest.TestCase):
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


class AggregatesTests(unittest.TestCase):
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

    def test_result_feed_is_not_settlement_eligible_without_quarter_scores(self) -> None:
        rf = self.agg["result_feed"]
        self.assertEqual(rf["team_lines_checked"], 16)
        self.assertEqual(rf["lines_that_disagree"], 0)
        self.assertFalse(rf["quarters_captured"])
        self.assertFalse(rf["settlement_eligible"])

    def test_consecutive_revision_diff_counts(self) -> None:
        diff = load("injuries-2026-11-17-1015-to-1030.diff.json")
        counts = diff["counts"]
        self.assertEqual(counts["old_rows"], 59)
        self.assertEqual(counts["new_rows"], 59)
        self.assertEqual(counts["status_changes"], 0)
        self.assertEqual(counts["reason_changes"], 0)
        self.assertEqual(counts["printing_variances"], 0)
        self.assertEqual(diff["old"]["revision_label"], "11/17/26 10:15 AM")
        self.assertEqual(diff["new"]["revision_label"], "11/17/26 10:30 AM")
        variance = [c for c in diff["changes"] if c["kind"] == "PRINTING_VARIANCE"]
        self.assertEqual(len(variance), 0)


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
        self.assertEqual(injuries_html.count(build_snapshots.REPORT_URL), 59)  # one per report row
        self.assertEqual(
            injuries_html.count(build_snapshots.SCHEDULE_URL),
            sum(
                1
                for game in load(CURRENT_INJURY_FILE)["games"]
                if game["cells_source"].startswith("schedule") or game["cells_source"] == "report-context"
                for _ in game["rows"]
            ),
        )


class AwayHomeBasisTests(unittest.TestCase):
    """The slate page shows "at" only where an official document confirms the order:
    the injury report's own matchup code for the same game date, or the schedule's
    printed "at" token. Code-only matching is not enough: POR@MIN appears in the
    11/16 report and again as the 11/17 slate row 254."""

    def test_code_corroborated_rows_are_exactly_253_to_269(self) -> None:
        report_codes = {
            (g.get("game_date") or g.get("game_date_from_schedule", ""), g["matchup"])
            for g in load(CURRENT_INJURY_FILE)["games"]
        }
        corroborated = set()
        for game in load(CURRENT_SLATE_FILE)["games"]:
            if (game["date"], f"{build_snapshots.ABBR[game['away']]}@{build_snapshots.ABBR[game['home']]}") in report_codes:
                corroborated.add(game["row"])
        self.assertEqual(corroborated, set(range(253, 270)))

    def test_rendered_slate_marks_every_row_corroborated(self) -> None:
        html = build_snapshots.render_slate()
        # all 21 rows are corroborated (17 report-code rows + 14 printed-"at" rows,
        # with rows 260-269 counted in both); no row rests on printed order alone
        self.assertEqual(html.count("</strong> at <strong>"), 21)
        self.assertEqual(html.count("(order unverified)"), 0)
        self.assertEqual(html.count('prints no "at"'), 0)

    def test_at_token_rows_are_not_flagged(self) -> None:
        data = load(CURRENT_SLATE_FILE)
        at_rows = {g["row"] for g in data["games"] if g.get("at_token_printed")}
        self.assertEqual(at_rows, set(range(260, 274)))


class GameLogTests(unittest.TestCase):
    """Task BI (arena/dab321e7-nba4): per-player game logs are dated attributed
    observations with row-level official links, never inferred values and never
    betting inputs. Merged into this suite at the third parallel collision."""

    GAMELOGS = "player-gamelogs-2026-11-14_to_2026-11-15.json"
    INJURY_1116 = "injuries-2026-11-16-0915am.json"

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
