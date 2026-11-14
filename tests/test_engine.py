"""Test suite for the NBA4 reference engine.

The tests use **synthetic** records generated inside the test file. They contain
no NBA data, no market data and no player identifiers; they only prove that
the arithmetic and the control logic behave as specified.

Run with:

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta, timezone

from engine import correlation, lineorigination, parlay, pipeline, sources, validation
from engine.contracts import (
    ContractError,
    Forecast,
    GameEvent,
    InjuryRecord,
    MarketQuote,
    Pick,
    Provenance,
    RightsError,
    Status,
    require_allowed_use,
    snapshot_hash,
)
from engine.leaderboard import GateOutcome, LeaderboardEntry, LeaderboardPolicy, rank

UTC = timezone.utc
NOW = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)


def provenance(
    source_id: str = "TEST-SYNTHETIC",
    allowed_use: bool = True,
    age_minutes: int = 1,
    source_timestamp: datetime | None = None,
) -> Provenance:
    """Synthetic provenance for tests (never an NBA or market source)."""
    published = source_timestamp or (NOW - timedelta(minutes=age_minutes + 1))
    return Provenance(
        source_id=source_id,
        source_name="Synthetic test fixture (not NBA data)",
        source_url="https://example.invalid/synthetic-fixture",
        source_timestamp=published,
        observed_at=NOW - timedelta(minutes=age_minutes),
        version="test-1",
        allowed_use=allowed_use,
        allowed_use_note="synthetic fixture for unit tests only",
    )


class ContractTests(unittest.TestCase):
    def test_provenance_requires_https_url(self) -> None:
        with self.assertRaises(ContractError):
            Provenance(
                source_id="X",
                source_name="X",
                source_url="http://example.invalid/x",
                source_timestamp=NOW,
                observed_at=NOW,
                version="1",
            )

    def test_observed_at_cannot_precede_source_timestamp(self) -> None:
        with self.assertRaises(ContractError):
            Provenance(
                source_id="X",
                source_name="X",
                source_url="https://example.invalid/x",
                source_timestamp=NOW,
                observed_at=NOW - timedelta(minutes=5),
                version="1",
            )

    def test_rights_flag_is_enforced(self) -> None:
        event = GameEvent(
            event_id="synthetic-1",
            tipoff_utc=NOW + timedelta(hours=2),
            home_team_id="SYN-HOME",
            away_team_id="SYN-AWAY",
            provenance=provenance(allowed_use=False),
        )
        with self.assertRaises(RightsError):
            require_allowed_use(event)

    def test_leakage_check_flags_future_inputs(self) -> None:
        forecast = Forecast(
            forecast_id="f-1",
            event_id="synthetic-1",
            market_type="spread",
            side="home",
            model_version="m-1",
            emitted_at=NOW,
            line=1.5,
            probability=0.5,
            input_snapshot_hash=snapshot_hash({"a": 1}),
            sample_size=120,
            provenance=provenance(),
        )
        stale_event = GameEvent(
            event_id="synthetic-1",
            tipoff_utc=NOW + timedelta(hours=2),
            home_team_id="SYN-HOME",
            away_team_id="SYN-AWAY",
            provenance=provenance(age_minutes=0),
        )
        violations = validation.leakage_violations(forecast, [stale_event])
        self.assertTrue(violations)


class LineOriginationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = lineorigination.GameScoreModel(
            expected_home_points=112.0,
            expected_away_points=108.0,
            margin_sd=11.0,
            total_sd=19.0,
            model_version="synthetic-v1",
        )

    def test_fair_price_round_trip(self) -> None:
        price = lineorigination.fair_decimal_price(0.25)
        self.assertAlmostEqual(price, 4.0)
        self.assertAlmostEqual(lineorigination.net_edge(0.25, 4.0), 0.0)

    def test_net_edge_sign(self) -> None:
        self.assertGreater(lineorigination.net_edge(0.55, 2.0), 0.0)
        self.assertLess(lineorigination.net_edge(0.40, 2.0), 0.0)

    def test_spread_and_total_come_from_the_distribution(self) -> None:
        self.assertAlmostEqual(lineorigination.originate_spread(self.model), 4.0)
        self.assertAlmostEqual(lineorigination.originate_total(self.model), 220.0)

    def test_rounding_uses_the_supplied_increment(self) -> None:
        self.assertEqual(lineorigination.round_to_increment(4.24, 0.5), 4.0)
        self.assertEqual(lineorigination.round_to_increment(4.26, 0.5), 4.5)
        self.assertEqual(lineorigination.round_to_increment(4.26, None), 4.26)

    def test_cover_probabilities_are_complementary(self) -> None:
        home = lineorigination.cover_probability(self.model, 2.0, "home")
        away = lineorigination.cover_probability(self.model, 2.0, "away")
        self.assertAlmostEqual(home + away, 1.0)

    def test_total_probabilities_are_complementary(self) -> None:
        over = lineorigination.total_probability(self.model, 215.0, "over")
        under = lineorigination.total_probability(self.model, 215.0, "under")
        self.assertAlmostEqual(over + under, 1.0)

    def test_devig_multiplicative_removes_the_margin(self) -> None:
        # A fair 50/50 market quoted at 1.91 / 1.91.
        p_a, p_b = lineorigination.devig_two_way(1.91, 1.91)
        self.assertAlmostEqual(p_a, 0.5, places=6)
        self.assertAlmostEqual(p_b, 0.5, places=6)
        margin = lineorigination.margin_of_two_way(1.91, 1.91)
        self.assertGreater(margin, 0.0)

    def test_devig_additive_splits_the_margin_evenly(self) -> None:
        p_a, p_b = lineorigination.devig_two_way(2.0, 1.8, method="additive")
        self.assertAlmostEqual(p_a + p_b, 1.0, places=9)

    def test_shin_requires_its_parameter(self) -> None:
        with self.assertRaises(ValueError):
            lineorigination.devig_two_way(2.0, 1.9, method="shin")
        shin_a, shin_b = lineorigination.devig_two_way(2.0, 1.9, method="shin", shin_z=0.02)
        mult_a, mult_b = lineorigination.devig_two_way(2.0, 1.9, method="multiplicative")
        self.assertAlmostEqual(shin_a + shin_b, 1.0, places=6)
        # Shin protects the favourite: the side with the higher implied
        # probability keeps (slightly) more probability than under
        # proportional de-vigging.
        favourite_shin = shin_b if shin_b > shin_a else shin_a
        favourite_mult = mult_b if mult_b > mult_a else mult_a
        self.assertGreater(favourite_shin, favourite_mult)

    def test_prop_line_is_the_quantile_of_the_predictive_distribution(self) -> None:
        prop = lineorigination.PlayerPropModel(
            expected_minutes=32.0,
            minutes_sd=6.0,
            rate_mean=0.55,
            rate_sd=0.12,
            minutes_corr_with_rate=0.2,
            model_version="synthetic-v1",
        )
        median_line = lineorigination.originate_prop_line(prop, quantile=0.5)
        self.assertAlmostEqual(median_line, prop.expected_total, delta=0.6)
        self.assertGreater(
            lineorigination.originate_prop_line(prop, quantile=0.8),
            lineorigination.originate_prop_line(prop, quantile=0.2),
        )
        p_over = lineorigination.prop_probability(prop, median_line, over=True)
        self.assertAlmostEqual(p_over, 0.5, delta=0.06)

    def test_prop_variance_includes_the_correlation_term(self) -> None:
        independent = lineorigination.PlayerPropModel(30.0, 5.0, 0.5, 0.1, 0.0, "synthetic-v1")
        correlated = lineorigination.PlayerPropModel(30.0, 5.0, 0.5, 0.1, 0.5, "synthetic-v1")
        self.assertGreater(correlated.total_variance, independent.total_variance)


class CorrelationTests(unittest.TestCase):
    def test_pearson_matches_a_known_value(self) -> None:
        xs = [1.0, 2.0, 3.0, 4.0]
        ys = [2.0, 4.0, 5.0, 4.0]
        # Cross-checked by hand: covariance 3.5, sx = sqrt(5), sy = sqrt(4.75).
        self.assertAlmostEqual(correlation.pearson(xs, ys), 0.7181848464596078, places=9)

    def test_pearson_rejects_a_constant_series(self) -> None:
        with self.assertRaises(ValueError):
            correlation.pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])

    def test_spearman_is_one_for_a_monotone_relationship(self) -> None:
        self.assertAlmostEqual(correlation.spearman([1.0, 2.0, 3.0], [10.0, 20.0, 30.0]), 1.0)

    def test_phi_for_perfect_agreement(self) -> None:
        xs = [True, True, False, False]
        ys = [True, True, False, False]
        self.assertAlmostEqual(correlation.phi(xs, ys), 1.0)

    def test_cluster_bootstrap_interval_brackets_the_estimate(self) -> None:
        clusters = {
            f"g{i}": [(float(i), float(i) + 0.1 * ((i % 3) - 1)) for i in range(4)]
            for i in range(12)
        }
        result = correlation.correlation_with_uncertainty(clusters, method="pearson", resamples=300)
        self.assertGreaterEqual(result.sample_size, 48)
        self.assertIsNotNone(result.lower)
        self.assertLessEqual(result.lower, result.upper)
        self.assertEqual(result.cluster_count, 12)

    def test_shrink_moves_toward_the_prior(self) -> None:
        self.assertAlmostEqual(correlation.shrink(0.5, 0.0, 0.5), 0.25)
        self.assertAlmostEqual(correlation.shrink(0.5, 0.0, 0.0), 0.5)


class ParlayTests(unittest.TestCase):
    def test_independent_legs_match_the_product_of_marginals(self) -> None:
        legs = [
            parlay.ParlayLeg("leg-1", "synthetic-1", 0.5),
            parlay.ParlayLeg("leg-2", "synthetic-1", 0.5),
        ]
        estimate = parlay.joint_probability(legs, [[1.0, 0.0], [0.0, 1.0]], draws=20000, seed=7)
        self.assertAlmostEqual(estimate.joint_probability, 0.25, delta=0.02)
        self.assertAlmostEqual(estimate.independent_probability, 0.25, places=9)

    def test_positive_dependence_raises_the_joint_probability(self) -> None:
        legs = [
            parlay.ParlayLeg("leg-1", "synthetic-1", 0.5),
            parlay.ParlayLeg("leg-2", "synthetic-1", 0.5),
        ]
        estimate = parlay.joint_probability(legs, [[1.0, 0.7], [0.7, 1.0]], draws=20000, seed=7)
        self.assertGreater(estimate.joint_probability, estimate.independent_probability)
        self.assertGreater(estimate.dependence_effect, 0.02)

    def test_cholesky_rejects_a_non_positive_definite_matrix(self) -> None:
        with self.assertRaises(ValueError):
            parlay.cholesky([[1.0, 1.2], [1.2, 1.0]])

    def test_cholesky_rejects_an_asymmetric_matrix(self) -> None:
        with self.assertRaises(ValueError):
            parlay.cholesky([[1.0, 0.3], [0.2, 1.0]])


class ValidationTests(unittest.TestCase):
    def test_brier_and_log_loss_of_a_perfect_forecast(self) -> None:
        probs = [1.0, 0.0, 1.0, 0.0]
        outcomes = [True, False, True, False]
        self.assertAlmostEqual(validation.brier_score(probs, outcomes), 0.0)
        self.assertLess(validation.log_loss(probs, outcomes), 1e-9)

    def test_reliability_table_reports_every_populated_bin(self) -> None:
        probs = [0.1, 0.2, 0.8, 0.9]
        outcomes = [False, True, True, True]
        table = validation.reliability_table(probs, outcomes, bins=10)
        self.assertTrue(table)
        for row in table:
            self.assertGreaterEqual(row["count"], 1)
            self.assertLessEqual(row["observed_frequency"], 1.0)

    def test_walk_forward_splits_are_chronological(self) -> None:
        events = [
            GameEvent(
                event_id=f"synthetic-{index}",
                tipoff_utc=NOW + timedelta(days=index),
                home_team_id="SYN-HOME",
                away_team_id="SYN-AWAY",
                provenance=provenance(),
            )
            for index in range(20)
        ]
        splits = validation.walk_forward_splits(events, train_days=5, test_days=2)
        self.assertTrue(splits)
        for train, test in splits:
            self.assertLess(max(e.tipoff_utc for e in train), min(e.tipoff_utc for e in test))

    def test_net_return_sums_the_settled_records(self) -> None:
        picks = [{"net_return": 1.0}, {"net_return": -1.0}, {"net_return": 0.0}]
        self.assertAlmostEqual(validation.net_return(picks), 0.0)

    def test_coverage_reports_the_share_inside_the_interval(self) -> None:
        intervals = [(0.0, 10.0), (0.0, 10.0)]
        self.assertAlmostEqual(validation.coverage([5.0, 5.0], intervals, [5.0, 11.0]), 0.5)


class LeaderboardTests(unittest.TestCase):
    def _entry(self, gates: tuple[GateOutcome, ...]) -> LeaderboardEntry:
        return LeaderboardEntry(
            strategy_id="S1",
            model_version="v1",
            market="spread",
            sample_size=500,
            test_window="2026-01-01..2026-06-30",
            brier_score=0.22,
            log_loss=0.62,
            expected_calibration_error=0.03,
            net_units=18.0,
            net_units_per_bet=0.03,
            max_drawdown_units=9.0,
            baseline_comparison="better than the declared baseline",
            correlation_check="legs checked",
            gates=gates,
        )

    def test_nothing_is_ranked_when_a_gate_fails(self) -> None:
        policy = LeaderboardPolicy(
            metric_weights={"net_units_per_bet": 1.0},
            minimum_sample_size=100,
            required_gate_ids=("G0", "G4"),
            tie_breaker="sample size, then strategy id",
        )
        gates = (
            GateOutcome("G0", True, "passed"),
            GateOutcome("G4", False, "failed"),
        )
        self.assertEqual(rank([self._entry(gates)], policy), [])

    def test_a_passing_entry_is_ranked(self) -> None:
        policy = LeaderboardPolicy(
            metric_weights={"net_units_per_bet": 1.0, "brier_score": 0.5},
            minimum_sample_size=100,
            required_gate_ids=("G0", "G4"),
            tie_breaker="sample size, then strategy id",
        )
        gates = (
            GateOutcome("G0", True, "passed"),
            GateOutcome("G4", True, "passed"),
        )
        rows = rank([self._entry(gates)], policy)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rank"], 1)

    def test_a_missing_gate_is_not_silently_passed(self) -> None:
        policy = LeaderboardPolicy(
            metric_weights={"net_units_per_bet": 1.0},
            minimum_sample_size=100,
            required_gate_ids=("G0", "G4", "G5"),
            tie_breaker="sample size, then strategy id",
        )
        gates = (
            GateOutcome("G0", True, "passed"),
            GateOutcome("G4", True, "passed"),
        )
        outcomes = __import__(
            "engine.leaderboard", fromlist=["evaluate_gates"]
        ).evaluate_gates(self._entry(gates), policy)
        self.assertFalse(any(gate.gate_id == "G5" and gate.passed for gate in outcomes))


class PipelineTests(unittest.TestCase):
    def _events(self, count: int = 3) -> list[GameEvent]:
        return [
            GameEvent(
                event_id=f"synthetic-{index}",
                tipoff_utc=NOW + timedelta(hours=6 * index + 2),
                home_team_id="SYN-HOME",
                away_team_id="SYN-AWAY",
                provenance=provenance(),
            )
            for index in range(count)
        ]

    def _config(self, **overrides) -> pipeline.RunConfig:
        base = dict(
            run_id="synthetic-run",
            now_utc=NOW,
            horizon_hours=pipeline.HORIZON_HOURS,
            timezone_name="UTC",
            max_input_age_minutes=90,
            model_version="synthetic-v1",
            market_specified=True,
        )
        base.update(overrides)
        return pipeline.RunConfig(**base)

    def test_horizon_filter_is_hard(self) -> None:
        events = self._events(3)
        slate = pipeline.select_slate(events, NOW, pipeline.HORIZON_HOURS)
        self.assertEqual(len(slate), 3)
        far = [
            GameEvent(
                event_id="synthetic-far",
                tipoff_utc=NOW + timedelta(days=5),
                home_team_id="SYN-HOME",
                away_team_id="SYN-AWAY",
                provenance=provenance(),
            )
        ]
        self.assertEqual(pipeline.select_slate(events + far, NOW, pipeline.HORIZON_HOURS), slate)

    def test_horizon_cannot_exceed_three_days(self) -> None:
        with self.assertRaises(ValueError):
            self._config(horizon_hours=100)

    def test_stale_inputs_suppress_the_run(self) -> None:
        events = [
            GameEvent(
                event_id="synthetic-stale",
                tipoff_utc=NOW + timedelta(hours=3),
                home_team_id="SYN-HOME",
                away_team_id="SYN-AWAY",
                provenance=provenance(age_minutes=600),
            )
        ]
        report = pipeline.run_pipeline(self._config(), events)
        self.assertTrue(report.stale_inputs)
        self.assertEqual(report.picks, [])
        self.assertTrue(any(s["reason_code"] == "STALE_DATA" for s in report.suppressed))

    def test_rights_failure_suppresses_the_run(self) -> None:
        events = [
            GameEvent(
                event_id="synthetic-norights",
                tipoff_utc=NOW + timedelta(hours=3),
                home_team_id="SYN-HOME",
                away_team_id="SYN-AWAY",
                provenance=provenance(allowed_use=False),
            )
        ]
        report = pipeline.run_pipeline(self._config(), events)
        self.assertFalse(report.rights_cleared)
        self.assertEqual(report.picks, [])
        self.assertTrue(any(s["reason_code"] == "RIGHTS_NOT_CLEARED" for s in report.suppressed))

    def test_no_bet_when_the_market_is_not_specified(self) -> None:
        events = self._events(1)

        def strategy(config, slate, injuries):
            return [
                Forecast(
                    forecast_id="f-1",
                    event_id=slate[0].event_id,
                    market_type="spread",
                    side="home",
                    model_version=config.model_version,
                    emitted_at=config.now_utc,
                    line=1.5,
                    probability=0.55,
                    input_snapshot_hash=snapshot_hash({"x": 1}),
                    sample_size=250,
                    provenance=provenance(),
                )
            ]

        report = pipeline.run_pipeline(self._config(market_specified=False), events, strategy=strategy)
        self.assertEqual(len(report.picks), 1)
        self.assertEqual(report.picks[0]["decision"], "no_bet")
        self.assertIn("NO_MARKET_SPEC", report.picks[0]["reason_codes"])

    def test_pick_records_an_edge_against_a_licensed_quote(self) -> None:
        events = self._events(1)
        quote = MarketQuote(
            market_id="q-1",
            event_id=events[0].event_id,
            market_type="spread",
            side="home",
            line=1.5,
            price_decimal=1.9,
            quote_timestamp=NOW - timedelta(minutes=2),
            provider_id="SYNTHETIC",
            provenance=provenance(),
        )

        def strategy(config, slate, injuries):
            return [
                Forecast(
                    forecast_id="f-2",
                    event_id=slate[0].event_id,
                    market_type="spread",
                    side="home",
                    model_version=config.model_version,
                    emitted_at=config.now_utc,
                    line=1.5,
                    probability=0.55,
                    input_snapshot_hash=snapshot_hash({"x": 2}),
                    sample_size=250,
                    provenance=provenance(),
                )
            ]

        report = pipeline.run_pipeline(self._config(), events, quotes=[quote], strategy=strategy)
        pick = report.picks[0]
        self.assertEqual(pick["decision"], "bet")
        self.assertAlmostEqual(pick["edge"], 0.55 * 1.9 - 1.0, places=9)

    def test_below_the_declared_minimum_sample_is_a_no_bet(self) -> None:
        events = self._events(1)
        quote = MarketQuote(
            market_id="q-2",
            event_id=events[0].event_id,
            market_type="spread",
            side="home",
            line=1.5,
            price_decimal=1.9,
            quote_timestamp=NOW - timedelta(minutes=2),
            provider_id="SYNTHETIC",
            provenance=provenance(),
        )

        def strategy(config, slate, injuries):
            return [
                Forecast(
                    forecast_id="f-3",
                    event_id=slate[0].event_id,
                    market_type="spread",
                    side="home",
                    model_version=config.model_version,
                    emitted_at=config.now_utc,
                    line=1.5,
                    probability=0.55,
                    input_snapshot_hash=snapshot_hash({"x": 3}),
                    sample_size=50,
                    provenance=provenance(),
                )
            ]

        report = pipeline.run_pipeline(
            self._config(minimum_sample_size=100), events, quotes=[quote], strategy=strategy
        )
        pick = report.picks[0]
        self.assertEqual(pick["decision"], "no_bet")
        self.assertIn("BELOW_MINIMUM_SAMPLE", pick["reason_codes"])

    def test_ledger_is_append_only(self) -> None:
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "ledger.jsonl")
            pipeline.append_ledger(path, {"run_id": "a"})
            pipeline.append_ledger(path, {"run_id": "b"})
            with open(path, encoding="utf-8") as handle:
                lines = [line for line in handle.read().splitlines() if line]
            self.assertEqual(len(lines), 2)


class PickContractTests(unittest.TestCase):
    def test_a_bet_requires_reason_codes(self) -> None:
        with self.assertRaises(ContractError):
            Pick(
                pick_id="p-1",
                forecast_id="f-1",
                event_id="synthetic-1",
                decision="bet",
                stake_fraction=0.01,
                edge=0.05,
                reason_codes=(),
            )

    def test_status_values_match_the_official_report_labels(self) -> None:
        self.assertEqual(Status.OUT.value, "Out")
        self.assertEqual(Status.QUESTIONABLE.value, "Questionable")
        self.assertEqual(Status.DOUBTFUL.value, "Doubtful")
        self.assertEqual(Status.PROBABLE.value, "Probable")
        self.assertEqual(Status.AVAILABLE.value, "Available")
        self.assertEqual(Status.NOT_WITH_TEAM.value, "Not With Team")


class SourceRegistryTests(unittest.TestCase):
    def test_every_source_has_an_https_official_url(self) -> None:
        allowed = (
            "nba.com",
            "github.com",
            "kansspelautoriteit.nl",
            "scikit-learn.org",
            "itl.nist.gov",
        )
        for source in sources.SOURCES:
            self.assertTrue(source.url.startswith("https://"), source.source_id)
            host = source.url.split("/")[2].lower()
            self.assertTrue(
                any(host == domain or host.endswith("." + domain) for domain in allowed),
                f"{source.source_id}: {host}",
            )

    def test_source_ids_are_unique(self) -> None:
        ids = [source.source_id for source in sources.SOURCES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_registry_contains_the_data_rights_sources(self) -> None:
        ids = {source.source_id for source in sources.SOURCES}
        for required in ("NBA-01", "NBA-02", "NBA-03", "GH-03", "KSA-01"):
            self.assertIn(required, ids)


class InjuryContractTests(unittest.TestCase):
    def test_injury_record_requires_a_known_status(self) -> None:
        record = InjuryRecord(
            event_id="synthetic-1",
            player_id="SYN-PLAYER",
            status=Status.OUT,
            reason="Injury/Illness",
            provenance=provenance(),
        )
        self.assertEqual(record.status.value, "Out")
        with self.assertRaises(ContractError):
            InjuryRecord(
                event_id="synthetic-1",
                player_id="SYN-PLAYER",
                status="Out",  # type: ignore[arg-type]
                reason="Injury/Illness",
                provenance=provenance(),
            )


if __name__ == "__main__":
    unittest.main()
