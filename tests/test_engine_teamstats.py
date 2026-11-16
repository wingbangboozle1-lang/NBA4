"""Tests for engine/teamstats.py - the three official team-stat pages and the re-cut.

Every number below is synthetic and hand-computed. No NBA or market data
appears in this file; the live values read from the three pages on 2026-11-16
are recorded in docs/verification-pass-cc82e369.md instead, with their sources.

The synthetic league uses three teams so the arithmetic can be checked by hand:

=========  ====  =====  =====  ==========  ======  ============
team       GP    MIN    PTS    OPP PTS     PACE    MIN total
=========  ====  =====  =====  ==========  ======  ============
Synthetic  10    48.0   120.0  110.0       100.0   480.0
Control    10    48.4   110.0  120.0        98.0   484.0
Baseline   10    48.0   100.0  100.0        95.0   480.0
=========  ====  =====  =====  ==========  ======  ============

Derived by hand:

* Synthetic: possessions/game = 100.0 x (48.0/48) = 100.0; off PPP = 1.2;
  def PPP = 1.1; OffRtg 120.0; DefRtg 110.0; NetRtg 10.0; POSS = 100 x 10 = 1000.
* Control: possessions/game = 98.0 x (48.4/48) = 98.8166667; off PPP =
  110/98.8166667 = 1.1131725; def PPP = 120/98.8166667 = 1.2143700;
  POSS = 98 x (484/48) = 988.1667.
* Baseline: possessions/game = 95.0; off PPP = def PPP = 100/95 = 1.0526316;
  POSS = 950.
* League defensive PPP = (1.1 + 1.2143700 + 1.0526316)/3 = 1.1223339.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from engine import teamstats
from engine.contracts import Provenance, RightsError
from engine.totals import project_total

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
TEAMS = 3


def prov(allowed: bool = True) -> Provenance:
    return Provenance(
        source_id="synthetic.invalid",
        source_name="SYNTHETIC FIXTURE - NOT AN OFFICIAL SOURCE",
        source_url="https://www.nba.com/stats/teams/advanced",
        source_timestamp=NOW - timedelta(days=1),
        observed_at=NOW - timedelta(hours=1),
        version="synthetic-1",
        allowed_use=allowed,
        allowed_use_note="labelled synthetic fixture used only to prove the engine mechanics",
    )


def traditional(team: str, minutes: float, points: float, games: int = 10, allowed: bool = True):
    return teamstats.TraditionalRow(
        team=team,
        games_played=games,
        minutes_per_game=minutes,
        points=points,
        field_goals_made=40.0,
        field_goal_attempts=90.0,
        free_throw_attempts=30.0,
        offensive_rebounds=12.0,
        turnovers=15.0,
        provenance=prov(allowed),
    )


def opponent(team: str, minutes: float, points: float, games: int = 10, plus_minus=None, allowed: bool = True):
    return teamstats.OpponentRow(
        team=team,
        games_played=games,
        minutes_per_game=minutes,
        opponent_points=points,
        opponent_field_goals_made=38.0,
        opponent_field_goal_attempts=88.0,
        opponent_free_throw_attempts=25.0,
        opponent_offensive_rebounds=10.0,
        opponent_turnovers=14.0,
        provenance=prov(allowed),
        opponent_plus_minus=plus_minus,
    )


def advanced(
    team: str,
    minutes_total: float,
    pace: float,
    possessions: float,
    off_rating: float,
    def_rating: float,
    net_rating: float,
    games: int = 10,
    allowed: bool = True,
):
    return teamstats.AdvancedRow(
        team=team,
        games_played=games,
        minutes_total=minutes_total,
        pace=pace,
        possessions_total=possessions,
        offensive_rating=off_rating,
        defensive_rating=def_rating,
        net_rating=net_rating,
        provenance=prov(allowed),
    )


def synth_rows(allowed: bool = True, off_rating_override=None):
    """The three raw row tuples, so a test can build its own PageRead."""
    trad = (
        traditional("Synthetic", 48.0, 120.0, allowed=allowed),
        traditional("Control", 48.4, 110.0, allowed=allowed),
        traditional("Baseline", 48.0, 100.0, allowed=allowed),
    )
    opp = (
        opponent("Synthetic", 48.0, 110.0, plus_minus=-10.0, allowed=allowed),
        opponent("Control", 48.4, 120.0, plus_minus=10.0, allowed=allowed),
        opponent("Baseline", 48.0, 100.0, plus_minus=0.0, allowed=allowed),
    )
    adv = (
        advanced(
            "Synthetic",
            480.0,
            100.0,
            1000.0,
            off_rating_override if off_rating_override is not None else 120.0,
            110.0,
            10.0,
            allowed=allowed,
        ),
        advanced("Control", 484.0, 98.0, 988.0, 111.3, 121.4, -10.1, allowed=allowed),
        advanced("Baseline", 480.0, 95.0, 950.0, 105.3, 105.3, 0.0, allowed=allowed),
    )
    return trad, opp, adv


def three_pages(allowed: bool = True, off_rating_override=None):
    trad, opp, adv = synth_rows(allowed, off_rating_override)
    return (
        teamstats.PageRead(
            page=teamstats.StatPage.TRADITIONAL,
            rows=trad,
            source_url=teamstats.StatPage.TRADITIONAL.url,
            retrieved_at=NOW,
            rows_expected=TEAMS,
        ),
        teamstats.PageRead(
            page=teamstats.StatPage.OPPONENT,
            rows=opp,
            source_url=teamstats.StatPage.OPPONENT.url,
            retrieved_at=NOW,
            rows_expected=TEAMS,
        ),
        teamstats.PageRead(
            page=teamstats.StatPage.ADVANCED,
            rows=adv,
            source_url=teamstats.StatPage.ADVANCED.url,
            retrieved_at=NOW,
            rows_expected=TEAMS,
        ),
    )


class RowValidationTest(unittest.TestCase):
    def test_negative_values_rejected(self):
        with self.assertRaises(teamstats.TeamStatsError):
            traditional("Synthetic", -48.0, 120.0)

    def test_field_goals_made_cannot_exceed_attempts(self):
        with self.assertRaises(teamstats.TeamStatsError) as caught:
            teamstats.TraditionalRow(
                team="Synthetic",
                games_played=10,
                minutes_per_game=48.0,
                points=120.0,
                field_goals_made=95.0,
                field_goal_attempts=90.0,
                free_throw_attempts=30.0,
                offensive_rebounds=12.0,
                turnovers=15.0,
                provenance=prov(),
            )
        self.assertIn("field goals made exceed attempts", str(caught.exception))

    def test_opponent_page_margin_is_the_opponents_margin(self):
        # The opponent page's final column is the opponent's +/-, which is the
        # negative of the team's own margin on the traditional page. Stored
        # separately so the two are never averaged together.
        row = opponent("Synthetic", 48.0, 110.0, plus_minus=-10.0)
        self.assertEqual(row.opponent_plus_minus, -10.0)
        self.assertNotEqual(row.opponent_plus_minus, 120.0 - 110.0)

    def test_pace_must_be_positive(self):
        with self.assertRaises(teamstats.TeamStatsError):
            advanced("Synthetic", 480.0, 0.0, 1000.0, 120.0, 110.0, 10.0)

    def test_page_urls_are_the_three_official_documents(self):
        urls = teamstats.page_urls()
        self.assertEqual(
            set(urls.values()),
            {
                "https://www.nba.com/stats/teams/traditional",
                "https://www.nba.com/stats/teams/opponent",
                "https://www.nba.com/stats/teams/advanced",
            },
        )


class ReadCompletenessTest(unittest.TestCase):
    def test_partial_rows_refuse_the_recut(self):
        trad, opp, adv = three_pages()
        _, opp_rows, _ = synth_rows()
        partial = teamstats.PageRead(
            page=teamstats.StatPage.OPPONENT,
            rows=opp_rows[:1],
            source_url=teamstats.StatPage.OPPONENT.url,
            retrieved_at=NOW,
            rows_expected=3,
        )
        with self.assertRaises(teamstats.TeamStatsError) as caught:
            teamstats.recut(trad, partial, adv)
        self.assertIn("TEAMSTATS_INCOMPLETE_READ", str(caught.exception))
        self.assertIn("1 of 3 rows read", str(caught.exception))

    def test_partial_chunks_refuse_the_recut(self):
        trad, opp, adv = three_pages()
        _, _, adv_rows = synth_rows()
        partial = teamstats.PageRead(
            page=teamstats.StatPage.ADVANCED,
            rows=adv_rows,
            source_url=teamstats.StatPage.ADVANCED.url,
            retrieved_at=NOW,
            chunks_read=1,
            chunks_total=2,
            rows_expected=3,
        )
        with self.assertRaises(teamstats.TeamStatsError) as caught:
            teamstats.recut(trad, opp, partial)
        self.assertIn("1 of 2 chunks read", str(caught.exception))

    def test_full_read_is_complete(self):
        trad, _, _ = three_pages()
        self.assertTrue(trad.complete)
        self.assertIsNone(trad.refusal)

    def test_naive_retrieval_time_rejected(self):
        with self.assertRaises(teamstats.TeamStatsError):
            teamstats.PageRead(
                page=teamstats.StatPage.TRADITIONAL,
                rows=(),
                source_url=teamstats.StatPage.TRADITIONAL.url,
                retrieved_at=datetime(2026, 11, 16, 12, 0),
            )

    def test_uncleared_rows_refuse_the_recut(self):
        trad, opp, adv = three_pages(allowed=False)
        with self.assertRaises(RightsError):
            teamstats.recut(trad, opp, adv)

    def test_wrong_row_type_for_the_page_rejected(self):
        trad, opp, _ = three_pages()
        trad_rows, _, _ = synth_rows()
        traditional_rows_in_an_advanced_read = teamstats.PageRead(
            page=teamstats.StatPage.ADVANCED,
            rows=trad_rows,
            source_url=teamstats.StatPage.ADVANCED.url,
            retrieved_at=NOW,
            rows_expected=3,
        )
        with self.assertRaises(teamstats.TeamStatsError) as caught:
            teamstats.recut(trad, opp, traditional_rows_in_an_advanced_read)
        self.assertIn("expected AdvancedRow", str(caught.exception))


class RecutTest(unittest.TestCase):
    def setUp(self) -> None:
        self.table = teamstats.recut(*three_pages())

    def test_all_three_teams_joined(self):
        self.assertEqual(len(self.table.teams), 3)
        self.assertEqual(self.table.flags, ())

    def test_possessions_come_from_pace_not_from_a_scoring_average(self):
        synthetic = self.table.by_team("Synthetic")
        self.assertIsNotNone(synthetic)
        self.assertAlmostEqual(synthetic.possessions_per_game, 100.0, places=6)
        self.assertAlmostEqual(synthetic.offensive_ppp, 1.2, places=6)
        self.assertAlmostEqual(synthetic.defensive_ppp, 1.1, places=6)

    def test_overtime_minutes_lengthen_the_game_and_the_possession_count(self):
        control = self.table.by_team("Control")
        self.assertIsNotNone(control)
        self.assertAlmostEqual(control.possessions_per_game, 98.8166667, places=4)
        self.assertAlmostEqual(control.offensive_ppp, 1.1131725, places=6)

    def test_ratings_recomputed_from_possessions_match_the_printed_ratings(self):
        for entry in self.table.teams:
            for name in ("offensive_rating", "defensive_rating", "net_rating", "possessions_total"):
                self.assertTrue(
                    entry.checks[name]["agrees"],
                    f"{entry.team}: {name} disagrees: {entry.checks[name]}",
                )

    def test_a_disagreeing_printed_rating_is_flagged_not_repaired(self):
        trad, opp, adv = three_pages(off_rating_override=130.0)
        table = teamstats.recut(trad, opp, adv)
        synthetic = table.by_team("Synthetic")
        check = synthetic.checks["offensive_rating"]
        self.assertFalse(check["agrees"])
        self.assertAlmostEqual(check["computed"], 120.0, places=4)
        self.assertEqual(check["printed"], 130.0)
        # The re-cut number is unchanged by the disagreement.
        self.assertAlmostEqual(synthetic.offensive_ppp, 1.2, places=6)

    def test_league_aggregates_are_the_mean_over_the_joined_teams(self):
        expected_def = (1.1 + 1.2143700 + 1.0526316) / 3
        self.assertAlmostEqual(self.table.league_defensive_ppp, expected_def, places=6)
        self.assertAlmostEqual(self.table.league_pace, (100.0 + 98.0 + 95.0) / 3, places=6)

    def test_games_played_mismatch_across_pages_drops_the_team_and_flags_it(self):
        trad, opp, adv = three_pages()
        mismatched = teamstats.PageRead(
            page=teamstats.StatPage.TRADITIONAL,
            rows=(
                traditional("Synthetic", 48.0, 120.0),
                traditional("Control", 48.4, 110.0, games=9),
                traditional("Baseline", 48.0, 100.0),
            ),
            source_url=teamstats.StatPage.TRADITIONAL.url,
            retrieved_at=NOW,
            rows_expected=3,
        )
        table = teamstats.recut(mismatched, opp, adv)
        self.assertEqual(len(table.teams), 2)
        self.assertTrue(any("Control" in flag for flag in table.flags))

    def test_a_team_missing_from_one_page_is_flagged(self):
        trad, opp, adv = three_pages()
        _, opp_rows, _ = synth_rows()
        short = teamstats.PageRead(
            page=teamstats.StatPage.OPPONENT,
            rows=opp_rows[:2],
            source_url=teamstats.StatPage.OPPONENT.url,
            retrieved_at=NOW,
            rows_expected=2,
        )
        table = teamstats.recut(trad, short, adv)
        self.assertEqual(len(table.teams), 2)
        self.assertTrue(any("Baseline" in flag for flag in table.flags))
        self.assertTrue(any("TEAMSTATS_PARTIAL_LEAGUE" in flag for flag in table.flags))

    def test_duplicate_team_rows_rejected(self):
        trad, opp, adv = three_pages()
        dupes = teamstats.PageRead(
            page=teamstats.StatPage.TRADITIONAL,
            rows=(traditional("Synthetic", 48.0, 120.0), traditional("Synthetic", 48.0, 120.0)),
            source_url=teamstats.StatPage.TRADITIONAL.url,
            retrieved_at=NOW,
            rows_expected=2,
        )
        with self.assertRaises(teamstats.TeamStatsError) as caught:
            teamstats.recut(dupes, opp, adv)
        self.assertIn("appears more than once", str(caught.exception))

    def test_summary_reports_the_league_state(self):
        summary = self.table.summary()
        self.assertEqual(summary["teams"], 3)
        self.assertEqual(summary["teams_expected"], teamstats.TEAMS_EXPECTED)
        self.assertEqual(summary["teams_failing_a_check"], [])


class MatchupInputsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.table = teamstats.recut(*three_pages())

    def test_possessions_are_the_weighted_mean_of_the_two_paces(self):
        inputs = teamstats.matchup_inputs(self.table, "Synthetic", "Control")
        self.assertAlmostEqual(inputs.possessions, 99.0, places=6)
        self.assertEqual(inputs.pace_rule, "pace_weighted_mean")

    def test_naive_baseline_is_the_sum_of_the_two_scoring_averages(self):
        inputs = teamstats.matchup_inputs(self.table, "Synthetic", "Control")
        self.assertEqual(inputs.scoring_averages, (120.0, 110.0))

    def test_adjustment_moves_efficiency_towards_the_opponents_defence(self):
        inputs = teamstats.matchup_inputs(self.table, "Synthetic", "Control")
        synthetic = self.table.by_team("Synthetic")
        control = self.table.by_team("Control")
        # Control allows 1.214 PPP, worse than the league's 1.122, so Synthetic's
        # offence is adjusted upward; Synthetic allows 1.1, better than league,
        # so Control's offence is adjusted downward.
        self.assertGreater(inputs.ppp_home, synthetic.offensive_ppp)
        self.assertLess(inputs.ppp_away, control.offensive_ppp)

    def test_model_total_against_the_naive_total(self):
        inputs = teamstats.matchup_inputs(self.table, "Synthetic", "Control")
        projection = project_total(
            "synthetic-game",
            inputs.possessions,
            inputs.ppp_home,
            inputs.ppp_away,
            scoring_averages=inputs.scoring_averages,
            pace_rule=inputs.pace_rule,
            adjustment_form=inputs.adjustment_form,
        )
        self.assertAlmostEqual(projection.model_total, 236.55, places=1)
        self.assertAlmostEqual(projection.naive_total, 230.0, places=6)
        self.assertAlmostEqual(projection.naive_minus_model, 230.0 - 236.55, places=1)

    def test_product_over_league_pace_rule_is_available_and_differs(self):
        weighted = teamstats.matchup_inputs(self.table, "Synthetic", "Control")
        product = teamstats.matchup_inputs(
            self.table, "Synthetic", "Control", pace_rule="pace_product_over_league"
        )
        # (100 x 98) / 97.6666667 = 100.3413..., not the 99.0 weighted mean.
        self.assertAlmostEqual(product.possessions, (100.0 * 98.0) / ((100 + 98 + 95) / 3), places=6)
        self.assertNotAlmostEqual(product.possessions, weighted.possessions, places=3)

    def test_missing_team_is_a_refusal_not_a_number(self):
        inputs = teamstats.matchup_inputs(self.table, "Synthetic", "Not In The Pages")
        self.assertIsNone(inputs.possessions)
        self.assertIsNone(inputs.ppp_home)
        self.assertIn("TEAMSTATS_MISSING_TEAM", inputs.status)
        self.assertIn("Not In The Pages", inputs.status)

    def test_unknown_pace_rule_rejected(self):
        with self.assertRaises(teamstats.TeamStatsError):
            teamstats.matchup_inputs(self.table, "Synthetic", "Control", pace_rule="vibes")

    def test_declared_by_caller_rule_points_at_totals(self):
        with self.assertRaises(teamstats.TeamStatsError) as caught:
            teamstats.matchup_inputs(self.table, "Synthetic", "Control", pace_rule="declared-by-caller")
        self.assertIn("engine.totals.project_total", str(caught.exception))

    def test_additive_adjustment_form_is_supported(self):
        inputs = teamstats.matchup_inputs(
            self.table, "Synthetic", "Control", adjustment_form="additive"
        )
        synthetic = self.table.by_team("Synthetic")
        control = self.table.by_team("Control")
        self.assertAlmostEqual(
            inputs.ppp_home,
            synthetic.offensive_ppp + (control.defensive_ppp - self.table.league_defensive_ppp),
            places=9,
        )


if __name__ == "__main__":
    unittest.main()


def _prov_dict() -> dict:
    return {
        "source_id": "synthetic.invalid",
        "source_name": "SYNTHETIC FIXTURE - NOT AN OFFICIAL SOURCE",
        "source_url": "https://www.nba.com/stats/teams/advanced",
        "source_timestamp": "2026-11-15T12:00:00Z",
        "observed_at": "2026-11-16T11:00:00Z",
        "version": "synthetic-1",
        "allowed_use": True,
        "allowed_use_note": "labelled synthetic fixture",
    }


class RowFromDictTest(unittest.TestCase):
    def test_builds_the_row_type_for_the_page(self):
        row = teamstats.row_from_dict("advanced", {
            "team": "Synthetic",
            "games_played": 10,
            "minutes_total": 480.0,
            "pace": 100.0,
            "possessions_total": 1000.0,
            "offensive_rating": 120.0,
            "defensive_rating": 110.0,
            "net_rating": 10.0,
            "provenance": _prov_dict(),
        })
        self.assertIsInstance(row, teamstats.AdvancedRow)

    def test_a_row_without_provenance_is_rejected(self):
        with self.assertRaises(teamstats.TeamStatsError):
            teamstats.row_from_dict("advanced", {"team": "Synthetic"})

    def test_a_naive_timestamp_is_rejected(self):
        payload = _prov_dict()
        payload["observed_at"] = "2026-11-16T11:00:00"
        with self.assertRaises(teamstats.TeamStatsError) as caught:
            teamstats.row_from_dict("advanced", {
                "team": "Synthetic",
                "games_played": 10,
                "minutes_total": 480.0,
                "pace": 100.0,
                "possessions_total": 1000.0,
                "offensive_rating": 120.0,
                "defensive_rating": 110.0,
                "net_rating": 10.0,
                "provenance": payload,
            })
        self.assertIn("UTC offset", str(caught.exception))

    def test_unknown_page_rejected(self):
        with self.assertRaises(teamstats.TeamStatsError):
            teamstats.row_from_dict("boxscores", {"provenance": _prov_dict()})

    def test_wrong_fields_for_the_page_rejected(self):
        with self.assertRaises(teamstats.TeamStatsError):
            teamstats.row_from_dict("advanced", {"team": "Synthetic", "provenance": _prov_dict()})

class TeamStatsCliTest(unittest.TestCase):
    """The subcommand a scheduled job runs; it exits non-zero on a refused read."""

    def _run(self, *argv: str) -> "tuple[int, str]":
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "engine.cli", *argv],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parents[1]),
        )
        return result.returncode, result.stdout + result.stderr

    def _pages(self, **overrides) -> dict:
        trad_rows, opp_rows, adv_rows = synth_rows()
        payload = {
            "retrieved_at": "2026-11-16T12:00:00Z",
            "traditional": [row.__dict__ | {"provenance": _prov_dict()} for row in trad_rows],
            "opponent": [row.__dict__ | {"provenance": _prov_dict()} for row in opp_rows],
            "advanced": [row.__dict__ | {"provenance": _prov_dict()} for row in adv_rows],
            "traditional_rows_expected": 3,
            "opponent_rows_expected": 3,
            "advanced_rows_expected": 3,
        }
        payload.update(overrides)
        return payload

    def test_complete_read_prints_the_league_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pages.json"
            path.write_text(json.dumps(self._pages()), encoding="utf-8")
            code, out = self._run("teamstats", "--pages", str(path))
        self.assertEqual(code, 0, out)
        self.assertIn("league pace", out)
        self.assertIn("Synthetic", out)

    def test_partial_read_is_refused_and_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pages.json"
            path.write_text(json.dumps(self._pages(opponent_chunks_read=1, opponent_chunks_total=2)),
                            encoding="utf-8")
            code, out = self._run("teamstats", "--pages", str(path))
        self.assertEqual(code, 1)
        self.assertIn(teamstats.TEAMSTATS_INCOMPLETE_READ, out)

    def test_json_output_is_parseable(self):
        import json as _json

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pages.json"
            path.write_text(json.dumps(self._pages()), encoding="utf-8")
            code, out = self._run("teamstats", "--pages", str(path), "--json")
        self.assertEqual(code, 0, out)
        parsed = _json.loads(out)
        self.assertEqual(parsed["teams"], 3)
