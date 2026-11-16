"""The site integrity checker runs as part of the unit-test suite.

``scripts/check_site.py`` is the gate this repository publishes with: every
root HTML page must carry the canonical sidebar, one heading, valid nesting,
local links that resolve, and a table row's final cell must cite an official
HTTPS source. These tests call the same audit functions the script uses, so a
broken page fails ``python3 -m unittest`` as well as ``check_site.py``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_site  # noqa: E402


class SiteAuditTests(unittest.TestCase):
    def test_page_inventory_covers_every_root_html_file(self) -> None:
        self.assertEqual(check_site.audit_page_inventory(), [])

    def test_stated_counts_and_navigation_are_consistent(self) -> None:
        self.assertEqual(check_site.audit_consistency(), [])

    def test_every_page_audit_is_clean(self) -> None:
        for name in check_site.PAGES:
            with self.subTest(page=name):
                errors, row_count = check_site.audit_page(name)
                self.assertEqual(errors, [])
                self.assertGreater(row_count, 0, f"{name} publishes no source-linked data rows")

    def test_snapshot_tables_are_in_sync_and_provenanced(self) -> None:
        self.assertEqual(check_site.audit_snapshots(), [])

    def test_bet_gated_headings_stay_off_publish_safe_pages(self) -> None:
        self.assertEqual(check_site.audit_surfaces(), [])

    def test_markdown_tables_cite_official_sources(self) -> None:
        errors, row_count = check_site.audit_markdown_tables()
        self.assertEqual(errors, [])
        self.assertGreater(row_count, 0)


if __name__ == "__main__":
    unittest.main()
