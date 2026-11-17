"""Offline tests for the official-page transport (tasks BU/BV, session `arena/af666c53-nba4`).

Every test here runs against a body captured from an official page, or against a
hand-built synthetic body whose expected answer is written out in the test. No
test makes a network call, so the whole suite is reproducible from a clone.

The captures live in `data/official-pages/2026-11-17/` and were made by
`scripts/capture_official_pages.py` on a GitHub-hosted runner, because the
sandbox these tests are developed in cannot reach nba.com at all.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import official_pages as op  # noqa: E402  (path set up above)

CAPTURE_DIR = ROOT / "data" / "official-pages" / "2026-11-17"
MANIFEST = CAPTURE_DIR / "manifest.json"
STAT_PAGE_KEYS = (
    "standings",
    "teamstats_traditional",
    "teamstats_opponent",
    "teamstats_advanced",
)


def _require_captures(testcase: unittest.TestCase) -> None:
    if not MANIFEST.is_file():
        testcase.skipTest(f"no capture manifest at {MANIFEST}")


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _record(key: str) -> dict | None:
    for record in _manifest().get("records", []):
        if record.get("key") == key:
            return record
    return None


class CaptureManifestEvidence(unittest.TestCase):
    """The reachability evidence the transport choice rests on."""

    def setUp(self) -> None:
        _require_captures(self)

    def test_manifest_declares_its_runner_and_clock(self):
        manifest = _manifest()
        self.assertIn("GitHub-hosted", manifest["runner"])
        self.assertTrue(manifest["generated_at_utc"].endswith("Z"))
        self.assertTrue(manifest["records"])

    def test_stats_nba_com_endpoints_are_recorded_as_unreached_timeouts(self):
        for key in ("stats_api_standings", "stats_api_teamstats", "stats_api_scoreboard"):
            record = _record(key)
            self.assertIsNotNone(record, f"missing capture record {key}")
            self.assertFalse(record["reached"])
            self.assertIsNone(record["http_status"])
            self.assertIn("timed out", record["failure"])

    def test_a_timeout_is_never_recorded_as_a_zero_row_feed(self):
        for record in _manifest()["records"]:
            if not record["reached"]:
                self.assertIsNone(
                    record["byte_length"],
                    f"{record['key']} failed but carries a byte_length",
                )
                self.assertNotIn("rows", record)

    def test_official_html_pages_return_200(self):
        for key in STAT_PAGE_KEYS + ("injury_index",):
            record = _record(key)
            self.assertIsNotNone(record, f"missing capture record {key}")
            self.assertTrue(record["reached"], f"{key} was not reached")
            self.assertEqual(200, record["http_status"])
            self.assertGreater(record["byte_length"], 10_000)

    def test_cdn_static_json_is_refused_for_every_header_variant_tried(self):
        variants = (
            "cdn_live_scoreboard",
            "cdn_live_scoreboard_minimal",
            "cdn_live_scoreboard_no_ua",
            "cdn_static_schedule",
        )
        for key in variants:
            record = _record(key)
            self.assertIsNotNone(record, f"missing capture record {key}")
            self.assertEqual(403, record["http_status"], f"{key} status")
        # The header sets really do differ, so the 403 is path-level not request-level.
        self.assertNotEqual(
            _record("cdn_live_scoreboard")["headers_sent"],
            _record("cdn_live_scoreboard_no_ua")["headers_sent"],
        )

    def test_the_schedule_pdf_on_the_same_cdn_host_is_served(self):
        for key in ("schedule_pdf", "cdn_schedule_pdf_minimal"):
            record = _record(key)
            self.assertIsNotNone(record)
            self.assertEqual(200, record["http_status"])
            self.assertTrue(record["shape_check"]["starts_with_pdf_magic"])

    def test_data_nba_net_fails_on_certificate_validation(self):
        record = _record("data_nba_today")
        self.assertIsNotNone(record)
        self.assertFalse(record["reached"])
        self.assertIn("CERTIFICATE_VERIFY_FAILED", record["failure"])


class NextDataExtraction(unittest.TestCase):
    """The payload extractor, on real and on deliberately broken bodies."""

    def setUp(self) -> None:
        _require_captures(self)

    def test_all_four_stat_pages_carry_a_parsing_next_data_payload(self):
        for key in STAT_PAGE_KEYS:
            payload_path = CAPTURE_DIR / f"{key}.next.json"
            self.assertTrue(payload_path.is_file(), f"missing {payload_path.name}")
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertIsInstance(payload, dict)
            self.assertIn("props", payload)

    def test_a_truncated_body_refuses_rather_than_returning_partial_data(self):
        # teamstats_*.head.html is the first 300 KB of a ~322 KB response, so the
        # payload is cut mid-object. The extractor must not invent a closing brace.
        raw = (CAPTURE_DIR / "teamstats_traditional.head.html").read_bytes()
        marker_found, payload = op.extract_next_data(raw)
        self.assertTrue(marker_found)
        self.assertIsNone(payload)

    def test_no_marker_means_no_payload(self):
        marker_found, payload = op.extract_next_data(b"<html><body>hello</body></html>")
        self.assertFalse(marker_found)
        self.assertIsNone(payload)

    def test_a_brace_inside_a_json_string_does_not_end_the_scan(self):
        body = (
            b'<html><script id="__NEXT_DATA__" type="application/json">'
            b'{"a": "not a } closing brace", "b": {"c": 1}}'
            b"</script></html>"
        )
        marker_found, payload = op.extract_next_data(body)
        self.assertTrue(marker_found)
        self.assertEqual({"a": "not a } closing brace", "b": {"c": 1}}, payload)

    def test_the_injury_index_is_not_a_next_js_app(self):
        raw = (CAPTURE_DIR / "injury_index.head.html").read_bytes()
        marker_found, _ = op.extract_next_data(raw)
        self.assertFalse(marker_found)


class RowContractClassification(unittest.TestCase):
    """A 200 response is not evidence of data."""

    def setUp(self) -> None:
        _require_captures(self)

    def test_the_four_stat_pages_are_rendered_shells(self):
        for key in STAT_PAGE_KEYS:
            verdict = op.classify_body(key, b"")  # guards the KeyError path below
            self.assertFalse(verdict.ok)
            payload = json.loads((CAPTURE_DIR / f"{key}.next.json").read_text(encoding="utf-8"))
            verdict = op.classify_payload(key, payload)
            self.assertEqual(op.NO_DATA_IN_BODY, verdict.verdict, key)
            self.assertEqual(0, verdict.rows)
            self.assertFalse(verdict.ok)
            self.assertIn("rendered shell", verdict.detail)

    def test_a_payload_that_does_carry_thirty_rows_passes(self):
        payload = {
            "props": {
                "pageProps": {
                    "teams": [
                        {"team": f"Team {i}", "w": i, "l": 30 - i} for i in range(30)
                    ]
                }
            }
        }
        verdict = op.classify_payload("standings", payload)
        self.assertEqual(op.CARRIES_ROWS, verdict.verdict)
        self.assertEqual(30, verdict.rows)
        self.assertTrue(verdict.ok)
        self.assertIn("props.pageProps.teams", verdict.evidence["row_list_paths"])

    def test_a_list_of_the_wrong_length_does_not_satisfy_the_contract(self):
        payload = {"props": {"pageProps": {"teams": [{"a": 1, "b": 2, "c": 3}] * 29}}}
        self.assertEqual(op.NO_DATA_IN_BODY, op.classify_payload("standings", payload).verdict)

    def test_an_empty_body_is_never_a_satisfied_feed(self):
        verdict = op.classify_body("standings", b"")
        self.assertEqual(op.EMPTY_BODY, verdict.verdict)
        self.assertFalse(verdict.ok)

    def test_a_server_rendered_table_without_next_data_is_honoured(self):
        rows = "".join(
            f"<tr><td>{i}</td><td>value</td></tr>" for i in range(30)
        )
        body = f"<table><tbody>{rows}</tbody></table>"
        verdict = op.classify_body("standings", body.encode("utf-8"))
        self.assertEqual(op.CARRIES_ROWS, verdict.verdict)
        self.assertEqual(30, verdict.rows)

    def test_the_schedule_pdf_satisfies_its_contract(self):
        verdict = op.classify_body(
            "schedule_pdf",
            (CAPTURE_DIR / "schedule_pdf.pdf").read_bytes(),
        )
        self.assertEqual(op.CARRIES_ROWS, verdict.verdict)
        self.assertTrue(verdict.evidence["starts_with_pdf_magic"])

    def test_a_pdf_shaped_body_that_is_not_a_pdf_is_refused(self):
        verdict = op.classify_body("schedule_pdf", b"<html>access denied</html>")
        self.assertEqual(op.NOT_THE_DECLARED_SHAPE, verdict.verdict)

    def test_an_undeclared_page_key_is_an_error_not_a_guess(self):
        with self.assertRaises(KeyError):
            op.classify_body("some_page_nobody_declared", b"<html></html>")

    def test_the_captured_directory_classifies_end_to_end(self):
        verdicts = {v.spec_key: v for v in op.classify_capture(CAPTURE_DIR)}
        self.assertEqual(set(STAT_PAGE_KEYS) | {"injury_index", "schedule_pdf"}, set(verdicts))
        for key in STAT_PAGE_KEYS:
            self.assertFalse(verdicts[key].ok, key)
        self.assertTrue(verdicts["injury_index"].ok)
        self.assertTrue(verdicts["schedule_pdf"].ok)


class InjuryIndexParsing(unittest.TestCase):
    """`official.nba.com` server-renders its links, so the body does carry data."""

    def setUp(self) -> None:
        _require_captures(self)
        html = (CAPTURE_DIR / "injury_index.head.html").read_text(encoding="utf-8", errors="replace")
        self.read = op.parse_injury_index(html)

    def test_the_index_carries_report_links(self):
        self.assertGreaterEqual(self.read.report_count, 1)

    def test_every_link_sits_on_an_official_host(self):
        for report in self.read.reports:
            self.assertTrue(
                report.url.startswith("https://") and "nba.com" in report.url,
                report.url,
            )

    def test_the_printed_label_agrees_with_the_filename_clock(self):
        # Two independent fields in the same document must agree. "12:00 a.m ET
        # report" has to belong to Injury-Report_..._12_00AM.pdf.
        for report in self.read.reports:
            # The page prints "12:00 a.m ET report" / "1:00 a.m ET report" while
            # the filename carries 12_00AM / 01_00AM, so the label's hour is
            # compared without a leading zero (flag BU-03 records the drift).
            meridiem = report.ampm.lower()[0] + ".m"
            expected = f"{report.hour}:{report.minute:02d} {meridiem}"
            self.assertTrue(
                report.label.lower().startswith(expected),
                f"label {report.label!r} does not start with {expected!r}",
            )
            self.assertIn(f"{report.hour:02d}_{report.minute:02d}{report.ampm}", report.url)

    def test_every_filename_carries_the_same_date_as_the_page_header(self):
        self.assertEqual(1, len(self.read.dates))
        self.assertTrue(self.read.date_headers)
        date = self.read.dates[0]
        for report in self.read.reports:
            self.assertEqual(date, report.date)
            self.assertIn(f"Injury-Report_{date}_", report.url)

    def test_links_are_unique_and_ordered_oldest_first(self):
        urls = [report.url for report in self.read.reports]
        self.assertEqual(len(urls), len(set(urls)))
        keys = [report.sort_key for report in self.read.reports]
        self.assertEqual(sorted(keys), keys)

    def test_the_newest_link_is_the_latest_clock(self):
        newest = self.read.newest
        self.assertIsNotNone(newest)
        for report in self.read.reports:
            self.assertLessEqual(report.sort_key, newest.sort_key)

    def test_newest_report_link_helper_returns_the_same_answer(self):
        html = (CAPTURE_DIR / "injury_index.head.html").read_text(encoding="utf-8", errors="replace")
        self.assertEqual(self.read.newest.url, op.newest_report_link(html).url)

    def test_a_page_with_no_report_links_yields_none_not_a_fabricated_link(self):
        self.assertIsNone(op.newest_report_link("<html><body>nothing here</body></html>"))
        self.assertEqual(0, op.parse_injury_index("<html></html>").report_count)

    def test_a_report_link_on_a_non_official_host_is_dropped(self):
        html = (
            '<a href="https://example.com/referee/injury/'
            'Injury-Report_2026-11-17_09_00AM.pdf">9:00 a.m report</a>'
        )
        self.assertEqual(0, op.parse_injury_index(html).report_count)

    def test_the_index_verdict_says_it_carries_rows(self):
        verdict = op.classify_body(
            "injury_index",
            (CAPTURE_DIR / "injury_index.head.html").read_bytes(),
        )
        self.assertEqual(op.CARRIES_ROWS, verdict.verdict)
        self.assertEqual(self.read.report_count, verdict.rows)
        self.assertEqual([self.read.dates[0]], verdict.evidence["dates"])


class PageSpecIntegrity(unittest.TestCase):
    """The declared contracts themselves."""

    def test_every_spec_declares_https_urls_on_an_official_host(self):
        for key, spec in op.PAGE_SPECS.items():
            for url in (spec.page_url, spec.transport_url):
                self.assertTrue(url.startswith("https://"), f"{key}: {url}")
                self.assertIn("nba.com", url, f"{key}: {url}")

    def test_every_spec_declares_a_positive_expected_row_count(self):
        for key, spec in op.PAGE_SPECS.items():
            self.assertGreaterEqual(spec.expected_rows, 1, key)

    def test_the_stat_pages_transport_and_cited_source_are_different_urls(self):
        # Recorded, not fixed: the job fetches stats.nba.com while the site cites
        # www.nba.com. They are not the same document and the difference matters.
        for key in STAT_PAGE_KEYS:
            spec = op.PAGE_SPECS[key]
            self.assertNotEqual(spec.page_url, spec.transport_url)
            self.assertIn("stats.nba.com", spec.transport_url)
            self.assertIn("www.nba.com", spec.page_url)

    def test_the_injury_index_and_schedule_pdf_are_their_own_transport(self):
        for key in ("injury_index", "schedule_pdf"):
            spec = op.PAGE_SPECS[key]
            self.assertEqual(spec.page_url, spec.transport_url)

    def test_reachability_rows_report_every_captured_record(self):
        _require_captures(self)
        rows = op.reachability_rows(_manifest())
        self.assertEqual(len(rows), len(_manifest()["records"]))
        for row in rows:
            self.assertIn("reached", row)
            if row["reached"]:
                self.assertEqual(200, row["http_status"])
            else:
                self.assertTrue(row["failure"])


if __name__ == "__main__":
    unittest.main()
