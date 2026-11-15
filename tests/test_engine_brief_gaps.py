"""Tests for the task-AN modules: every refusal path and every arithmetic path.

Fixtures are synthetic. The only real values used are the two the repo already
publishes as official extractions (the 2026-11-14 results snapshot and the
2026-11-15 standings snapshot); no NBA value is invented in this file, and no test
asserts a number that a source did not print.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.contracts import Provenance as ContractProvenance  # noqa: F401  (documents the gate's home)
from engine.dualestimate import MIN_PAIRS, Pair, compare, disagreement_statistics
from engine.homerate import arena_adjustment, for_ratings, load_and_pin, measure_home_win_rate
from engine.injurystore import NOT_YET_SUBMITTED, InjuryRow, diff_revisions, load_revision, team_for_row
from engine.inputs import NO_INPUT, MissingInput
from engine.luckscore import ONE_POSSESSION_POINTS, expected_close_wins, luck_delta, one_possession_record
from engine.marketprior import NO_AUTHORISATION, Quote, implied_probability, no_vig_pair, prior_or_refusal
from engine.minutesshare import MinutesRow, replacement_share, rotation_availability, top_n_share
from engine.prereg import PreReg, amend, assert_covers, code_hash, register, verify_file
from engine.resultfeed import ResultLine, check_day, check_line, load_results_snapshot, settlement_gate
from engine.schema import Provenance, TeamGame
from engine.seallayer import CRITERIA, TieInputs, resolve_multi_team, resolve_two_team
from engine.travel import Tip, back_to_back, disruption, games_in_nights, rest_hours

REPO = Path(__file__).resolve().parents[1]
SNAP = REPO / "data" / "snapshots"


def tg(game_id: str, team: str, opp: str, pts: float, opp_pts: float, *, date: str, poss=None) -> TeamGame:
    prov = Provenance("https://www.nba.com/game/x", "2026-11-14T00:00:00+00:00", "2026-11-14T00:00:00+00:00")
    return TeamGame(
        record_id=f"{team}-{game_id}",
        game_id=game_id,
        game_date=f"{date}T23:00:00-05:00",
        team=team,
        opponent=opp,
        is_home=True,
        points=pts,
        opp_points=opp_pts,
        possessions=poss,
        provenance=prov,
    )


class ResultFeedTests(unittest.TestCase):
    def line(self, quarters, final, **kw):
        return ResultLine(
            game_id=kw.pop("game_id", "g1"),
            team=kw.pop("team", "AAA"),
            quarters=quarters,
            printed_final=final,
            source_url=kw.pop("source_url", "https://www.nba.com/game/x"),
            source_time=kw.pop("source_time", "2026-11-14"),
            observed_at=kw.pop("observed_at", "2026-11-15T00:00:00+00:00"),
            source_time_precision=kw.pop("precision", "date"),
        )

    def test_quarter_sum_agreement(self):
        self.assertTrue(check_line(self.line([30, 30, 30, 30], 120)).agrees)

    def test_quarter_sum_disagreement_is_not_repaired(self):
        check = check_line(self.line([30, 30, 30, 30], 121))
        self.assertFalse(check.agrees)
        self.assertEqual(check.quarter_sum, 120)
        self.assertIn("disagrees", check.note)

    def test_missing_quarter_blocks_settlement(self):
        check = check_line(self.line([30, 30, None, 30], 120))
        self.assertIsNone(check.agrees)
        self.assertIn("no quarter score invented", check.note)

    def test_short_quarter_list_is_unchecked(self):
        check = check_line(self.line([30, 30], 60))
        self.assertIsNone(check.agrees)
        self.assertIn("not checked, not repaired", check.note)

    def test_source_time_without_offset_is_refused_when_clock_claimed(self):
        with self.assertRaises(MissingInput):
            self.line([30, 30, 30, 30], 120, source_time="2026-11-14T00:00:00", precision="datetime").validated()

    def test_day_gate_settles_only_when_every_line_agrees(self):
        status = check_day(
            [self.line([30, 20, 25, 25], 100), self.line([28, 22, 26, 24], 100, team="BBB")],
            day="2026-11-14",
            last_tip_utc="2026-11-15T02:00:00+00:00",
            retrieved_utc="2026-11-15T03:00:00+00:00",
            source_url="https://www.nba.com/games?date=2026-11-14",
        )
        self.assertEqual(status.status, "SETTLED")
        self.assertEqual(settlement_gate(status)["action"], "SETTLE")
        self.assertEqual(status.feed_delay_hours, None)
        self.assertEqual(status.retrieval_lag_after_tip_hours, 1.0)
        self.assertIn(NO_INPUT, status.reasons()[0])

    def test_day_with_unchecked_line_refuses(self):
        status = check_day(
            [self.line([30, 20, 25, 25], 100), self.line([28, 22, None, 24], 100, team="BBB")],
            day="2026-11-14",
            source_url="https://www.nba.com/games?date=2026-11-14",
        )
        self.assertEqual(status.status, "INCOMPLETE")
        gate = settlement_gate(status)
        self.assertEqual(gate["action"], "REFUSE")

    def test_real_snapshot_settles_ten_of_ten(self):
        status = load_results_snapshot(SNAP / "results-2026-11-14.json", last_tip_utc="2026-11-15T02:00:00+00:00")
        self.assertEqual((status.games, status.lines_checked, status.agreed), (5, 10, 10))
        self.assertEqual(status.status, "SETTLED")


class InjuryStoreTests(unittest.TestCase):
    @property
    def revisions(self):
        return (
            load_revision(SNAP / "injuries-2026-11-15-0600am.cells.json"),
            load_revision(SNAP / "injuries-2026-11-15-0615am.cells.json"),
        )

    def test_row_count_matches_the_printed_file(self):
        old, new = self.revisions
        self.assertEqual(len(old.rows), len(new.rows))
        self.assertEqual(len(old.rows), json.loads((SNAP / "injuries-2026-11-15-0615am.cells.json").read_text())["row_count"])

    def test_consecutive_revisions_show_no_status_change(self):
        old, new = self.revisions
        diff = diff_revisions(old, new, source_url=new.source_url)
        self.assertEqual(diff.counts["status_changes"], 0)
        self.assertEqual(diff.counts["printing_variances"], 1)
        self.assertIn("positional", diff.alignment)
        variance = diff.changes[0]
        self.assertEqual((variance["old"], variance["new"]), ("Embiid, Joel", "Embid, Joel"))
        self.assertIn("not a status change", variance["note"])

    def test_realignment_when_row_counts_differ_is_not_a_status_change(self):
        a = InjuryRow("11/15", "7:00", "X@Y", "Y", "One, A", "Out", "Illness")
        b = InjuryRow("11/15", "7:00", "X@Y", "Y", "One, A", "Out", "Illness")
        c = InjuryRow("11/15", "7:00", "X@Y", "Y", "Two, B", "Questionable", "Knee")
        from engine.injurystore import InjuryRevision

        old = InjuryRevision("6:00 AM ET", "hdr", "https://www.nba.com/x", "2026-11-15T10:00:00+00:00", (a, b))
        new = InjuryRevision("6:15 AM ET", "hdr", "https://www.nba.com/x", "2026-11-15T10:15:00+00:00", (b, c))
        diff = diff_revisions(old, new)
        self.assertEqual(diff.counts["status_changes"], 0)
        kinds = {ch["kind"] for ch in diff.changes}
        self.assertTrue(kinds <= {"ADDED_OR_REALIGNED", "REMOVED_OR_REALIGNED"})

    def test_unaligned_row_refuses_team_attribution(self):
        row = InjuryRow("11/15", "7:00", "", "", "Sexton, Collin", "Questionable", "Face")
        with self.assertRaises(MissingInput):
            team_for_row(row)
        self.assertEqual(team_for_row(row, [("Boston", 0)]), "Boston")

    def test_not_yet_submitted_is_a_reporting_state(self):
        row = InjuryRow("11/16", "7:00", "A@B", "A", "", "", NOT_YET_SUBMITTED)
        self.assertTrue(row.is_reporting_state)
        self.assertEqual(row.as_dict()["player"], "")

    def test_diff_rows_always_end_with_the_official_link(self):
        old, new = self.revisions
        diff = diff_revisions(old, new, source_url=new.source_url)
        for row in diff.as_rows():
            self.assertTrue(row[-1].startswith("https://"))


class PreRegTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "prereg.jsonl"
        self.store = PreReg(self.path)
        self.hash = code_hash([REPO / "engine" / "homerate.py"])

    def tearDown(self):
        self.tmp.cleanup()

    def test_registration_is_append_only(self):
        register(self.store, run_id="r1", cycle="2026-11-15-am", code_sha256=self.hash, registered_at="2026-11-15T05:00:00+00:00")
        with self.assertRaises(MissingInput):
            register(self.store, run_id="r1", cycle="2026-11-15-am", code_sha256=self.hash)
        entry = amend(self.store, supersedes="r1", note="hash corrected", code_sha256="0" * 64)
        self.assertEqual(entry.supersedes, "r1")
        report = verify_file(self.store)
        self.assertEqual((report["entries"], report["amendments"]), (2, 1))

    def test_run_must_be_covered_by_an_earlier_registration(self):
        with self.assertRaises(MissingInput):
            assert_covers(self.store, run_id="nope", code_sha256=self.hash, run_started_at="2026-11-15T06:00:00+00:00")
        register(self.store, run_id="r1", cycle="c", code_sha256=self.hash, registered_at="2026-11-15T06:30:00+00:00")
        with self.assertRaises(MissingInput):
            assert_covers(self.store, run_id="r1", code_sha256=self.hash, run_started_at="2026-11-15T06:00:00+00:00")
        with self.assertRaises(MissingInput):
            assert_covers(self.store, run_id="r1", code_sha256="f" * 64, run_started_at="2026-11-15T07:00:00+00:00")
        self.assertEqual(
            assert_covers(self.store, run_id="r1", code_sha256=self.hash, run_started_at="2026-11-15T07:00:00+00:00").run_id,
            "r1",
        )

    def test_hash_is_over_content_not_order_of_mtime(self):
        again = code_hash([REPO / "engine" / "homerate.py"])
        self.assertEqual(again, self.hash)
        self.assertNotEqual(again, code_hash([REPO / "engine" / "travel.py"]))


class SealLayerTests(unittest.TestCase):
    def test_first_criterion_decides(self):
        a = TieInputs("A", head_to_head=0.6, source_url="https://www.nba.com/standings")
        b = TieInputs("B", head_to_head=0.4)
        res = resolve_two_team(a, b)
        self.assertTrue(res.resolved)
        self.assertEqual(res.higher, "A")
        self.assertEqual(len(res.criteria), 1)

    def test_missing_input_stops_the_chain(self):
        a = TieInputs("A", head_to_head=0.6, own_conference_pct=0.5, source_url="https://www.nba.com/standings")
        b = TieInputs("B", head_to_head=0.6, own_conference_pct=0.7)
        res = resolve_two_team(a, b)
        self.assertFalse(res.resolved)
        self.assertIn("same_division", res.reason)
        self.assertEqual(res.stopped_at, 1)

    def test_zero_is_a_value_not_an_absence(self):
        a = TieInputs("A", head_to_head=0.0, same_division=False, own_division_pct=0.0, own_conference_pct=0.0,
                      eligible_own_conference_pct=0.0, eligible_other_conference_pct=0.0, point_differential=-12.0,
                      source_url="https://www.nba.com/standings")
        b = TieInputs("B", head_to_head=0.0, same_division=False, own_division_pct=0.0, own_conference_pct=0.0,
                      eligible_own_conference_pct=0.0, eligible_other_conference_pct=0.0, point_differential=3.0)
        res = resolve_two_team(a, b)
        self.assertEqual(res.higher, "B")
        self.assertEqual([c.name for c in res.criteria], list(CRITERIA)[:7])

    def test_multi_team_peels_and_refuses_without_inputs(self):
        clubs = [
            TieInputs("A", head_to_head=0.7, source_url="https://www.nba.com/standings"),
            TieInputs("B", head_to_head=0.5),
            TieInputs("C", head_to_head=0.3),
        ]
        out = resolve_multi_team(clubs)
        self.assertEqual(out["ordered"], [["A"]])
        self.assertIn("same_division", out["reason"])
        with self.assertRaises(MissingInput):
            resolve_multi_team(clubs[:2])


class DualEstimateTests(unittest.TestCase):
    def test_band_assignment_is_the_published_constant(self):
        self.assertEqual(compare(Pair("L1", "v1", 0.55, 0.51)).band, "SMALL (2-5pt)")
        self.assertEqual(compare(Pair("L2", "v1", 0.55, 0.535)).band, "AGREE (<=2pt)")
        self.assertEqual(compare(Pair("L3", "v1", 0.62, 0.51)).band, "LARGE (>10pt)")
        self.assertEqual(compare(Pair("L4", "v1", 0.57, 0.51)).band, "MEDIUM (5-10pt)")

    def test_missing_market_refuses(self):
        with self.assertRaises(MissingInput):
            compare(Pair("L5", "v1", 0.5, None))

    def test_small_sample_reports_counts_without_a_mean(self):
        pairs = [Pair(f"L{i}", "v1", 0.5 + 0.01 * i, 0.5) for i in range(3)]
        stats = disagreement_statistics(pairs)
        self.assertEqual(stats["mean_absolute_difference"], NO_INPUT)
        self.assertEqual(sum(stats["bands"].values()), 3)
        self.assertIn("at least 10", stats["mean_refusal"])

    def test_large_sample_computes_a_mean(self):
        pairs = [Pair(f"L{i}", "v1" if i % 2 else "v2", 0.5 + 0.011 * (i % 3), 0.5) for i in range(MIN_PAIRS)]
        stats = disagreement_statistics(pairs, source_url="https://www.nba.com/stats/teams/traditional")
        self.assertNotEqual(stats["mean_absolute_difference"], NO_INPUT)
        self.assertEqual(set(stats["by_variant"]), {"v1", "v2"})
        self.assertEqual(stats["no_market"], 0)


class HomeRateTests(unittest.TestCase):
    def test_measured_rate_from_the_official_extraction(self):
        payload = json.loads((SNAP / "standings-2026-11-15.json").read_text())
        rate, missing = measure_home_win_rate(payload["rows"], source_url=payload["source_url"])
        self.assertEqual((rate.home_wins, rate.home_losses, rate.home_games), (99, 88, 187))
        self.assertEqual(round(rate.rate, 4), 0.5294)
        self.assertEqual((rate.neutral_wins, rate.neutral_losses), (1, 1))
        self.assertEqual(missing, 0)

    def test_pin_conversion_is_the_inverse_of_the_models_win_probability(self):
        from engine.ratings import win_probability

        pin = load_and_pin(SNAP / "standings-2026-11-15.json")
        self.assertAlmostEqual(win_probability(pin.points), pin.rate, places=4)

    def test_the_conversion_is_delegated_not_reimplemented(self):
        """IR-T1 guard: homerate must call ratings' conversion, not duplicate it."""
        import inspect

        from engine import homerate, ratings

        source = inspect.getsource(homerate.pin_home_advantage)
        self.assertIn("home_advantage_from_win_rate", source)
        self.assertNotIn("normal_quantile", source)
        self.assertTrue(hasattr(ratings, "home_advantage_from_win_rate"))

    def test_gate_blocks_an_unregistered_calibration(self):
        pin = load_and_pin(SNAP / "standings-2026-11-15.json")
        with self.assertRaises(MissingInput):
            for_ratings(pin, pre_registered=False, rights_cleared=True)
        with self.assertRaises(MissingInput):
            for_ratings(pin, pre_registered=True, rights_cleared=False)
        from engine.ratings import home_advantage_from_win_rate

        expected = round(home_advantage_from_win_rate(pin.rate, 12.0), 4)
        self.assertEqual(for_ratings(pin, pre_registered=True, rights_cleared=True), expected)

    def test_arena_feature_is_refused_not_fitted(self):
        out = arena_adjustment("Madison Square Garden")
        self.assertEqual(out["status"], "REFUSED")
        self.assertIsNone(out["adjustment_points"])


