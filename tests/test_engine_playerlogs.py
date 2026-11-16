"""Tests for engine/playerlogs.py - per-player game-log capture.

Synthetic fixtures only. The player ids are invented here; no NBA player, team
or game appears in this file. Every assertion is hand-checkable.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from engine import playerlogs
from engine.contracts import Provenance, RightsError

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


def prov(allowed: bool = True) -> Provenance:
    return Provenance(
        source_id="synthetic.invalid",
        source_name="SYNTHETIC FIXTURE - NOT AN OFFICIAL SOURCE",
        source_url="https://www.nba.com/games",
        source_timestamp=NOW - timedelta(days=1),
        observed_at=NOW - timedelta(hours=2),
        version="synthetic-1",
        allowed_use=allowed,
        allowed_use_note="labelled synthetic fixture used only to prove the engine mechanics",
    )


def log(
    player: str = "synthetic-player-1",
    event: str = "synthetic-game-1",
    team: str = "SYN-A",
    opponent: str = "SYN-B",
    minutes: float = 30.0,
    points: float = 18.0,
    rebounds: float = 5.0,
    assists: float = 4.0,
    date: str = "2026-11-15",
    overtime: int = 0,
    allowed: bool = True,
) -> playerlogs.PlayerGameLog:
    return playerlogs.PlayerGameLog(
        player_id=player,
        player_name=f"Player {player}",
        team_id=team,
        opponent_team_id=opponent,
        event_id=event,
        game_date=date,
        minutes=minutes,
        points=points,
        rebounds=rebounds,
        assists=assists,
        provenance=prov(allowed),
        overtime_periods=overtime,
    )


class LogValidationTest(unittest.TestCase):
    def test_opponent_is_required(self):
        with self.assertRaises(playerlogs.PlayerLogError) as caught:
            log(opponent="")
        self.assertIn("opponent", str(caught.exception))

    def test_a_team_cannot_play_itself(self):
        with self.assertRaises(playerlogs.PlayerLogError) as caught:
            log(team="SYN-A", opponent="SYN-A")
        self.assertIn("cannot play itself", str(caught.exception))

    def test_negative_statistics_rejected(self):
        for field in ("minutes", "points", "rebounds", "assists"):
            with self.assertRaises(playerlogs.PlayerLogError):
                log(**{field: -1.0})

    def test_minutes_cannot_exceed_a_regulation_game(self):
        with self.assertRaises(playerlogs.PlayerLogError) as caught:
            log(minutes=48.5)
        self.assertIn("exceed the game length 48.0", str(caught.exception))

    def test_overtime_raises_the_minutes_ceiling(self):
        # One overtime period is five extra minutes, so the ceiling is 53: 50 is
        # legal in a single-overtime game although it is illegal in regulation.
        self.assertEqual(log(minutes=50.0, overtime=1).minutes, 50.0)
        with self.assertRaises(playerlogs.PlayerLogError):
            log(minutes=48.5)
        with self.assertRaises(playerlogs.PlayerLogError):
            log(minutes=53.5, overtime=1)

    def test_two_overtime_periods_give_a_58_minute_ceiling(self):
        self.assertEqual(log(minutes=58.0, overtime=2).minutes, 58.0)
        with self.assertRaises(playerlogs.PlayerLogError):
            log(minutes=58.5, overtime=2)

    def test_negative_overtime_rejected(self):
        with self.assertRaises(playerlogs.PlayerLogError):
            log(overtime=-1)

    def test_missing_player_or_event_rejected(self):
        with self.assertRaises(playerlogs.PlayerLogError):
            log(player="")
        with self.assertRaises(playerlogs.PlayerLogError):
            log(event="")


class PerMinuteTest(unittest.TestCase):
    def test_rate_is_points_per_minute_when_the_player_played(self):
        self.assertAlmostEqual(log(minutes=30.0, points=18.0).per_minute("points"), 0.6, places=9)

    def test_a_did_not_play_game_has_no_rate_not_a_zero(self):
        self.assertIsNone(log(minutes=0.0).per_minute("points"))

    def test_unknown_stat_rejected(self):
        with self.assertRaises(playerlogs.PlayerLogError):
            log().per_minute("steals")

    def test_played_flag(self):
        self.assertTrue(log(minutes=0.1).played)
        self.assertFalse(log(minutes=0.0).played)


class BookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.book = playerlogs.PlayerLogBook()
        self.book.extend(
            [
                log(player="p1", event="g1", date="2026-11-13"),
                log(player="p1", event="g2", date="2026-11-15"),
                log(player="p2", event="g1", date="2026-11-13", minutes=0.0, points=0.0),
            ]
        )

    def test_distinct_player_games_stored(self):
        self.assertEqual(len(self.book), 3)
        summary = self.book.summary()
        self.assertEqual(summary["distinct_players"], 2)
        self.assertEqual(summary["distinct_games"], 2)
        self.assertEqual(summary["log_rows"], 3)

    def test_logs_for_one_player_are_ordered_by_date(self):
        rows = self.book.logs_for("p1")
        self.assertEqual([row.event_id for row in rows], ["g1", "g2"])


class CorroborationTest(unittest.TestCase):
    def test_agreeing_observation_does_not_duplicate_the_row(self):
        book = playerlogs.PlayerLogBook()
        self.assertTrue(book.add(log()))
        self.assertFalse(book.add(log()))
        self.assertEqual(len(book), 1)
        self.assertEqual(book.corroborations[("synthetic-player-1", "synthetic-game-1")], 1)

    def test_disagreeing_observation_raises_and_does_not_overwrite(self):
        book = playerlogs.PlayerLogBook()
        book.add(log())
        with self.assertRaises(playerlogs.LogConflict):
            book.add(log(points=99.0))
        # The stored row is untouched.
        self.assertEqual(book.logs[("synthetic-player-1", "synthetic-game-1")].points, 18.0)

    def test_different_opponent_for_the_same_game_is_a_conflict(self):
        book = playerlogs.PlayerLogBook()
        book.add(log(opponent="SYN-B"))
        with self.assertRaises(playerlogs.LogConflict):
            book.add(log(opponent="SYN-C"))


class CoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.book = playerlogs.PlayerLogBook()
        self.book.extend(
            [
                log(player="p1", event="g1"),
                log(player="p2", event="g1", minutes=0.0, points=0.0),
            ]
        )

    def test_captured_and_missing_are_reported_separately(self):
        report = self.book.coverage(["p1", "p2", "p3"])
        self.assertEqual(report.captured, ("p1", "p2"))
        self.assertEqual(report.missing, ("p3",))
        self.assertAlmostEqual(report.coverage_fraction, 2 / 3, places=9)

    def test_a_missing_player_is_never_a_line_of_zeros(self):
        report = self.book.coverage(["p3"])
        self.assertEqual(report.captured, ())
        self.assertEqual(report.missing, ("p3",))
        self.assertEqual(report.coverage_fraction, 0.0)
        self.assertEqual(len(self.book.logs_for("p3")), 0)

    def test_a_did_not_play_log_counts_as_captured_not_missing(self):
        report = self.book.coverage(["p2"])
        self.assertEqual(report.captured, ("p2",))
        self.assertEqual(report.missing, ())

    def test_empty_roster_has_zero_coverage(self):
        self.assertEqual(self.book.coverage([]).coverage_fraction, 0.0)

    def test_duplicate_roster_entries_counted_once(self):
        report = self.book.coverage(["p1", "p1"])
        self.assertEqual(report.roster, ("p1",))
        self.assertEqual(report.coverage_fraction, 1.0)

    def test_uncleared_logs_are_named_in_the_report(self):
        book = playerlogs.PlayerLogBook()
        book.add(log(player="p9", event="g1", allowed=False))
        report = book.coverage(["p9"])
        self.assertEqual(report.uncleared, ("p9",))


class RightsGateTest(unittest.TestCase):
    def test_model_inputs_refuse_an_uncleared_log(self):
        book = playerlogs.PlayerLogBook()
        book.add(log(allowed=False))
        with self.assertRaises(RightsError):
            book.model_inputs(["synthetic-player-1"])

    def test_model_inputs_refuse_a_missing_player_rather_than_inferring_a_log(self):
        book = playerlogs.PlayerLogBook()
        book.add(log(player="p1"))
        with self.assertRaises(playerlogs.PlayerLogError) as caught:
            book.model_inputs(["p1", "p2"])
        self.assertIn(playerlogs.LOG_MISSING, str(caught.exception))

    def test_model_inputs_return_rows_when_everything_is_captured_and_cleared(self):
        book = playerlogs.PlayerLogBook()
        book.add(log(player="p1", event="g1"))
        book.add(log(player="p1", event="g2", date="2026-11-15"))
        payload = book.model_inputs(["p1"])
        self.assertEqual(len(payload["rows"]), 2)
        self.assertEqual(payload["players"], ["p1"])
        self.assertEqual(payload["coverage"]["coverage_fraction"], 1.0)
        self.assertTrue(payload["inputs_hash"])


class HashTest(unittest.TestCase):
    def test_hash_is_stable_and_order_independent(self):
        first = playerlogs.PlayerLogBook()
        first.extend([log(player="p1", event="g1"), log(player="p2", event="g2")])
        second = playerlogs.PlayerLogBook()
        second.extend([log(player="p2", event="g2"), log(player="p1", event="g1")])
        self.assertEqual(first.canonical_hash(), second.canonical_hash())

    def test_hash_changes_when_a_row_changes(self):
        first = playerlogs.PlayerLogBook()
        first.add(log(points=18.0))
        second = playerlogs.PlayerLogBook()
        second.add(log(points=19.0))
        self.assertNotEqual(first.canonical_hash(), second.canonical_hash())

    def test_roster_scoped_hash_ignores_other_players(self):
        book = playerlogs.PlayerLogBook()
        book.add(log(player="p1", event="g1"))
        scoped = book.canonical_hash(["p1"])
        book.add(log(player="p2", event="g2"))
        self.assertEqual(book.canonical_hash(["p1"]), scoped)


if __name__ == "__main__":
    unittest.main()


class PlayerLogsCliTest(unittest.TestCase):
    """The capture subcommand; it exits non-zero when the roster has a gap."""

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

    def _logs(self, roster=("p1",)) -> dict:
        return {
            "roster": list(roster),
            "logs": [
                {
                    "player_id": "p1",
                    "player_name": "Synthetic One",
                    "team_id": "SYN-A",
                    "opponent_team_id": "SYN-B",
                    "event_id": "g1",
                    "game_date": "2026-11-15",
                    "minutes": 30.0,
                    "points": 18.0,
                    "rebounds": 5.0,
                    "assists": 4.0,
                    "overtime_periods": 0,
                    "provenance": {
                        "source_id": "synthetic.invalid",
                        "source_name": "SYNTHETIC FIXTURE - NOT AN OFFICIAL SOURCE",
                        "source_url": "https://www.nba.com/games",
                        "source_timestamp": "2026-11-15T12:00:00Z",
                        "observed_at": "2026-11-16T10:00:00Z",
                        "version": "synthetic-1",
                        "allowed_use": True,
                        "allowed_use_note": "synthetic fixture",
                    },
                }
            ],
        }

    def test_complete_roster_exits_zero_and_prints_the_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "logs.json"
            path.write_text(json.dumps(self._logs()), encoding="utf-8")
            code, out = self._run("playerlogs", "--logs", str(path))
        self.assertEqual(code, 0, out)
        self.assertIn("canonical hash", out)
        self.assertIn("1.0 covered", out)

    def test_missing_roster_player_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "logs.json"
            path.write_text(json.dumps(self._logs(roster=("p1", "p2"))), encoding="utf-8")
            code, out = self._run("playerlogs", "--logs", str(path))
        self.assertEqual(code, 1)
        self.assertIn("p2", out)
        self.assertIn(playerlogs.LOG_MISSING, out)

    def test_explicit_roster_flag_overrides_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "logs.json"
            path.write_text(json.dumps(self._logs()), encoding="utf-8")
            code, out = self._run("playerlogs", "--logs", str(path), "--roster", "p1,p9")
        self.assertEqual(code, 1)
        self.assertIn("p9", out)
