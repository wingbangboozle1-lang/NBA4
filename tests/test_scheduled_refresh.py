"""Unit tests for scripts/scheduled_refresh.py (task BH, session arena/cbc8e41a-nba4).

Offline by design: every network call goes through an injected fetcher and every
filesystem touch goes through a temporary directory. No test contacts the web,
and no NBA data value is asserted — only the shape, ordering, freshness and
fail-closed behaviour of the gates.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scheduled_refresh", ROOT / "scripts" / "scheduled_refresh.py")
assert SPEC and SPEC.loader
sr = importlib.util.module_from_spec(SPEC)
sys.modules["scheduled_refresh"] = sr  # required for @dataclass under exec_module
SPEC.loader.exec_module(sr)

NOW = datetime(2026, 11, 16, 10, 15, 0, tzinfo=timezone.utc)

INDEX_HTML = """
<html><body>
<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_11_30PM.pdf">11:30 p.m. ET</a>
<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_12_00AM.pdf">12:00 a.m. ET</a>
<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf">9:15 a.m. ET</a>
<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_11_30PM.pdf">11:30 p.m. ET</a>
<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_12_00AM.pdf">12:00 a.m. ET</a>
</body></html>
"""

PDF_BYTES = b"%PDF-1.4\n%fake\n"
STANDINGS_JSON = json.dumps({"ResultSet": {"RowSet": [[f"row{i}"] for i in range(30)]}}).encode()
STANDINGS_SHORT = json.dumps({"ResultSet": {"RowSet": [[f"row{i}"] for i in range(29)]}}).encode()


def ok_fetch(url: str, *, headers=None, timeout=30.0):
    if url == sr.SCHEDULE_URL:
        return 200, PDF_BYTES, url
    if url == sr.INJURY_INDEX_URL:
        return 200, INDEX_HTML.encode(), url
    if "Injury-Report_" in url:
        return 200, PDF_BYTES, url
    return 200, STANDINGS_JSON, url


def fake_pdf_text(_data: bytes) -> str:
    return "some page text\nInjury Report: 11/17/26 12:00 AM\n"


class ParseTests(unittest.TestCase):
    def test_newest_report_link_ordering(self):
        url, label = sr.parse_newest_report_link(INDEX_HTML)
        self.assertEqual(label, "2026-11-17 12:00 AM")
        self.assertTrue(url.endswith("Injury-Report_2026-11-17_12_00AM.pdf"))

    def test_newest_within_day_prefers_pm_over_am(self):
        html = (
            '<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_12_00AM.pdf">x</a>'
            '<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_11_30PM.pdf">y</a>'
            '<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_30AM.pdf">z</a>'
        )
        _, label = sr.parse_newest_report_link(html)
        self.assertEqual(label, "2026-11-16 11:30 PM")

    def test_no_link_returns_none(self):
        self.assertIsNone(sr.parse_newest_report_link("<html>no reports</html>"))

    def test_report_header_parse_and_url_match(self):
        header = sr.parse_report_header("Injury Report: 11/16/26 06:15 AM")
        self.assertEqual(header, "2026-11-16")
        self.assertTrue(
            sr.header_matches_url(header, "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_06_15AM.pdf")
        )
        self.assertFalse(
            sr.header_matches_url(header, "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf")
        )

    def test_header_absent(self):
        self.assertIsNone(sr.parse_report_header("no header on this page"))

    def test_row_count(self):
        self.assertEqual(sr.count_nba_rows(STANDINGS_JSON), (30, True))
        self.assertEqual(sr.count_nba_rows(STANDINGS_SHORT), (29, False))
        count, ok = sr.count_nba_rows(b"not json at all 1610612738 1610612747")
        self.assertFalse(ok)
        self.assertGreater(count, 0)

    def test_is_pdf(self):
        self.assertTrue(sr.is_pdf(PDF_BYTES))
        self.assertFalse(sr.is_pdf(b"<html>"))

    def test_slate_window_parse(self):
        snapshot = {"window": {"start_utc": "2026-11-15T11:29:57Z", "end_utc": "2026-11-18T11:29:57Z"}}
        start, end = sr.parse_slate_window(snapshot)
        self.assertTrue(start <= NOW <= end)
        self.assertIsNone(sr.parse_slate_window({"window": {}}))


class FreshnessGateTests(unittest.TestCase):
    def _pointer(self, fetched_at: str) -> dict:
        return {"fetched_at_utc": fetched_at, "source_url": "https://ak-static.cms.nba.com/referee/injury/x.pdf"}

    def _slate(self) -> dict:
        return {
            "window": {"start_utc": "2026-11-15T11:29:57Z", "end_utc": "2026-11-18T11:29:57Z"},
            "source_url": sr.SCHEDULE_URL,
        }

    def _gate(self, pointer, slate, newest=None):
        gates = sr.gate_freshness(NOW, pointer=pointer, slate=slate, newest_report=newest)
        return {g.name: g for g in gates}

    def test_fresh_pointer_and_window_pass(self):
        gates = self._gate(self._pointer("2026-11-16T09:00:00Z"), self._slate(), "2026-11-16 09:15 AM")
        self.assertTrue(gates["injury_transcription_age"].passed)
        self.assertTrue(gates["slate_window_current"].passed)
        self.assertIn("9:15 AM", gates["injury_transcription_age"].detail)

    def test_stale_pointer_fails(self):
        gates = self._gate(self._pointer("2026-11-14T09:00:00Z"), self._slate())
        self.assertFalse(gates["injury_transcription_age"].passed)

    def test_missing_pointer_fails(self):
        gates = self._gate(None, self._slate())
        self.assertFalse(gates["injury_transcription_age"].passed)

    def test_window_not_current_fails(self):
        slate = {"window": {"start_utc": "2026-11-10T00:00:00Z", "end_utc": "2026-11-13T00:00:00Z"}}
        gates = self._gate(self._pointer("2026-11-16T09:00:00Z"), slate)
        self.assertFalse(gates["slate_window_current"].passed)


class ScheduleDriftTests(unittest.TestCase):
    def test_first_run_establishes_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "schedule-sha.txt"
            gates = sr.gate_schedule_drift(NOW, baseline, "a" * 64)
            self.assertTrue(all(g.passed for g in gates))
            self.assertEqual(baseline.read_text().strip(), "a" * 64)

    def test_matching_baseline_passes_and_changed_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "schedule-sha.txt"
            baseline.write_text("b" * 64 + "\n")
            gates = {g.name: g for g in sr.gate_schedule_drift(NOW, baseline, "b" * 64)}
            self.assertTrue(gates["schedule_pdf_drift"].passed)
            gates = {g.name: g for g in sr.gate_schedule_drift(NOW, baseline, "c" * 64)}
            self.assertFalse(gates["schedule_pdf_drift"].passed)
            self.assertIn("CHANGED", gates["schedule_pdf_drift"].detail)


class ProvenanceGateTests(unittest.TestCase):
    def _run_on(self, files: dict[str, str]) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp)
            for name, text in files.items():
                (snap / name).write_text(text)
            original = sr.SNAPSHOTS
            sr.SNAPSHOTS = snap
            try:
                return sr.gate_provenance(NOW)
            finally:
                sr.SNAPSHOTS = original

    def test_good_chain_passes(self):
        good = json.dumps(
            {"kind": "official_report_pointer_metadata_only", "source_url": "https://x", "fetched_at_utc": "2026-11-16T10:00:00Z"}
        )
        derived = json.dumps({"kind": "derived_aggregates", "derived_from": ["a.json"]})
        gates = self._run_on({"a.json": good, "b.json": derived})
        self.assertTrue(gates[0].passed)

    def test_missing_fetched_at_fails(self):
        bad = json.dumps({"kind": "official_schedule_rows", "source_url": "https://x"})
        gates = self._run_on({"a.json": bad})
        self.assertFalse(gates[0].passed)
        self.assertIn("fetched_at_utc", gates[0].detail)

    def test_derived_without_inputs_fails(self):
        bad = json.dumps({"kind": "derived_aggregates"})
        gates = self._run_on({"a.json": bad})
        self.assertFalse(gates[0].passed)

    def test_empty_directory_fails(self):
        gates = self._run_on({})
        self.assertFalse(gates[0].passed)


class RunOrchestrationTests(unittest.TestCase):
    """End-to-end gate logic with injected fetchers (no network, no real build)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        snap = Path(self._tmp.name) / "snapshots"
        snap.mkdir()
        (snap / "injuries-newest-pointer-2026-11-16.json").write_text(
            json.dumps(
                {
                    "kind": "official_report_pointer_metadata_only",
                    "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf",
                    "fetched_at_utc": "2026-11-16T09:20:00Z",
                }
            )
        )
        (snap / "slate-2026-11-16.json").write_text(
            json.dumps(
                {
                    "kind": "official_schedule_rows",
                    "source_url": sr.SCHEDULE_URL,
                    "fetched_at_utc": "2026-11-16T09:00:00Z",
                    "window": {"start_utc": "2026-11-16T00:00:00Z", "end_utc": "2026-11-19T00:00:00Z"},
                }
            )
        )
        self._orig_snapshots = sr.SNAPSHOTS
        sr.SNAPSHOTS = snap
        self._orig_build = sr.gate_build
        sr.gate_build = lambda now: [sr.Gate("build_stub", "build", True, "stubbed for tests", observed_at_utc=sr._iso(now))]
        self._baseline = Path(self._tmp.name) / "baseline.txt"

    def tearDown(self):
        sr.SNAPSHOTS = self._orig_snapshots
        sr.gate_build = self._orig_build
        self._tmp.cleanup()

    def test_all_green_gates_mode(self):
        record = sr.run("gates", now=NOW, fetch=ok_fetch, baseline_path=self._baseline, pdf_text=fake_pdf_text)
        self.assertTrue(record.all_passed, [g.as_dict() for g in record.failed()])
        self.assertTrue(record.rebuild_allowed())
        self.assertEqual(record.exit_code(), 0)
        names = [g.name for g in record.gates]
        for expected in (
            "schedule_pdf_fetch",
            "schedule_pdf_drift",
            "injury_index_fetch",
            "injury_report_newest_fetch",
            "injury_report_header",
            "standings_fetch",
            "teamstats_traditional_fetch",
            "teamstats_advanced_fetch",
            "teamstats_opponent_fetch",
            "injury_transcription_age",
            "slate_window_current",
            "provenance_chain",
            "build_stub",
        ):
            self.assertIn(expected, names)

    def test_fail_closed_when_standings_short(self):
        def short_standings(url, *, headers=None, timeout=30.0):
            status, body, final = ok_fetch(url, headers=headers, timeout=timeout)
            if url == sr.STANDINGS_API:
                return 200, STANDINGS_SHORT, url
            return status, body, final

        record = sr.run("gates", now=NOW, fetch=short_standings, baseline_path=self._baseline, pdf_text=fake_pdf_text)
        self.assertFalse(record.rebuild_allowed())
        self.assertEqual(record.exit_code(), 1)
        self.assertIn("standings_fetch", [g.name for g in record.failed()])

    def test_stale_transcription_blocks_rebuild_in_gates_mode(self):
        pointer = sr.SNAPSHOTS / "injuries-newest-pointer-2026-11-16.json"
        doc = json.loads(pointer.read_text())
        doc["fetched_at_utc"] = "2026-11-14T09:20:00Z"
        pointer.write_text(json.dumps(doc))
        record = sr.run("gates", now=NOW, fetch=ok_fetch, baseline_path=self._baseline, pdf_text=fake_pdf_text)
        self.assertFalse(record.rebuild_allowed())
        self.assertEqual(record.exit_code(), 1)
        self.assertIn("injury_transcription_age", [g.name for g in record.failed()])

    def test_probe_asserts_fetch_only(self):
        pointer = sr.SNAPSHOTS / "injuries-newest-pointer-2026-11-16.json"
        doc = json.loads(pointer.read_text())
        doc["fetched_at_utc"] = "2026-11-14T09:20:00Z"  # stale -> freshness gate fails
        pointer.write_text(json.dumps(doc))
        record = sr.run("probe", now=NOW, fetch=ok_fetch, baseline_path=self._baseline, pdf_text=fake_pdf_text)
        self.assertEqual(record.exit_code(), 0)  # freshness reported, not asserted in probe
        self.assertFalse(record.rebuild_allowed())  # probe never licenses a rebuild
        self.assertIn("injury_transcription_age", [g.name for g in record.failed()])

    def test_probe_fails_when_fetch_phase_fails(self):
        def broken(url, *, headers=None, timeout=30.0):
            raise RuntimeError("network down")

        record = sr.run("probe", now=NOW, fetch=broken, baseline_path=self._baseline, pdf_text=fake_pdf_text)
        self.assertEqual(record.exit_code(), 1)
        self.assertFalse(record.fetch_phase_ok)

    def test_offline_mode_never_touches_network(self):
        def exploding(url, *, headers=None, timeout=30.0):  # pragma: no cover
            raise AssertionError(f"offline mode attempted a fetch: {url}")

        record = sr.run("offline", now=NOW, fetch=exploding, baseline_path=self._baseline)
        self.assertTrue(record.all_passed)
        self.assertEqual(record.exit_code(), 0)
        self.assertFalse(record.rebuild_allowed())

    def test_missing_pypdf_fails_header_gate_closed(self):
        record = sr.run(
            "gates",
            now=NOW,
            fetch=ok_fetch,
            baseline_path=self._baseline,
            pdf_text=lambda _d: None,  # simulates pypdf unavailable
        )
        header_gate = next(g for g in record.gates if g.name == "injury_report_header")
        self.assertFalse(header_gate.passed)
        self.assertFalse(record.rebuild_allowed())

    def test_run_record_shape(self):
        record = sr.run("offline", now=NOW, fetch=None, baseline_path=self._baseline)
        payload = record.as_dict()
        self.assertEqual(payload["kind"], "scheduled_refresh_run_record")
        self.assertIn("gates", payload)
        self.assertIn("rebuild_allowed", payload["summary"])
        self.assertEqual(payload["summary"]["exit_code"], record.exit_code())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