class LuckTests(unittest.TestCase):
    def setUp(self):
        self.games = [
            tg("g1", "MIL", "DET", 100, 99, date="2026-11-01"),
            tg("g2", "MIL", "DET", 100, 102, date="2026-11-03"),
            tg("g3", "MIL", "DET", 110, 90, date="2026-11-05"),
            tg("g4", "MIL", "DET", 101, 100, date="2026-11-07", poss=96.0),
        ]

    def test_window_is_what_exists_not_a_padded_ten(self):
        rec = one_possession_record(self.games, "MIL")
        self.assertEqual((rec.games_used, rec.close_games, rec.record), (4, 3, "2-1"))
        self.assertEqual(rec.one_possession_value, ONE_POSSESSION_POINTS)
        self.assertIn("made field goal", rec.possessions_basis)

    def test_no_baseline_is_printed_as_no_baseline(self):
        rec = one_possession_record(self.games, "MIL")
        out = luck_delta(rec, None)
        self.assertEqual(out["expected_close_wins"], "[NO BASELINE]")
        self.assertEqual(out["verdict"], "NO INPUT")

    def test_within_chance_uses_the_exact_binomial_band(self):
        rec = one_possession_record(self.games, "MIL")
        out = luck_delta(rec, expected_close_wins([0.5, 0.5, 0.5]))
        self.assertEqual(out["delta"], 0.5)
        self.assertEqual(out["band"], "0-2")
        self.assertEqual(out["verdict"], "WITHIN CHANCE")

    def test_team_absent_from_the_feed_refuses(self):
        with self.assertRaises(MissingInput):
            one_possession_record(self.games, "CHI")


