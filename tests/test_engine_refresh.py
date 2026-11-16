"""Tests for engine/refresh.py - the rolling-slate refresh gate.

All fixtures are synthetic and labelled as such. No NBA or market data is used
anywhere in this file: every timestamp, URL and row count is invented here so
the arithmetic can be checked by hand.

The URLs are the ones the module declares (they identify the feed), but no test
asserts anything about what those documents contain.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from engine import refresh
from engine.pipeline import refresh_gate

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)

STANDINGS = refresh.STANDINGS_URL
TRAD, OPP, ADV = refresh.TEAM_STATS_URLS
INJURIES = refresh.INJURY_INDEX_URL


def spec_url() -> str:
    return refresh.SCHEDULE_URL


def spec(**kwargs) -> refresh.FeedSpec:
    base = {
        "feed_id": "synthetic_feed",
        "label": "synthetic feed",
        "url": "https://www.nba.com/standings",
        "required": True,
        "max_age_minutes": 90,
    }
    base.update(kwargs)
    return refresh.FeedSpec(**base)


def observation(**kwargs) -> refresh.FeedObservation:
    base = {
        "feed_id": "synthetic_feed",
        "url": "https://www.nba.com/standings",
        # Retrieved two minutes ago by default: any document timestamp used in
        # these tests is older than that, so the provenance chain stays possible.
        "retrieved_at": NOW - timedelta(minutes=2),
        "allowed_use": True,
    }
    base.update(kwargs)
    return refresh.FeedObservation(**base)


class RollingWindowTest(unittest.TestCase):
    def test_default_horizon_is_three_days(self):
        window = refresh.rolling_window(NOW)
        self.assertEqual(window.horizon_hours, 72)
        self.assertEqual(window.end - window.start, timedelta(hours=72))

    def test_horizon_capped_at_three_days(self):
        for hours in (0, -1, 73, 200):
            with self.assertRaises(refresh.RefreshError):
                refresh.rolling_window(NOW, hours)

    def test_one_and_two_day_horizons_allowed(self):
        self.assertEqual(refresh.rolling_window(NOW, 24).horizon_hours, 24)
        self.assertEqual(refresh.rolling_window(NOW, 48).horizon_hours, 48)

    def test_naive_now_rejected(self):
        with self.assertRaises(refresh.RefreshError):
            refresh.rolling_window(datetime(2026, 11, 16, 12, 0))


class FeedSpecValidationTest(unittest.TestCase):
    def test_non_https_url_rejected(self):
        with self.assertRaises(refresh.RefreshError):
            spec(url="http://www.nba.com/standings")

    def test_non_positive_age_rejected(self):
        with self.assertRaises(refresh.RefreshError):
            spec(max_age_minutes=0)

    def test_non_positive_expected_rows_rejected(self):
        with self.assertRaises(refresh.RefreshError):
            spec(expected_rows=0)

    def test_missing_feed_id_rejected(self):
        with self.assertRaises(refresh.RefreshError):
            spec(feed_id="")

    def test_naive_retrieved_at_rejected(self):
        with self.assertRaises(refresh.RefreshError):
            observation(retrieved_at=datetime(2026, 11, 16, 12, 0))


class EvaluateTest(unittest.TestCase):
    def test_missing_observation_is_not_retrieved_and_blocks(self):
        verdict = refresh.evaluate(spec(), None, NOW)
        self.assertIs(verdict.state, refresh.FeedState.NOT_RETRIEVED)
        self.assertTrue(verdict.blocking)

    def test_optional_feed_failure_warns_without_blocking(self):
        verdict = refresh.evaluate(spec(required=False), None, NOW)
        self.assertIs(verdict.state, refresh.FeedState.NOT_RETRIEVED)
        self.assertFalse(verdict.blocking)

    def test_fresh_document_inside_tolerance_passes(self):
        obs = observation(document_timestamp=NOW - timedelta(minutes=10))
        verdict = refresh.evaluate(spec(), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.PASS)
        self.assertFalse(verdict.blocking)
        self.assertEqual(verdict.age_basis, "document timestamp")
        self.assertAlmostEqual(verdict.age_minutes, 10.0, places=3)

    def test_stale_document_blocked_and_age_measured_from_the_document(self):
        obs = observation(
            document_timestamp=NOW - timedelta(minutes=200),
            retrieved_at=NOW - timedelta(minutes=1),
        )
        verdict = refresh.evaluate(spec(max_age_minutes=90), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.STALE_DOCUMENT)
        self.assertTrue(verdict.blocking)
        self.assertAlmostEqual(verdict.age_minutes, 200.0, places=3)

    def test_no_document_stamp_uses_retrieval_time_and_says_so(self):
        obs = observation(retrieved_at=NOW - timedelta(minutes=30))
        verdict = refresh.evaluate(spec(), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.PASS)
        self.assertEqual(verdict.age_basis, "retrieval time (no document stamp)")

    def test_stale_retrieval_blocked(self):
        obs = observation(retrieved_at=NOW - timedelta(minutes=95))
        verdict = refresh.evaluate(spec(max_age_minutes=90), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.STALE_RETRIEVAL)
        self.assertTrue(verdict.blocking)

    def test_required_document_timestamp_missing_blocks(self):
        obs = observation(retrieved_at=NOW - timedelta(minutes=1))
        verdict = refresh.evaluate(spec(requires_document_timestamp=True), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.NO_DOCUMENT_TIMESTAMP)
        self.assertTrue(verdict.blocking)

    def test_required_document_timestamp_present_passes(self):
        obs = observation(
            retrieved_at=NOW - timedelta(minutes=1),
            document_timestamp=NOW - timedelta(minutes=20),
        )
        verdict = refresh.evaluate(spec(requires_document_timestamp=True), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.PASS)

    def test_uncleared_feed_blocked_before_freshness_is_reported(self):
        obs = observation(allowed_use=False, document_timestamp=NOW - timedelta(minutes=10))
        verdict = refresh.evaluate(spec(), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.RIGHTS_NOT_CLEARED)
        self.assertTrue(verdict.blocking)

    def test_retrieved_before_published_is_refused_not_repaired(self):
        obs = observation(
            retrieved_at=NOW - timedelta(minutes=60),
            document_timestamp=NOW - timedelta(minutes=20),
        )
        verdict = refresh.evaluate(spec(), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.RETRIEVED_BEFORE_PUBLISHED)
        self.assertTrue(verdict.blocking)

    def test_url_mismatch_blocked(self):
        obs = observation(url="https://www.nba.com/games")
        verdict = refresh.evaluate(spec(), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.URL_MISMATCH)
        self.assertTrue(verdict.blocking)

    def test_partial_rows_blocked(self):
        obs = observation(rows_read=13, document_timestamp=NOW - timedelta(minutes=10))
        verdict = refresh.evaluate(spec(expected_rows=30), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.INCOMPLETE_ROWS)
        self.assertTrue(verdict.blocking)
        self.assertIn("13 of 30", verdict.detail)

    def test_unreported_row_count_blocked(self):
        obs = observation(document_timestamp=NOW - timedelta(minutes=10))
        verdict = refresh.evaluate(spec(expected_rows=30), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.INCOMPLETE_ROWS)

    def test_complete_rows_pass(self):
        obs = observation(rows_read=30, document_timestamp=NOW - timedelta(minutes=10))
        verdict = refresh.evaluate(spec(expected_rows=30), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.PASS)

    def test_partial_chunks_blocked(self):
        obs = observation(chunks_read=1, document_timestamp=NOW - timedelta(minutes=10))
        verdict = refresh.evaluate(spec(expected_chunks=2), obs, NOW)
        self.assertIs(verdict.state, refresh.FeedState.INCOMPLETE_CHUNKS)


class RefreshDecisionTest(unittest.TestCase):
    def test_all_feeds_fresh_permits_rebuild(self):
        specs = (spec(feed_id="a"), spec(feed_id="b"))
        obs = {
            "a": observation(feed_id="a", document_timestamp=NOW - timedelta(minutes=10)),
            "b": observation(feed_id="b", document_timestamp=NOW - timedelta(minutes=20)),
        }
        decision = refresh.refresh_decision(specs, obs, NOW)
        self.assertTrue(decision.may_rebuild)
        self.assertEqual(decision.blocking_reasons, ())
        self.assertEqual(len(decision.verdicts), 2)
        self.assertEqual(decision.window.as_dict()["horizon_hours"], 72)

    def test_one_stale_required_feed_blocks_the_rebuild(self):
        specs = (spec(feed_id="a"), spec(feed_id="b"))
        obs = {
            "a": observation(feed_id="a", document_timestamp=NOW - timedelta(minutes=10)),
            "b": observation(feed_id="b", document_timestamp=NOW - timedelta(minutes=500)),
        }
        decision = refresh.refresh_decision(specs, obs, NOW)
        self.assertFalse(decision.may_rebuild)
        self.assertEqual(len(decision.blocking_reasons), 1)
        self.assertIn("b: STALE_DOCUMENT", decision.blocking_reasons[0])

    def test_failed_optional_feed_warns_and_still_permits(self):
        specs = (spec(feed_id="a"), spec(feed_id="optional", required=False))
        obs = {"a": observation(feed_id="a", document_timestamp=NOW - timedelta(minutes=10))}
        decision = refresh.refresh_decision(specs, obs, NOW)
        self.assertTrue(decision.may_rebuild)
        self.assertEqual(decision.blocking_reasons, ())
        self.assertEqual(len(decision.warnings), 1)
        self.assertIn("optional", decision.warnings[0])

    def test_undeclared_observation_is_a_warning(self):
        specs = (spec(feed_id="a"),)
        obs = {
            "a": observation(feed_id="a", document_timestamp=NOW - timedelta(minutes=10)),
            "stray": observation(feed_id="stray"),
        }
        decision = refresh.refresh_decision(specs, obs, NOW)
        self.assertTrue(decision.may_rebuild)
        self.assertTrue(any("stray" in warning for warning in decision.warnings))

    def test_default_specs_cover_the_five_brief_feeds(self):
        specs = refresh.default_feed_specs()
        ids = {s.feed_id for s in specs}
        self.assertEqual(
            ids,
            {
                "schedule",
                "standings",
                "team_stats_traditional",
                "team_stats_opponent",
                "team_stats_advanced",
                "injuries",
                "results",
            },
        )
        by_id = {s.feed_id: s for s in specs}
        self.assertTrue(by_id["injuries"].requires_document_timestamp)
        for name in ("team_stats_traditional", "team_stats_opponent", "team_stats_advanced"):
            self.assertEqual(by_id[name].expected_rows, 30)
        self.assertFalse(by_id["results"].required, "results settles after the fact, so it is optional pre-tip")
        for s in specs:
            self.assertTrue(s.url.startswith("https://"))

    def test_default_specs_with_nothing_observed_refuse_the_rebuild(self):
        decision = refresh.refresh_decision(refresh.default_feed_specs(), {}, NOW)
        self.assertFalse(decision.may_rebuild)
        self.assertEqual(len(decision.blocking_reasons), 6)

    def test_summary_counts(self):
        specs = (spec(feed_id="a"), spec(feed_id="b"))
        obs = {"a": observation(feed_id="a", document_timestamp=NOW - timedelta(minutes=10))}
        decision = refresh.refresh_decision(specs, obs, NOW)
        summary = decision.summary()
        self.assertEqual(summary["feeds_checked"], 2)
        self.assertEqual(summary["feeds_passed"], 1)
        self.assertFalse(summary["may_rebuild"])


class PipelineHookTest(unittest.TestCase):
    def test_hook_passes_a_permitting_decision(self):
        specs = (spec(feed_id="a"),)
        obs = {"a": observation(feed_id="a", document_timestamp=NOW - timedelta(minutes=10))}
        decision = refresh.refresh_decision(specs, obs, NOW)
        may, reasons = refresh_gate(decision)
        self.assertTrue(may)
        self.assertEqual(reasons, ())

    def test_hook_blocks_and_carries_the_reasons(self):
        decision = refresh.refresh_decision(refresh.default_feed_specs(), {}, NOW)
        may, reasons = refresh_gate(decision)
        self.assertFalse(may)
        self.assertEqual(len(reasons), 6)

    def test_hook_refuses_an_inconsistent_decision(self):
        class Inconsistent:
            may_rebuild = True
            blocking_reasons = ("synthetic: blocking reason",)

        may, reasons = refresh_gate(Inconsistent())
        self.assertFalse(may)
        self.assertIn("REFRESH_DECISION_INCONSISTENT", reasons[-1])

    def test_hook_defaults_to_refusal_on_an_empty_object(self):
        class Empty:
            pass

        may, reasons = refresh_gate(Empty())
        self.assertFalse(may)
        self.assertEqual(reasons, ())


if __name__ == "__main__":
    unittest.main()


class RefreshCliTest(unittest.TestCase):
    """The scheduled job must not be able to mistake a refusal for success."""

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

    def test_no_observations_refuses_and_exits_non_zero(self):
        code, out = self._run("refresh", "--now", "2026-11-16T12:00:00Z")
        self.assertEqual(code, 1)
        self.assertIn("NO REBUILD", out)
        self.assertIn("NOT_RETRIEVED", out)

    def test_all_feeds_fresh_permits_the_rebuild_and_exits_zero(self):
        payload = {
            "observations": [
                {
                    "feed_id": feed,
                    "url": url,
                    "retrieved_at": "2026-11-16T11:58:00Z",
                    "document_timestamp": doc,
                    "rows_read": 30,
                    "allowed_use": True,
                }
                for feed, url, doc in (
                    ("schedule", spec_url(), "2026-11-16T00:00:00Z"),
                    ("standings", STANDINGS, "2026-11-16T06:00:00Z"),
                    ("team_stats_traditional", TRAD, "2026-11-16T06:00:00Z"),
                    ("team_stats_opponent", OPP, "2026-11-16T06:00:00Z"),
                    ("team_stats_advanced", ADV, "2026-11-16T06:00:00Z"),
                    ("injuries", INJURIES, "2026-11-16T11:00:00Z"),
                )
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            code, out = self._run(
                "refresh", "--now", "2026-11-16T12:00:00Z", "--observations", str(path)
            )
        self.assertEqual(code, 0, out)
        self.assertIn("REBUILD", out)

    def test_one_stale_feed_blocks_the_rebuild_and_exits_non_zero(self):
        payload = {
            "observations": [
                {
                    "feed_id": "injuries",
                    "url": INJURIES,
                    # The injury report is 5 hours old; its tolerance is 90 minutes.
                    "retrieved_at": "2026-11-16T11:58:00Z",
                    "document_timestamp": "2026-11-16T07:00:00Z",
                    "allowed_use": True,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            code, out = self._run(
                "refresh", "--now", "2026-11-16T12:00:00Z", "--observations", str(path)
            )
        self.assertEqual(code, 1)
        self.assertIn("injuries: STALE_DOCUMENT", out)

    def test_modules_audit_exits_zero_and_reports_the_new_modules(self):
        code, out = self._run("modules")
        self.assertEqual(code, 0, out)
        self.assertIn("refresh", out)
        self.assertIn("playerlogs", out)
        self.assertIn("teamstats", out)
        self.assertIn("modules imported cleanly", out)
