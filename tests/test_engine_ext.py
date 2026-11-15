"""Unit tests for the NBA4 engine extensions (stdlib unittest).

Fixtures here are SYNTHETIC (host synthetic.invalid) and exist only to test
mechanics.  No NBA value, player name, team name, market price or result
appears in this file.

Covers the eighth-cycle additions:
  * two independent estimators, their disagreement headline and the blend
    underneath (engine.estimators);
  * the market-anchored prior weighted by measured out-of-sample log loss
    (engine.marketprior);
  * luck as a per-team z-score with a noise band (engine.luck);
  * minutes redistribution and the top-eight rotation (engine.rotation);
  * rest, back-to-back, 3-in-4 and travel distance (engine.travel);
  * final-score verification, settlement and the settlement stamp
    (engine.results);
  * the tamper-evident seal chain (engine.seal);
  * frozen strategy pre-registration (engine.prereg);
  * consecutive injury-report diffing (engine.injury_diff).

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.estimators import (  # noqa: E402
    OutcomeEstimator,
    PppEstimator,
    blend_estimators,
    disagreement,
    home_win_rate_interval,
    implied_home_advantage_points,
    measured_home_win_rate,
    pair_games,
)
from engine.injury_diff import InjuryRow, diff_reports  # noqa: E402
from engine.luck import (  # noqa: E402
    DEFAULT_MIN_EXPOSURE,
    NOISE_BAND_Z,
    check_strategy_luck,
    is_within_noise_band,
    luck_zscore,
    team_luck_zscores,
    teams_outside_noise_band,
)
from engine.marketprior import (  # noqa: E402
    blend_probability,
    blend_with_market,
    expit,
    logit,
)
from engine.prereg import (  # noqa: E402
    Preregistration,
    check_first_bet,
    freeze,
    load_preregistration,
    verify_preregistration,
)
from engine.results import (  # noqa: E402
    SETTLEMENT_RULES,
    GameResult,
    settle_pick,
    settlement_stamp,
    verify_final,
)
from engine.rotation import (  # noqa: E402
    TOP_EIGHT,
    build_rotation,
    minutes_shares,
    redistribute_when_out,
    top_eight_shares,
)
from engine.schema import Provenance, SlateGame, TeamGame  # noqa: E402
from engine.seal import (  # noqa: E402
    GENESIS_HASH,
    canonical_hash,
    seal_record,
    verify_chain,
    verify_published_hash,
)
from engine.travel import (  # noqa: E402
    Arena,
    compute_load,
    haversine_miles,
    load_arenas,
)

BASE = datetime(2026, 11, 1, 0, 0, tzinfo=timezone.utc)
PROV = Provenance("https://synthetic.invalid/fixture", BASE.isoformat(), BASE.isoformat())


def _team_game(game_id, date, team, opponent, is_home, points, opp_points, possessions=None):
    return TeamGame(
        record_id=f"{game_id}:{team}",
        game_id=game_id,
        game_date=date,
        team=team,
        opponent=opponent,
        is_home=is_home,
        points=float(points),
        opp_points=float(opp_points),
        possessions=possessions,
        provenance=PROV,
    )


def _season(team_a="SYNTH-A", team_b="SYNTH-B", n=10, start=BASE, seed=0):
    """A synthetic season: team A wins more at home than on the road."""
    games = []
    for i in range(n):
        day = start + timedelta(days=i * 2)
        date = day.isoformat()
        gid = f"g{i:03d}"
        a_home = i % 2 == 0
        margin = 6.0 + (i % 3) - (0 if a_home else 4)
        if a_home:
            games.append(_team_game(gid, date, team_a, team_b, True, 110 + margin, 100, 99.0 + seed))
            games.append(_team_game(gid, date, team_b, team_a, False, 100, 110 + margin, 99.0 + seed))
        else:
            games.append(_team_game(gid, date, team_a, team_b, False, 105 + margin, 100, 101.0 + seed))
            games.append(_team_game(gid, date, team_b, team_a, True, 100, 105 + margin, 101.0 + seed))
    return games


class TestEstimators(unittest.TestCase):
    def test_pair_games_reduces_to_one_row_per_game(self):
        games = _season(n=4)
        pairs = pair_games(games)
        self.assertEqual(len(pairs), 4)
        self.assertTrue(all(p.home_team == "SYNTH-A" or p.home_team == "SYNTH-B" for p in pairs))

    def test_measured_home_win_rate(self):
        pairs = pair_games(_season(n=10))
        rate = measured_home_win_rate(pairs)
        self.assertIsNotNone(rate)
        self.assertTrue(0.0 <= rate <= 1.0)

    def test_measured_home_win_rate_is_none_without_games(self):
        self.assertIsNone(measured_home_win_rate([]))

    def test_home_win_rate_interval_brackets_the_estimate(self):
        lo, hi = home_win_rate_interval(0.6, 100)
        self.assertLess(lo, 0.6)
        self.assertGreater(hi, 0.6)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)

    def test_home_advantage_is_pinned_to_the_measured_rate(self):
        value, low, high, notes = implied_home_advantage_points(0.6, 12.0, n_home_games=100)
        self.assertIsNotNone(value)
        self.assertGreater(value, 0.0)
        self.assertLess(low, value)
        self.assertGreater(high, value)
        self.assertTrue(any("pinned" in n for n in notes))

    def test_home_advantage_undefined_without_a_measured_rate(self):
        value, low, high, notes = implied_home_advantage_points(None, 12.0)
        self.assertIsNone(value)
        self.assertIsNone(low)
        self.assertIsNone(high)

    def test_ppp_estimator_uses_measured_pace_and_refuses_without_games(self):
        est = PppEstimator()
        out = est.estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40), 12.0,
                            measured_home_rate=0.6)
        self.assertIsNotNone(out.expected_home_margin)
        self.assertIsNotNone(out.home_win_probability)
        self.assertTrue(any("pace" in n for n in out.notes))
        empty = est.estimate([], "SYNTH-A", "SYNTH-B", BASE, 12.0, measured_home_rate=0.6)
        self.assertIsNone(empty.expected_home_margin)

    def test_outcome_estimator_refuses_without_a_measured_home_rate(self):
        est = OutcomeEstimator()
        out = est.estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40), 12.0)
        self.assertIsNone(out.expected_home_margin)
        self.assertTrue(any("pinned" in n or "home" in n for n in out.notes))

    def test_outcome_estimator_produces_a_probability(self):
        est = OutcomeEstimator()
        out = est.estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40), 12.0,
                           measured_home_rate=0.6)
        self.assertIsNotNone(out.home_win_probability)
        self.assertTrue(0.0 < out.home_win_probability < 1.0)

    def test_disagreement_is_the_headline(self):
        a = PppEstimator().estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40),
                                    12.0, measured_home_rate=0.6)
        b = OutcomeEstimator().estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40),
                                        12.0, measured_home_rate=0.6)
        gap = disagreement(a, b)
        self.assertTrue(gap.is_measurable)
        self.assertIsNotNone(gap.z_score)
        self.assertIn("gap", gap.headline)

    def test_disagreement_is_blank_when_one_estimator_is_blank(self):
        a = PppEstimator().estimate([], "A", "B", BASE, 12.0, measured_home_rate=0.6)
        b = OutcomeEstimator().estimate([], "A", "B", BASE, 12.0, measured_home_rate=0.6)
        gap = disagreement(a, b)
        self.assertFalse(gap.is_measurable)
        self.assertIsNone(gap.margin_gap)

    def test_blend_needs_measured_log_loss(self):
        a = PppEstimator().estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40),
                                    12.0, measured_home_rate=0.6)
        b = OutcomeEstimator().estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40),
                                        12.0, measured_home_rate=0.6)
        gap = disagreement(a, b)
        blended, wa, wb, notes = blend_estimators(gap, None, 0.69)
        self.assertIsNone(blended)
        self.assertIsNone(wa)
        self.assertTrue(any("log loss" in n for n in notes))
        blended, wa, wb, notes = blend_estimators(gap, 0.60, 0.72)
        self.assertIsNotNone(blended)
        self.assertAlmostEqual(wa + wb, 1.0, places=9)
        self.assertGreater(wa, wb)

    def test_blend_rejects_non_positive_log_loss(self):
        a = PppEstimator().estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40),
                                    12.0, measured_home_rate=0.6)
        b = OutcomeEstimator().estimate(_season(n=12), "SYNTH-A", "SYNTH-B", BASE + timedelta(days=40),
                                        12.0, measured_home_rate=0.6)
        gap = disagreement(a, b)
        with self.assertRaises(ValueError):
            blend_estimators(gap, 0.0, 0.7)


class TestMarketPrior(unittest.TestCase):
    def test_weights_follow_the_lower_log_loss(self):
        blend = blend_with_market(110.0, 108.0, 0.60, 0.75)
        self.assertTrue(blend.is_blended)
        self.assertGreater(blend.weight_model, blend.weight_market)
        self.assertAlmostEqual(blend.weight_model + blend.weight_market, 1.0, places=9)
        self.assertAlmostEqual(blend.blended_value, 110 * blend.weight_model + 108 * blend.weight_market)

    def test_no_blend_without_measured_log_loss(self):
        blend = blend_with_market(110.0, 108.0, None, 0.75)
        self.assertIsNone(blend.blended_value)
        self.assertIsNone(blend.weight_model)

    def test_no_blend_without_the_market_line(self):
        blend = blend_with_market(110.0, None, 0.6, 0.75)
        self.assertIsNone(blend.blended_value)

    def test_probability_blend_uses_log_odds(self):
        blend = blend_probability(0.60, 0.50, 0.60, 0.75)
        self.assertIsNotNone(blend.blended_value)
        self.assertTrue(0.0 < blend.blended_value < 1.0)
        self.assertAlmostEqual(expit(logit(0.5)), 0.5, places=9)

    def test_equal_weights_give_the_midpoint(self):
        blend = blend_with_market(110.0, 108.0, 0.70, 0.70)
        self.assertAlmostEqual(blend.blended_value, 109.0, places=9)


class TestLuck(unittest.TestCase):
    def test_luck_zscore(self):
        self.assertAlmostEqual(luck_zscore(100.0, 110.0, 10.0), 1.0)
        self.assertIsNone(luck_zscore(None, 110.0, 10.0))
        self.assertIsNone(luck_zscore(100.0, 110.0, None))
        with self.assertRaises(ValueError):
            luck_zscore(100.0, 110.0, 0.0)

    def test_team_luck_zscores_and_band(self):
        z = team_luck_zscores({"A": 100.0}, {"A": 115.0}, {"A": 10.0})
        self.assertAlmostEqual(z["A"], 1.5)
        self.assertFalse(is_within_noise_band(z["A"], NOISE_BAND_Z))
        self.assertIn("A", teams_outside_noise_band(z, NOISE_BAND_Z))

    def test_strategy_leaning_on_a_lucky_team_is_refused(self):
        check = check_strategy_luck({"A": 0.8, "B": 0.2}, {"A": 2.5, "B": 0.1})
        self.assertEqual(check.verdict, "REFUSE")
        self.assertTrue(check.refused)
        self.assertIn("A", check.offending_teams)

    def test_strategy_inside_the_band_is_publishable(self):
        check = check_strategy_luck({"A": 0.8, "B": 0.2}, {"A": 0.4, "B": 0.1})
        self.assertEqual(check.verdict, "PUBLISH")

    def test_unmeasured_luck_is_not_publishable(self):
        check = check_strategy_luck({"A": 0.8, "B": 0.2}, {"B": 0.1})
        self.assertEqual(check.verdict, "NOT MEASURABLE")

    def test_minimum_exposure_is_respected(self):
        # A team outside the band but with a small exposure does not block.
        check = check_strategy_luck({"A": 0.9, "B": 0.1}, {"A": 0.2, "B": 3.0},
                                    min_exposure=DEFAULT_MIN_EXPOSURE)
        self.assertEqual(check.verdict, "PUBLISH")


class TestRotation(unittest.TestCase):
    def _minutes(self):
        return {f"P{i}": 30.0 - i for i in range(12)}

    def test_minutes_shares_sum_to_one(self):
        shares = minutes_shares(self._minutes())
        self.assertAlmostEqual(sum(s.share for s in shares), 1.0, places=9)
        self.assertEqual(shares[0].player, "P0")

    def test_top_eight_and_replacement_pool(self):
        top, pool = top_eight_shares(self._minutes())
        self.assertEqual(len(top), TOP_EIGHT)
        self.assertEqual(len(pool), 12 - TOP_EIGHT)

    def test_redistribution_equal_split(self):
        rot = build_rotation("T", self._minutes())
        out = redistribute_when_out(rot, "P0", method="equal")
        self.assertTrue(out["measurable"])
        added = dict(out["minutes_added"])
        self.assertEqual(len(added), 4)
        self.assertAlmostEqual(sum(added.values()), rot.minutes_of("P0"), places=6)
        self.assertAlmostEqual(max(added.values()), min(added.values()), places=9)

    def test_redistribution_proportional_split(self):
        rot = build_rotation("T", self._minutes())
        out = redistribute_when_out(rot, "P0", method="proportional")
        added = dict(out["minutes_added"])
        self.assertAlmostEqual(sum(added.values()), rot.minutes_of("P0"), places=6)
        # The player with the larger current share receives more minutes.
        pool = {p.player: p.share for p in rot.replacements}
        best = max(added, key=lambda k: added[k])
        self.assertEqual(pool[best], max(pool.values()))

    def test_redistribution_refuses_an_unknown_player(self):
        rot = build_rotation("T", self._minutes())
        out = redistribute_when_out(rot, "NOT-A-PLAYER")
        self.assertFalse(out["measurable"])

    def test_redistribution_rejects_an_unknown_method(self):
        rot = build_rotation("T", self._minutes())
        with self.assertRaises(ValueError):
            redistribute_when_out(rot, "P0", method="random")

    def test_share_cap_leaves_minutes_unplaced(self):
        rot = build_rotation("T", self._minutes())
        out = redistribute_when_out(rot, "P0", method="equal", max_share=0.085)
        self.assertGreater(out["unplaced_minutes"], 0.0)
        for share in out["shares"]:
            self.assertLessEqual(share.share, 0.085 + 1e-9)

    def test_minutes_are_conserved_when_a_cap_binds(self):
        rot = build_rotation("T", self._minutes())
        out = redistribute_when_out(rot, "P0", method="equal", max_share=0.085)
        placed = sum(m for _, m in out["minutes_added"])
        self.assertAlmostEqual(
            placed + out["unplaced_minutes"], rot.minutes_of("P0"), places=6
        )

    def test_minutes_are_conserved_without_a_cap(self):
        rot = build_rotation("T", self._minutes())
        out = redistribute_when_out(rot, "P0", method="proportional")
        placed = sum(m for _, m in out["minutes_added"])
        self.assertAlmostEqual(placed, rot.minutes_of("P0"), places=6)
        self.assertAlmostEqual(out["unplaced_minutes"], 0.0, places=9)


class TestTravel(unittest.TestCase):
    def test_haversine_known_distance(self):
        # Los Angeles -> New York is about 2445 miles great-circle.
        d = haversine_miles(34.0522, -118.2437, 40.7128, -74.0060)
        self.assertTrue(2400 < d < 2500)

    def test_haversine_is_zero_for_identical_points(self):
        self.assertAlmostEqual(haversine_miles(41.5, -87.5, 41.5, -87.5), 0.0, places=9)

    def test_load_arenas_drops_unverified_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "arenas.json"
            path.write_text(json.dumps({
                "arenas": [
                    {"team": "A", "venue": "V", "city": "C", "latitude": 41.5,
                     "longitude": -87.5, "source_url": "https://synthetic.invalid/a",
                     "verified": True},
                    {"team": "B", "venue": "W", "city": "D", "latitude": 40.0,
                     "longitude": -75.0, "source_url": "https://synthetic.invalid/b",
                     "verified": False},
                    {"team": "C", "venue": "X", "city": "E", "latitude": None,
                     "longitude": None, "source_url": "", "verified": False},
                ]
            }), encoding="utf-8")
            arenas = load_arenas(path)
        self.assertTrue(arenas["A"].has_coordinates)
        self.assertFalse(arenas["B"].has_coordinates)
        self.assertFalse(arenas["C"].has_coordinates)

    def _games(self):
        t0 = datetime(2026, 11, 1, 19, 0, tzinfo=timezone.utc)
        return [
            SlateGame("g1", "g1", (t0).isoformat(), "SYNTH-A", "SYNTH-B", PROV),
            SlateGame("g2", "g2", (t0 + timedelta(days=1)).isoformat(), "SYNTH-A", "SYNTH-B", PROV),
            SlateGame("g3", "g3", (t0 + timedelta(days=2)).isoformat(), "SYNTH-A", "SYNTH-B", PROV),
        ]

    def test_rest_back_to_back_and_three_in_four(self):
        arenas = {
            "SYNTH-A": Arena("SYNTH-A", "VA", "C", 41.5, -87.5, "https://synthetic.invalid/a"),
            "SYNTH-B": Arena("SYNTH-B", "VB", "D", 40.0, -75.0, "https://synthetic.invalid/b"),
        }
        load = compute_load(self._games(), arenas)
        second = load["g2:SYNTH-A"]
        self.assertAlmostEqual(second.rest_days, 1.0, places=6)
        self.assertFalse(second.is_back_to_back)
        self.assertEqual(second.games_in_next_four_days, 2)
        third = load["g3:SYNTH-A"]
        self.assertEqual(third.games_in_next_four_days, 1)

    def test_travel_distance_is_measured_when_coordinates_are_sourced(self):
        arenas = {
            "SYNTH-A": Arena("SYNTH-A", "VA", "C", 41.5, -87.5, "https://synthetic.invalid/a"),
            "SYNTH-B": Arena("SYNTH-B", "VB", "D", 40.0, -75.0, "https://synthetic.invalid/b"),
        }
        load = compute_load(self._games(), arenas)
        self.assertIsNotNone(load["g2:SYNTH-B"].travel_miles)
        self.assertGreater(load["g2:SYNTH-B"].travel_miles, 0.0)

    def test_travel_is_blank_without_sourced_coordinates(self):
        arenas = {
            "SYNTH-A": Arena("SYNTH-A", "VA", "C", None, None, ""),
            "SYNTH-B": Arena("SYNTH-B", "VB", "D", None, None, ""),
        }
        load = compute_load(self._games(), arenas)
        self.assertIsNone(load["g2:SYNTH-B"].travel_miles)
        self.assertTrue(load["g2:SYNTH-B"].notes)


class TestResults(unittest.TestCase):
    def _result(self, **kw):
        payload = dict(
            record_id="r1", game_id="g1", game_date="2026-11-14T00:00:00+00:00",
            home_team="H", away_team="A", home_points=110, away_points=104,
            quarter_scores=((30, 28), (28, 24), (30, 30), (22, 22)),
            status="Final", source_url="https://synthetic.invalid/box1",
            source_label="box score 1", source_time="2026-11-15T00:00:00+00:00",
            observed_at="2026-11-15T00:05:00+00:00",
        )
        payload.update(kw)
        return GameResult(**payload)

    def test_two_independent_confirmations_verify_a_final(self):
        result = self._result()
        confirmation = self._result(
            record_id="r2", source_url="https://synthetic.invalid/box2"
        )
        verification = verify_final(result, [confirmation])
        self.assertTrue(verification.verified)
        self.assertEqual(len(verification.confirmations), 2)

    def test_one_confirmation_is_not_enough(self):
        result = self._result()
        confirmation = self._result(
            record_id="r2", source_url="https://synthetic.invalid/box2"
        )
        verification = verify_final(result, [confirmation], required_confirmations=3)
        self.assertFalse(verification.verified)

    def test_a_disagreeing_confirmation_blocks_settlement(self):
        result = self._result()
        confirmation = self._result(
            record_id="r2", source_url="https://synthetic.invalid/box2", home_points=111
        )
        verification = verify_final(result, [confirmation])
        self.assertFalse(verification.verified)
        settlement = settle_pick("spread", "home", -2.5, result, "spread_home_covers",
                                 verification=verification)
        self.assertEqual(settlement.outcome, "NOT SETTLED")

    def test_a_non_final_status_blocks_settlement(self):
        result = self._result(status="In Progress")
        verification = verify_final(result, [self._result(record_id="r2",
                              source_url="https://synthetic.invalid/box2")])
        self.assertFalse(verification.verified)

    def test_spread_settlement_outcomes(self):
        result = self._result()
        verification = verify_final(result, [self._result(record_id="r2",
                              source_url="https://synthetic.invalid/box2")])
        win = settle_pick("spread", "home", -3.0, result, "spread_home_covers",
                           verification=verification, stake=1.0)
        self.assertEqual(win.outcome, "WON")
        # A home line of -9.0 means the home team must win by more than nine.
        loss = settle_pick("spread", "home", -9.0, result, "spread_home_covers",
                           verification=verification, stake=1.0)
        self.assertEqual(loss.outcome, "LOST")
        # A home line of +3.0 means the home team covers when it does not lose
        # by more than three; the home team wins by six, so it covers.
        covers_as_underdog = settle_pick("spread", "home", 3.0, result,
                                         "spread_home_covers", verification=verification)
        self.assertEqual(covers_as_underdog.outcome, "WON")
        push = settle_pick("spread", "home", -6.0, result, "spread_home_covers",
                            verification=verification, stake=1.0)
        self.assertEqual(push.outcome, "PUSH")

    def test_total_and_moneyline_settlement(self):
        result = self._result()
        verification = verify_final(result, [self._result(record_id="r2",
                              source_url="https://synthetic.invalid/box2")])
        over = settle_pick("total", "over", 210.0, result, "total", verification=verification)
        self.assertEqual(over.outcome, "WON")
        under = settle_pick("total", "under", 210.0, result, "total", verification=verification)
        self.assertEqual(under.outcome, "LOST")
        push = settle_pick("total", "over", 214.0, result, "total", verification=verification)
        self.assertEqual(push.outcome, "PUSH")
        ml = settle_pick("moneyline", "home", None, result, "moneyline_home",
                         verification=verification)
        self.assertEqual(ml.outcome, "WON")

    def test_unregistered_settlement_rule_is_void(self):
        result = self._result()
        verification = verify_final(result, [self._result(record_id="r2",
                              source_url="https://synthetic.invalid/box2")])
        settlement = settle_pick("spread", "home", -2.0, result, "made_up_rule",
                                 verification=verification)
        self.assertEqual(settlement.outcome, "VOID")

    def test_settlement_stamp_is_visible_and_carries_the_sources(self):
        result = self._result()
        verification = verify_final(result, [self._result(record_id="r2",
                              source_url="https://synthetic.invalid/box2")])
        stamp = settlement_stamp(result, verification, settled_at=BASE, ledger_hash="abc123")
        self.assertIn("verified=2 source(s)", stamp)
        self.assertIn("result=110-104", stamp)
        self.assertIn("ledger=abc123", stamp)

    def test_settlement_rules_are_stated_exactly(self):
        for key, text in SETTLEMENT_RULES.items():
            self.assertTrue(text.strip())


class TestSeal(unittest.TestCase):
    def test_canonical_hash_is_order_independent(self):
        self.assertEqual(canonical_hash({"a": 1, "b": 2}), canonical_hash({"b": 2, "a": 1}))

    def test_canonical_hash_changes_with_content(self):
        self.assertNotEqual(canonical_hash({"a": 1}), canonical_hash({"a": 2}))

    def test_chain_verifies(self):
        e1 = seal_record({"pick": "a"}, "p1", sealed_at=BASE, previous_hash=GENESIS_HASH, index=0)
        e2 = seal_record({"pick": "b"}, "p2", sealed_at=BASE, previous_hash=e1.chain_hash, index=1)
        ok, problems = verify_chain([e1, e2])
        self.assertTrue(ok, problems)

    def test_tampering_breaks_the_chain(self):
        e1 = seal_record({"pick": "a"}, "p1", sealed_at=BASE, previous_hash=GENESIS_HASH, index=0)
        e2 = seal_record({"pick": "b"}, "p2", sealed_at=BASE, previous_hash=e1.chain_hash, index=1)
        payload = dict(e2.payload)
        payload["pick"] = "tampered"
        e2.payload = payload
        ok, problems = verify_chain([e1, e2])
        self.assertFalse(ok)
        self.assertTrue(any("payload hash" in p for p in problems))

    def test_removing_an_entry_breaks_the_chain(self):
        e1 = seal_record({"pick": "a"}, "p1", sealed_at=BASE, previous_hash=GENESIS_HASH, index=0)
        e2 = seal_record({"pick": "b"}, "p2", sealed_at=BASE, previous_hash=e1.chain_hash, index=1)
        e3 = seal_record({"pick": "c"}, "p3", sealed_at=BASE, previous_hash=e2.chain_hash, index=2)
        ok, problems = verify_chain([e1, e3])
        self.assertFalse(ok)

    def test_published_hash_must_precede_the_tip(self):
        payload = {"pick": "a"}
        digest = canonical_hash(payload)
        tip = BASE + timedelta(hours=5)
        ok, problems = verify_published_hash(digest, payload, published_at=BASE, tip_time=tip)
        self.assertTrue(ok, problems)
        ok, problems = verify_published_hash(digest, payload, published_at=tip, tip_time=tip)
        self.assertFalse(ok)
        self.assertTrue(any("after the tip" in p for p in problems))

    def test_published_hash_must_match_the_record(self):
        ok, problems = verify_published_hash(canonical_hash({"pick": "a"}), {"pick": "b"})
        self.assertFalse(ok)

    def test_missing_published_hash_fails(self):
        ok, problems = verify_published_hash(None, {"pick": "a"})
        self.assertFalse(ok)
        self.assertTrue(any("no hash" in p for p in problems))


class TestPrereg(unittest.TestCase):
    def _prereg(self, **kw):
        payload = dict(
            strategy_id="synthetic-strategy",
            signal="a synthetic signal",
            thresholds={"publish_if": "out-of-sample log loss beats the baseline"},
            universe={"leagues": ["SYNTH"], "markets": ["spread"]},
            settlement_rule="spread_home_covers",
            version="1",
            frozen_at_utc=BASE.isoformat(),
            notes="synthetic fixture",
        )
        payload.update(kw)
        return Preregistration(**payload)

    def test_freeze_writes_the_file_and_its_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path, sha_path, digest = freeze(self._prereg(), tmp)
            self.assertTrue(json_path.is_file())
            self.assertTrue(sha_path.is_file())
            self.assertIn(digest, sha_path.read_text(encoding="utf-8"))
            ok, problems = verify_preregistration(json_path)
            self.assertTrue(ok, problems)

    def test_a_frozen_file_cannot_be_edited(self):
        with tempfile.TemporaryDirectory() as tmp:
            freeze(self._prereg(), tmp)
            with self.assertRaises(ValueError):
                freeze(self._prereg(signal="a different signal"), tmp)

    def test_edited_file_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path, _, _ = freeze(self._prereg(), tmp)
            body = json.loads(json_path.read_text(encoding="utf-8"))
            body["signal"] = "edited after the freeze"
            json_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            ok, problems = verify_preregistration(json_path)
            self.assertFalse(ok)
            self.assertTrue(any("altered" in p for p in problems))

    def test_load_returns_the_frozen_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path, _, _ = freeze(self._prereg(), tmp)
            loaded = load_preregistration(json_path)
            self.assertEqual(loaded.strategy_id, "synthetic-strategy")
            self.assertEqual(loaded.settlement_rule, "spread_home_covers")

    def test_unregistered_settlement_rule_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                freeze(self._prereg(settlement_rule="made_up"), tmp)

    def test_missing_required_field_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                freeze(self._prereg(thresholds={}), tmp)

    def test_a_bet_before_the_freeze_blocks_the_strategy(self):
        ok, problems = check_first_bet(self._prereg(), ["2026-10-31T00:00:00+00:00"])
        self.assertFalse(ok)
        ok, problems = check_first_bet(self._prereg(), ["2026-11-02T00:00:00+00:00"])
        self.assertTrue(ok, problems)


class TestInjuryDiff(unittest.TestCase):
    def _rows(self, *tuples):
        return [InjuryRow(*t) for t in tuples]

    def test_status_change_is_detected(self):
        prev = self._rows(("T", "P1", "Out", "Injury"))
        curr = self._rows(("T", "P1", "Questionable", "Injury"))
        diff = diff_reports(prev, curr, "2026-11-14 04:30 AM", "2026-11-14 05:00 PM")
        self.assertEqual(len(diff.status_changes), 1)
        self.assertEqual(diff.status_changes[0].previous_status, "Out")
        self.assertEqual(diff.status_changes[0].current_status, "Questionable")

    def test_added_and_removed_players(self):
        prev = self._rows(("T", "P1", "Out", "Injury"))
        curr = self._rows(("T", "P2", "Out", "Injury"))
        diff = diff_reports(prev, curr, "a", "b")
        self.assertEqual(len(diff.added), 1)
        self.assertEqual(len(diff.removed), 1)
        self.assertEqual(diff.added[0].player, "P2")
        self.assertEqual(diff.removed[0].player, "P1")

    def test_reason_change_is_not_a_status_change(self):
        prev = self._rows(("T", "P1", "Out", "Injury"))
        curr = self._rows(("T", "P1", "Out", "Illness"))
        diff = diff_reports(prev, curr, "a", "b")
        self.assertEqual(len(diff.status_changes), 0)
        self.assertEqual(len(diff.reason_changes), 1)

    def test_unchanged_rows_are_counted(self):
        prev = self._rows(("T", "P1", "Out", "Injury"), ("T", "P2", "Out", "Illness"))
        curr = self._rows(("T", "P1", "Out", "Injury"), ("T", "P2", "Out", "Illness"))
        diff = diff_reports(prev, curr, "a", "b")
        self.assertEqual(diff.unchanged_count, 2)
        self.assertEqual(len(diff.changes), 0)

    def test_report_times_are_carried_into_the_diff(self):
        diff = diff_reports([], [], "2026-11-14 04:30 AM", "2026-11-14 05:00 PM")
        self.assertEqual(diff.previous_report_time, "2026-11-14 04:30 AM")
        self.assertEqual(diff.current_report_time, "2026-11-14 05:00 PM")

    def test_missing_timestamp_is_flagged(self):
        diff = diff_reports([], [], "", "2026-11-14 05:00 PM")
        self.assertTrue(diff.notes)


if __name__ == "__main__":
    unittest.main()