class TravelTests(unittest.TestCase):
    def test_rest_and_back_to_back_from_printed_tips(self):
        prev = Tip("g1", "CHI", "2026-11-14T01:00:00+00:00")
        nxt = Tip("g2", "CHI", "2026-11-16T00:00:00+00:00")
        self.assertEqual(rest_hours(prev, nxt), 47.0)
        flag = back_to_back(prev, nxt, source_url="https://www.nba.com/schedule")
        self.assertTrue(flag.is_back_to_back)
        self.assertFalse(flag.short_rest)

    def test_naive_tip_without_offset_is_refused(self):
        with self.assertRaises(MissingInput):
            rest_hours(Tip("g1", "CHI", "2026-11-14T01:00:00"), Tip("g2", "CHI", "2026-11-16T00:00:00+00:00"))

    def test_partial_slate_refuses_a_night_count(self):
        tips = [Tip("g1", "CHI", "2026-11-15T00:00:00+00:00")]
        out = games_in_nights(tips, team="CHI", window_nights=4, anchor="2026-11-18")
        self.assertEqual(out["status"], "REFUSED")
        self.assertIsNone(out["games"])
        full = [Tip(f"g{i}", "CHI", f"2026-11-{15 + i}T00:00:00+00:00") for i in range(4)]
        out = games_in_nights(full, team="NYK", window_nights=4, anchor="2026-11-18")
        self.assertEqual((out["games"], out["fifth_in_four"]), (0, False))

    def test_ground_stop_flag_carries_no_penalty(self):
        out = disruption(
            team="CHI",
            notice_url="https://www.nba.com/news/example-ground-stop",
            notice_time_utc="2026-11-13T22:00:00+00:00",
            game_id="g2",
            label="nationwide ground stop",
            affected_game_ids=["g2"],
        ).as_dict()
        self.assertEqual(out["penalty_points"], 0.0)
        self.assertFalse(out["penalty_allowed"])
        self.assertIn("no penalty value", out["note"])


