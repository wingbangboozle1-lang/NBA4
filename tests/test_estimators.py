"""Synthetic unit tests for disagreement-first margin estimates (not NBA data)."""
from __future__ import annotations

import sys
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.estimators import compare_estimators
from engine.ratings import (
    home_advantage_from_win_rate,
    measured_home_win_rate,
    margin_forecast,
)
from engine.selftest import BASE, build_synthetic_games
from engine.schema import TeamGame


class TestEmpiricalHomeRate(unittest.TestCase):
    def test_rate_is_observed_unique_home_games_before_as_of(self):
        games = build_synthetic_games()
        rate, n = measured_home_win_rate(games, BASE)
        self.assertEqual(n, 8)
        self.assertAlmostEqual(rate, 0.5)

    def test_future_home_games_are_excluded(self):
        games = build_synthetic_games() + [TeamGame(
            "future", "future-game", (BASE + timedelta(days=1)).isoformat(),
            "SYNTH-H", "SYNTH-A", True, 1, 0, 100,
            build_synthetic_games()[0].provenance,
        )]
        rate, n = measured_home_win_rate(games, BASE)
        self.assertEqual(n, 8)
        self.assertAlmostEqual(rate, 0.5)

    def test_duplicate_home_row_is_rejected(self):
        g = build_synthetic_games()[0]
        duplicate = TeamGame("copy", g.game_id, g.game_date, g.team, g.opponent,
                             True, g.points, g.opp_points, g.possessions, g.provenance)
        with self.assertRaisesRegex(ValueError, "duplicate home-team"):
            measured_home_win_rate([g, duplicate], BASE)

    def test_no_free_home_advantage_parameter(self):
        with self.assertRaises(TypeError):
            margin_forecast(build_synthetic_games(), "SYNTH-H", "SYNTH-A", BASE,
                            home_advantage=99.0)

    def test_rate_conversion_refuses_extremes_and_bad_sd(self):
        for rate in (0.0, 1.0):
            with self.assertRaises(ValueError):
                home_advantage_from_win_rate(rate, 12.0)
        with self.assertRaises(ValueError):
            home_advantage_from_win_rate(0.6, 0.0)

    def test_margin_forecast_records_anchor(self):
        f = margin_forecast(build_synthetic_games(), "SYNTH-H", "SYNTH-A", BASE)
        self.assertEqual(f.measured_home_win_rate, 0.5)
        self.assertEqual(f.home_games_used, 8)
        self.assertEqual(f.home_advantage_points, 0.0)

    def test_missing_possessions_are_not_replaced_with_a_default(self):
        games = [TeamGame(g.record_id, g.game_id, g.game_date, g.team, g.opponent,
                          g.is_home, g.points, g.opp_points, None, g.provenance)
                 for g in build_synthetic_games()]
        f = margin_forecast(games, "SYNTH-H", "SYNTH-A", BASE)
        self.assertIsNone(f.expected_home_margin)
        self.assertIsNone(f.expected_total)

    def test_extreme_rate_suppresses_instead_of_clipping(self):
        games = []
        for i in range(8):
            date = (BASE - timedelta(days=i + 1)).isoformat()
            games.extend([
                TeamGame(f"h{i}", f"g{i}", date, "H", "A", True, 100, 90, 100,
                         build_synthetic_games()[0].provenance),
                TeamGame(f"a{i}", f"away{i}", date, "A", "H", False, 90, 100, 100,
                         build_synthetic_games()[0].provenance),
            ])
        self.assertIsNone(margin_forecast(games, "H", "A", BASE).expected_home_margin)


class TestEstimatorDisagreement(unittest.TestCase):
    def test_disagreement_is_primary_and_blend_is_secondary(self):
        result = compare_estimators(build_synthetic_games(), "SYNTH-H", "SYNTH-A", BASE)
        self.assertIsNotNone(result.estimator_a_matchup_ppp)
        self.assertIsNotNone(result.estimator_b_point_differential)
        self.assertEqual(
            result.primary_confidence_signal,
            abs(result.estimator_a_matchup_ppp - result.estimator_b_point_differential),
        )
        self.assertEqual(
            result.blended_margin_secondary,
            (result.estimator_a_matchup_ppp + result.estimator_b_point_differential) / 2,
        )

    def test_outcome_does_not_create_a_pick_or_confidence_probability(self):
        result = compare_estimators(build_synthetic_games(), "SYNTH-H", "SYNTH-A", BASE)
        self.assertIsInstance(result.primary_confidence_signal, float)
        self.assertGreaterEqual(result.primary_confidence_signal, 0.0)
        self.assertFalse(hasattr(result, "confidence_probability"))


if __name__ == "__main__":
    unittest.main()
