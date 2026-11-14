"""Unit tests for the NBA4 engine (stdlib unittest).

Fixtures here are SYNTHETIC (host synthetic.invalid) and exist only to test
mechanics. Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import math
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.corrstats import (  # noqa: E402
    cluster_bootstrap_ci,
    joint_event_estimate,
    pearson,
    phi,
    residual_correlation_estimate,
    shrink_toward_zero,
)
from engine.gameflow import scenario_distribution  # noqa: E402
from engine.injuries import availability_scenario, roster_scenario  # noqa: E402
from engine.ledger import integrity_report, load_ledger  # noqa: E402
from engine.picks import generate_slate_picks, in_horizon, parlay_record  # noqa: E402
from engine.player_props import player_prop_forecast  # noqa: E402
from engine.ratings import cover_probability, margin_forecast, win_probability  # noqa: E402
from engine.schema import (  # noqa: E402
    InjuryObservation,
    PickRecord,
    PlayerGame,
    Provenance,
    SchemaError,
    SlateGame,
    TeamGame,
)
from engine.gates import (  # noqa: E402
    brier_score,
    log_loss,
    reliability_bins,
    run_gates,
    skill_vs_baseline,
    trials_adjusted_alpha,
    walk_forward_folds,
)
from engine.selftest import BASE, build_synthetic_games, run_selftest  # noqa: E402

PROV = Provenance("https://synthetic.invalid/fixture", BASE.isoformat(), BASE.isoformat())
BAD_PROV = Provenance("http://insecure.example/x", BASE.isoformat(), BASE.isoformat())


class TestSchema(unittest.TestCase):
    def test_valid_game(self):
        g = TeamGame("g1", "x", BASE.isoformat(), "A", "B", True, 100, 95, 100.0, PROV)
        g.validate()

    def test_rejects_missing_https_source(self):
        g = TeamGame("g1", "x", BASE.isoformat(), "A", "B", True, 100, 95, 100.0, BAD_PROV)
        with self.assertRaises(SchemaError):
            g.validate()

    def test_rejects_naive_datetime(self):
        prov = Provenance("https://synthetic.invalid/f", "2026-11-14T12:00:00", BASE.isoformat())
        g = TeamGame("g1", "x", BASE.isoformat(), "A", "B", True, 100, 95, 100.0, prov)
        with self.assertRaises(SchemaError):
            g.validate()

    def test_rejects_unknown_injury_status(self):
        obs = InjuryObservation("i1", BASE.isoformat(), "x", "A", "P", "Probably", "r", PROV)
        with self.assertRaises(SchemaError):
            obs.validate()

    def test_rejects_minutes_out_of_range(self):
        p = PlayerGame("p1", "x", BASE.isoformat(), "P", "A", 60.0, 10, provenance=PROV)
        with self.assertRaises(SchemaError):
            p.validate()


class TestLedger(unittest.TestCase):
    def _write(self, tmp: Path, name: str, rows):
        import json

        (tmp / name).write_text(
            "\n".join(json.dumps(r) for r in rows), encoding="utf-8"
        )

    def test_rejects_rows_without_provenance(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            self._write(tmp, "games.jsonl", [{
                "record_id": "g1", "game_id": "x", "game_date": BASE.isoformat(),
                "team": "A", "opponent": "B", "is_home": True,
                "points": 100, "opp_points": 95,
                "provenance": {"source_url": "", "source_time": "", "observed_at": ""},
            }])
            ledger = load_ledger(tmp, allow_synthetic=True)
            self.assertEqual(ledger.games, [])
            self.assertEqual(len(ledger.rejected), 1)

    def test_production_run_filters_synthetic_host(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            self._write(tmp, "games.jsonl", [{
                "record_id": "g1", "game_id": "x", "game_date": BASE.isoformat(),
                "team": "A", "opponent": "B", "is_home": True,
                "points": 100, "opp_points": 95, "possessions": 100.0,
                "provenance": {"source_url": "https://synthetic.invalid/f",
                               "source_time": BASE.isoformat(),
                               "observed_at": BASE.isoformat()},
            }])
            self.assertEqual(len(load_ledger(tmp, allow_synthetic=True).games), 1)
            self.assertEqual(len(load_ledger(tmp).games), 0)  # production mode

    def test_integrity_report(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            ledger = load_ledger(td)
            report = integrity_report(ledger, td)
            self.assertFalse(report.passed)
            self.assertIn("missing ledger files", report.notes[0])


class TestRatings(unittest.TestCase):
    def test_no_line_under_min_games(self):
        games = build_synthetic_games()[:3]
        f = margin_forecast(games, "SYNTH-H", "SYNTH-A", BASE)
        self.assertIsNone(f.expected_home_margin)

    def test_line_from_enough_games(self):
        games = build_synthetic_games()
        f = margin_forecast(games, "SYNTH-H", "SYNTH-A", BASE)
        self.assertIsNotNone(f.expected_home_margin)
        self.assertGreater(f.expected_home_margin, 0)  # SYNTH-H is stronger

    def test_never_uses_future_games(self):
        games = build_synthetic_games() + [TeamGame(
            "future", "f", (BASE + timedelta(days=2)).isoformat(),
            "SYNTH-A", "SYNTH-H", True, 130, 80, 100.0, PROV,
        )]
        f = margin_forecast(games, "SYNTH-H", "SYNTH-A", BASE)
        f2 = margin_forecast(build_synthetic_games(), "SYNTH-H", "SYNTH-A", BASE)
        self.assertAlmostEqual(f.expected_home_margin, f2.expected_home_margin)

    def test_win_probability_symmetry(self):
        self.assertAlmostEqual(win_probability(0.0), 0.5)
        self.assertAlmostEqual(win_probability(6.0) + win_probability(-6.0), 1.0)

    def test_cover_probability_equal_line(self):
        self.assertAlmostEqual(cover_probability(3.0, 3.0), 0.5)


class TestPlayerProps(unittest.TestCase):
    def _games(self, n=8):
        return [PlayerGame(
            f"p{i}", f"x{i}", (BASE - timedelta(days=i * 3 + 1)).isoformat(),
            "SYNTH-PLAYER", "SYNTH-H", 30.0, 18.0 + i % 4, 5.0, 4.0, PROV,
        ) for i in range(n)]

    def test_min_games_gate(self):
        f = player_prop_forecast(self._games(3), "SYNTH-PLAYER", "points", 0.5, BASE)
        self.assertIsNone(f.expected_value)
        self.assertEqual(f.games_used, 3)

    def test_forecast_and_shrinkage(self):
        f = player_prop_forecast(self._games(8), "SYNTH-PLAYER", "points", 0.5, BASE)
        self.assertIsNotNone(f.expected_value)
        # raw rate ~ 19.5/30 = 0.65/min; shrinkage toward 0.5 pulls below raw
        self.assertLess(f.expected_value, 0.65 * 30.0)
        self.assertGreater(f.over_probability(15.0), 0.5)

    def test_availability_multiplier_scales_minutes(self):
        f1 = player_prop_forecast(self._games(), "SYNTH-PLAYER", "points", 0.5, BASE)
        f2 = player_prop_forecast(self._games(), "SYNTH-PLAYER", "points", 0.5, BASE,
                                  availability_multiplier=0.5)
        self.assertAlmostEqual(f2.expected_value, f1.expected_value * 0.5)


class TestInjuries(unittest.TestCase):
    def test_unresolved_without_observation(self):
        s = availability_scenario([], "GHOST")
        self.assertFalse(s.resolved)
        self.assertIsNone(s.availability_prob)

    def test_latest_status_wins(self):
        old = InjuryObservation("i1", (BASE - timedelta(days=1)).isoformat(), "x",
                                "A", "P", "Out", "r", PROV)
        new = InjuryObservation("i2", BASE.isoformat(), "x", "A", "P", "Probable", "r", PROV)
        s = availability_scenario([old, new], "P")
        self.assertEqual(s.status, "Probable")

    def test_roster_all_resolved(self):
        obs = [InjuryObservation("i1", BASE.isoformat(), "x", "A", "P", "Out", "r", PROV)]
        _, resolved = roster_scenario(obs, ["P"])
        self.assertTrue(resolved)
        _, resolved2 = roster_scenario(obs, ["P", "Q"])
        self.assertFalse(resolved2)


class TestGameFlow(unittest.TestCase):
    def test_probabilities_partition(self):
        s = scenario_distribution(0.0, 12.0)
        total = s.p_competitive + s.p_separation_home + s.p_separation_away + s.p_moderate
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_heavy_favourite_more_separation(self):
        s = scenario_distribution(20.0, 12.0)
        self.assertGreater(s.p_separation_home, s.p_separation_away)

    def test_rejects_bad_sd(self):
        with self.assertRaises(ValueError):
            scenario_distribution(0.0, 0.0)


class TestCorrelation(unittest.TestCase):
    def test_pearson_known_values(self):
        self.assertAlmostEqual(pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(pearson([1, 2, 3], [-2, -4, -6]), -1.0)
        self.assertIsNone(pearson([1, 1, 1], [1, 2, 3]))  # zero variance

    def test_phi_known_values(self):
        a = [True, True, False, False]
        b = [True, True, False, False]
        self.assertAlmostEqual(phi(a, b), 1.0)
        self.assertIsNone(phi([True], [True]))

    def test_shrink_toward_zero(self):
        self.assertAlmostEqual(shrink_toward_zero(0.5, 10, 10), 0.25)
        self.assertEqual(shrink_toward_zero(0.5, 0), 0.0)

    def test_residual_estimate_blank_without_pairs(self):
        est = residual_correlation_estimate([("g1", 1.0)], [])
        self.assertIsNone(est.value)
        self.assertIn("stays blank", est.notes[0])

    def test_residual_estimate_with_pairs(self):
        a = [("g1", 1.0), ("g1", 2.0), ("g2", -1.0), ("g2", -2.0)]
        b = [("g1", 1.0), ("g1", 2.0), ("g2", -1.0), ("g2", -2.0)]
        est = residual_correlation_estimate(a, b, shrink=False)
        self.assertAlmostEqual(est.value, 1.0)
        self.assertEqual(est.clusters, 2)
        self.assertEqual(est.clusters, 2)

    def test_bootstrap_deterministic_with_seed(self):
        vals = [("g1", 1.0), ("g1", 2.0), ("g2", 3.0), ("g2", 4.0),
                ("g3", 5.0), ("g3", 6.0)]
        f = lambda s: sum(s) / len(s)  # noqa: E731
        ci1 = cluster_bootstrap_ci(vals, f, n_boot=200, seed=7)
        ci2 = cluster_bootstrap_ci(vals, f, n_boot=200, seed=7)
        self.assertEqual(ci1, ci2)
        self.assertIsNotNone(ci1[0])

    def test_joint_event_estimate(self):
        a = [("g1", True), ("g2", False), ("g3", True), ("g4", False)]
        b = [("g1", True), ("g2", False), ("g3", True), ("g4", False)]
        est = joint_event_estimate(a, b)
        self.assertAlmostEqual(est.value, 1.0)


class TestValidation(unittest.TestCase):
    def test_brier_known(self):
        self.assertAlmostEqual(brier_score([1.0, 0.0], [1, 0]), 0.0)
        self.assertAlmostEqual(brier_score([0.5, 0.5], [1, 0]), 0.25)

    def test_log_loss_known(self):
        self.assertAlmostEqual(log_loss([1.0, 1.0], [1, 1]), 0.0, places=6)

    def test_reliability_bins(self):
        bins = reliability_bins([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1], bins=2)
        self.assertEqual(len(bins), 2)
        self.assertEqual(bins[0][2], 2)

    def test_walk_forward_is_chronological(self):
        folds = walk_forward_folds(100, 3, 40)
        self.assertEqual(len(folds), 3)
        for train, test in folds:
            self.assertLess(max(train), min(test))

    def test_trials_adjustment(self):
        self.assertAlmostEqual(trials_adjusted_alpha(0.05, 10), 0.005)

    def test_skill_vs_baseline(self):
        self.assertAlmostEqual(skill_vs_baseline([0.2, 0.3], [0.4, 0.5]), 0.2)

    def test_gate_report_states(self):
        from engine.ledger import Ledger

        rep = integrity_report(Ledger(), "/nonexistent")
        states = run_gates(rep, has_market_spec=False, n_settled_forecasts=0)
        names = {s.gate: s.state for s in states}
        self.assertEqual(names["G0 rights/jurisdiction"], "blocked")
        self.assertEqual(names["G6 net value"], "blocked")
        self.assertEqual(len(states), 13)  # G0..G12


class TestPicks(unittest.TestCase):
    def test_horizon_filter(self):
        self.assertTrue(in_horizon((BASE + timedelta(days=1)).isoformat(), BASE))
        self.assertTrue(in_horizon((BASE + timedelta(hours=71)).isoformat(), BASE))
        self.assertFalse(in_horizon((BASE + timedelta(days=4)).isoformat(), BASE))
        self.assertFalse(in_horizon((BASE - timedelta(hours=1)).isoformat(), BASE))

    def test_empty_ledger_yields_no_picks(self):
        from engine.ledger import Ledger

        decisions, report = generate_slate_picks(Ledger(), issued_at=BASE)
        self.assertEqual(decisions, [])
        self.assertIn("no authorized inputs in ledger (G1 blocked)",
                      report["no_pick_reasons"])

    def test_no_pick_suppression_with_slate_but_no_games(self):
        from engine.ledger import Ledger

        ledger = Ledger(slate=[SlateGame(
            "s1", "x", (BASE + timedelta(days=1)).isoformat(), "H", "A", PROV
        )])
        decisions, _ = generate_slate_picks(ledger, issued_at=BASE)
        self.assertEqual(len(decisions), 1)
        for rec in decisions[0].records:
            self.assertEqual(rec.status, "NO PICK")
            self.assertTrue(rec.reason_codes)
            self.assertIsNone(rec.originated_line)

    def test_shadow_run_on_synthetic_data(self):
        from engine.selftest import build_synthetic_ledger
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            by_file = {}
            for name, row in build_synthetic_ledger():
                by_file.setdefault(name, []).append(row)
            for name, rows in by_file.items():
                (tmp / name).write_text(
                    "\n".join(json.dumps(r) for r in rows), encoding="utf-8"
                )
            ledger = load_ledger(tmp, allow_synthetic=True)
            decisions, _ = generate_slate_picks(
                ledger, issued_at=BASE, allow_shadow=True
            )
            self.assertEqual(len(decisions), 1)
            statuses = {r.status for r in decisions[0].records}
            self.assertIn("SHADOW", statuses)
            spread = [r for r in decisions[0].records if r.market == "spread"][0]
            self.assertIsNotNone(spread.originated_line)

    def test_parlay_same_game_needs_joint(self):
        legs = [PickRecord(
            pick_id=f"l{i}", issued_at=BASE.isoformat(), model_version="m",
            code_version="c", market="prop", selection=f"leg{i}",
            originated_line=None, forecast_probability=0.55, fair_price=None,
            benchmark_quote_id=None, horizon_end=BASE.isoformat(),
            status="SHADOW", reason_codes=(), input_snapshot=(),
        ) for i in range(2)]
        p = parlay_record(legs, [0.55, 0.60], None, BASE, ["g1", "g1"])
        self.assertEqual(p.status, "NO PICK")
        self.assertIn("same-game legs: joint dependence unverified (G8)", p.reason_codes)

    def test_parlay_cross_game_uses_product(self):
        legs = [PickRecord(
            pick_id=f"l{i}", issued_at=BASE.isoformat(), model_version="m",
            code_version="c", market="spread", selection=f"leg{i}",
            originated_line=None, forecast_probability=0.5, fair_price=None,
            benchmark_quote_id=None, horizon_end=BASE.isoformat(),
            status="SHADOW", reason_codes=(), input_snapshot=(),
        ) for i in range(2)]
        p = parlay_record(legs, [0.5, 0.5], None, BASE, ["g1", "g2"])
        self.assertEqual(p.status, "SHADOW")
        self.assertAlmostEqual(p.forecast_probability, 0.25)


class TestSelftest(unittest.TestCase):
    def test_selftest_runs_clean(self):
        self.assertEqual(run_selftest(), 0)


if __name__ == "__main__":
    unittest.main()