class MinutesShareTests(unittest.TestCase):
    def setUp(self):
        rows = [MinutesRow("BOS", "Player 1", 36.0), MinutesRow("BOS", "Player 2", 34.0)]
        rows += [MinutesRow("BOS", f"Player {i}", 30.0 - i) for i in range(3, 9)]
        rows += [MinutesRow("BOS", f"Player {i}", 12.0) for i in range(9, 13)]
        rows.append(MinutesRow("BOS", "TEAM", 240.0))
        self.rows = rows

    def test_top8_share_arithmetic(self):
        out = top_n_share(self.rows, "BOS", source_url="https://www.nba.com/game/x")
        self.assertEqual(out["team_minutes"], 240.0)
        self.assertEqual(out["top_minutes"], 36 + 34 + 27 + 26 + 25 + 24 + 23 + 22)
        self.assertAlmostEqual(out["share"], out["top_minutes"] / 240.0, places=4)

    def test_missing_team_total_refuses_a_synthesised_denominator(self):
        rows = [r for r in self.rows if r.player != "TEAM"]
        with self.assertRaises(MissingInput):
            top_n_share(rows, "BOS")

    def test_fewer_than_eight_lines_refuses(self):
        with self.assertRaises(MissingInput):
            top_n_share([MinutesRow("BOS", "Player 1", 30.0), MinutesRow("BOS", "TEAM", 240.0)], "BOS")

    def test_replacement_share_excludes_unattributed_and_unaligned(self):
        unavailable = [
            InjuryRow("11/15", "7:00", "X@BOS", "BOS", "Player 1", "Out", "Ankle"),
            InjuryRow("11/15", "7:00", "X@BOS", "BOS", "Rookie, New", "Out", "League minimum"),
            InjuryRow("11/15", "7:00", "", "", "Sexton, Collin", "Questionable", "Face"),
        ]
        out = replacement_share(unavailable, self.rows, "BOS")
        self.assertEqual(out["replacement_minutes"], 36.0)
        self.assertEqual(out["unattributed_players"], ["Rookie, New"])
        self.assertEqual(out["rows_excluded_for_missing_team_cell"], 1)
        self.assertAlmostEqual(out["replacement_share"], 36.0 / 240.0, places=4)

    def test_rotation_does_not_remove_unresolved_rows(self):
        unavailable = [
            InjuryRow("11/15", "7:00", "X@BOS", "BOS", "Player 1", "Out", "Ankle"),
            InjuryRow("11/15", "7:00", "", "", "Player 2", "Out", "Knee"),
        ]
        out = rotation_availability("BOS", roster_minutes=self.rows, unavailable=unavailable)
        self.assertEqual(out["removed"], ["Player 1"])
        self.assertEqual(out["available_players"], 11)


class MarketPriorTests(unittest.TestCase):
    def quote(self, side, american, **kw):
        return Quote(
            leg_id=kw.pop("leg_id", "g1"),
            side=side,
            american_odds=american,
            source_url=kw.pop("source_url", "https://www.nba.com/lineups"),
            source_time="2026-11-15T10:00:00+00:00",
            observed_at="2026-11-15T10:05:00+00:00",
            **kw,
        )

    def test_price_conversion_and_vig_normalisation(self):
        home, away = self.quote("HOME", -150.0), self.quote("AWAY", 130.0)
        pair = no_vig_pair(home, away)
        self.assertAlmostEqual(pair["raw_home"], 0.6, places=4)
        self.assertGreater(pair["overround"], 0.0)
        self.assertAlmostEqual(pair["novig_home"] + pair["novig_away"], 1.0, places=9)

    def test_sides_summing_under_one_are_refused(self):
        with self.assertRaises(MissingInput):
            no_vig_pair(self.quote("HOME", 100.0), self.quote("AWAY", 100.0))

    def test_no_price_no_probability(self):
        with self.assertRaises(MissingInput):
            implied_probability(Quote("g9", "HOME", source_url="https://www.nba.com/lineups"))

    def test_gate_blocks_the_prior_without_authorisation(self):
        home, away = self.quote("HOME", -150.0), self.quote("AWAY", 130.0)
        out = prior_or_refusal(
            0.58, [home, away], weight=0.5, rights_cleared=False, pre_registered=True
        )
        self.assertEqual(out["surface"], "model only")
        self.assertEqual(out["priors"], {})
        self.assertEqual(out["refusals"][0]["status"], NO_AUTHORISATION)
        self.assertNotIn("blended_p", json.dumps(out["refusals"]))


class IntegrationShapeTests(unittest.TestCase):
    def test_no_module_imports_a_third_party_package(self):
        import re

        for name in (
            "inputs.py", "resultfeed.py", "injurystore.py", "prereg.py", "seallayer.py", "dualestimate.py",
            "homerate.py", "luckscore.py", "travel.py", "minutesshare.py", "marketprior.py",
        ):
            text = (REPO / "engine" / name).read_text()
            for mod in re.findall(r"^(?:from|import) ([\w.]+)", text, re.M):
                if mod.startswith("."):  # intra-engine imports are not third party
                    continue
                top = mod.split(".")[0]
                self.assertIn(
                    top,
                    {"__future__", "json", "re", "math", "dataclasses", "datetime", "pathlib", "typing", "engine", "hashlib", "collections"},
                    f"{name} imports {mod}",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
