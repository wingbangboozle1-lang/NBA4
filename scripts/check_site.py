#!/usr/bin/env python3
"""Static integrity checks for NBA4's source-linked GitHub Pages site."""

from __future__ import annotations

import re
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html",
    "slate.html",
    "injuries.html",
    "results.html",
    "line-origination.html",
    "automation.html",
    "strategies.html",
    "leaderboard.html",
    "questions.html",
    "suggestions.html",
    "sources.html",
    "review.html",
)
# The unified sidebar: every page must carry exactly these 12 links in this
# order, with no duplicates and with aria-current pointing at its own page.
CANONICAL_NAV = tuple(PAGES)
OFFICIAL_HOSTS = (
    "nba.com",
    "github.com",
    "wingbangboozle1-lang.github.io",  # this project's own published site
    "kansspelautoriteit.nl",
    "scikit-learn.org",
    "itl.nist.gov",
    "nist.gov",
)


def is_official_https(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(host == domain or host.endswith("." + domain) for domain in OFFICIAL_HOSTS)


class PageAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.h1_count = 0
        self.in_title = False
        self.in_h1 = False
        self.title_text: list[str] = []
        self.h1_text: list[str] = []
        self.nav_links: list[str] = []
        self.nav_current: list[str] = []
        self._in_primary_nav = False
        self.table_rows = 0
        self.bad_rows: list[int] = []
        self._row_number = 0
        self._row_has_td = False
        self._last_td_official = False
        self._cell_official = False
        self._in_td = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if attrs_dict.get("id"):
            self.ids.add(attrs_dict["id"] or "")
        if tag == "nav" and attrs_dict.get("class") == "primary-nav":
            self._in_primary_nav = True
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.in_h1 = True
            self.h1_count += 1
        elif tag == "tr":
            self._row_number += 1
            self._row_has_td = False
            self._last_td_official = False
            self._in_td = False
        elif tag == "td":
            self._row_has_td = True
            self._in_td = True
            self._cell_official = False
        elif tag == "a":
            href = attrs_dict.get("href") or ""
            self.links.append(href)
            if self._in_primary_nav:
                self.nav_links.append(href)
                if attrs_dict.get("aria-current") == "page":
                    self.nav_current.append(href)
            if self._in_td and is_official_https(href):
                self._cell_official = True
        elif tag == "link":
            self.links.append(attrs_dict.get("href") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self._in_primary_nav:
            self._in_primary_nav = False
        elif tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "td":
            if self._in_td:
                self._last_td_official = self._cell_official
            self._in_td = False
        elif tag == "tr" and self._row_has_td:
            self.table_rows += 1
            if not self._last_td_official:
                self.bad_rows.append(self._row_number)

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_text.append(data)
        if self.in_h1:
            self.h1_text.append(data)


def is_local_target(href: str) -> tuple[Path, str | None] | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith("//") or not parsed.path:
        return None
    target = (ROOT / parsed.path).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return (target, parsed.fragment or None)
    return (target, parsed.fragment or None)


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}


class NestingAudit(HTMLParser):
    """Stack check: every closing tag must match the most recent open tag."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.problems: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_ELEMENTS:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            top = self.stack[-1] if self.stack else "nothing"
            self.problems.append(f"</{tag}> closes while <{top}> is open at {self.getpos()}")


def audit_nesting(path: Path) -> list[str]:
    audit = NestingAudit()
    audit.feed(path.read_text(encoding="utf-8"))
    audit.close()
    problems = list(audit.problems)
    if audit.stack:
        problems.append(f"unclosed element(s) at end of page: {audit.stack[-5:]}")
    return problems


def audit_page(name: str) -> tuple[list[str], int]:
    errors: list[str] = []
    path = ROOT / name
    if not path.is_file():
        return [f"missing page: {name}"], 0
    errors.extend(f"{name}: invalid nesting: {p}" for p in audit_nesting(path))
    parser = PageAudit()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    if not "".join(parser.title_text).strip():
        errors.append(f"{name}: missing <title>")
    if parser.h1_count != 1 or not "".join(parser.h1_text).strip():
        errors.append(f"{name}: expected exactly one non-empty <h1>, found {parser.h1_count}")
    if parser.bad_rows:
        errors.append(f"{name}: table data row(s) missing an official HTTPS source in the final cell: {parser.bad_rows}")
    if tuple(parser.nav_links) != CANONICAL_NAV:
        duplicates = sorted({href for href in parser.nav_links if parser.nav_links.count(href) > 1})
        if duplicates:
            errors.append(f"{name}: duplicate sidebar link(s): {duplicates}")
        errors.append(
            f"{name}: sidebar navigation must be the canonical {len(CANONICAL_NAV)}-item list in order; "
            f"found {parser.nav_links!r}"
        )
    if parser.nav_current != [name]:
        errors.append(
            f"{name}: expected exactly one sidebar aria-current=\"page\" on its own link, found {parser.nav_current!r}"
        )

    for href in parser.links:
        parsed_href = urlsplit(href)
        if not parsed_href.scheme and not parsed_href.netloc and not parsed_href.path and parsed_href.fragment:
            if parsed_href.fragment not in parser.ids:
                errors.append(f"{name}: missing local fragment #{parsed_href.fragment}")
            continue
        target_info = is_local_target(href)
        if target_info is None:
            continue
        target, fragment = target_info
        if not target.is_file():
            errors.append(f"{name}: broken local link {href!r}")
            continue
        if fragment:
            try:
                target_parser = PageAudit()
                target_parser.feed(target.read_text(encoding="utf-8"))
                target_parser.close()
            except (UnicodeDecodeError, OSError):
                continue
            if fragment not in target_parser.ids:
                errors.append(f"{name}: missing local fragment #{fragment} in {target}")
    return errors, parser.table_rows


def audit_markdown_tables() -> tuple[list[str], int]:
    errors: list[str] = []
    row_count = 0
    for path in sorted((ROOT / "docs").glob("*.md")):
        in_table = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("|"):
                in_table = False
                continue
            if not line.replace("|", "").replace("-", "").replace(":", "").strip():
                continue
            if not in_table:  # Header row
                in_table = True
                continue
            row_count += 1
            urls = [part.split(")", 1)[0] for part in line.split("](")[1:]]
            if not any(is_official_https(url) for url in urls):
                errors.append(f"{path.relative_to(ROOT)}:{line_number}: table row missing an official HTTPS source link")
    return errors, row_count


def audit_consistency() -> list[str]:
    """Counts stated on the public pages must match the repository; primary navigation must not repeat links."""
    errors: list[str] = []
    tests = 0
    for path in (ROOT / "tests").glob("test_*.py"):
        tests += len(re.findall(r"^\s*def test_", path.read_text(encoding="utf-8"), re.M))
    # README may split the suite by file (e.g. "47 + 43") while the index states a
    # single total; each stated number must add up to the real count.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    stated = re.search(r"(\d+(?:\s*\+\s*\d+)*)\s+passing unit tests", readme)
    if not stated:
        errors.append("README.md does not state a passing unit-test count")
    elif sum(int(part) for part in re.findall(r"\d+", stated.group(1))) != tests:
        errors.append(
            f"README.md states {stated.group(1)} passing unit tests but the suite has {tests}"
        )
    checks = (("index.html", rf"\b{tests} unit tests\b"),)
    for name, pattern in checks:
        if not re.search(pattern, (ROOT / name).read_text(encoding="utf-8")):
            errors.append(f"{name} does not state the current engine unit-test count ({tests})")
    for name in PAGES:
        text = (ROOT / name).read_text(encoding="utf-8")
        nav = re.search(r'<nav class="primary-nav".*?</nav>', text, re.S)
        if nav:
            hrefs = re.findall(r'href="([^"]+)"', nav.group(0))
            repeated = sorted({href for href in hrefs if hrefs.count(href) > 1})
            if repeated:
                errors.append(f"{name}: primary navigation repeats {repeated}")
    return errors


def audit_snapshots() -> list[str]:
    """Published snapshot tables must be in sync and their data files must keep provenance."""
    import importlib.util

    errors: list[str] = []
    spec = importlib.util.spec_from_file_location(
        "build_snapshots", ROOT / "scripts" / "build_snapshots.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for block_id, (page_name, render) in module.BLOCKS.items():
        try:
            stale = module.splice(ROOT / page_name, block_id, render())
        except SystemExit as exc:  # missing markers
            errors.append(str(exc))
            continue
        if stale is not None:
            errors.append(
                f"{page_name}: snapshot table out of date; run python3 scripts/build_snapshots.py"
            )
    for path in sorted((ROOT / "data" / "snapshots").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON ({exc})")
            continue
        for key in ("source_url", "source_document_header", "fetched_at_utc", "extraction_tool"):
            if not payload.get(key):
                errors.append(f"{path.name}: missing provenance field {key}")
        if not str(payload.get("source_url", "")).startswith("https://"):
            errors.append(f"{path.name}: source_url is not https")
    return errors


def audit_page_inventory() -> list[str]:
    """Every HTML page in the repository root must be part of the checked set."""
    errors: list[str] = []
    on_disk = {path.name for path in ROOT.glob("*.html")}
    missing = on_disk - set(PAGES)
    for name in sorted(missing):
        errors.append(f"page present on disk but not in the checked page list: {name}")
    return errors


def run_engine_tests() -> list[str]:
    """Run the engine unit tests so a broken engine cannot be published."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"engine unit tests failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"]
    return []


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(audit_page_inventory())
    all_errors.extend(audit_snapshots())
    all_errors.extend(audit_consistency())
    html_rows = 0
    for name in PAGES:
        errors, row_count = audit_page(name)
        if errors:
            all_errors.extend(errors)
        else:
            html_rows += row_count
            print(f"OK {name}: title, heading, local links and {row_count} source-linked data rows")

    markdown_errors, markdown_rows = audit_markdown_tables()
    all_errors.extend(markdown_errors)
    css = ROOT / "assets/site.css"
    if not css.is_file():
        all_errors.append("missing assets/site.css")
    if (ROOT / ".nojekyll").is_file() is False:
        all_errors.append("missing .nojekyll marker for the static Pages site")

    if all_errors:
        print("\nSite check failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print(f"OK docs/*.md: {markdown_rows} source-linked data rows")

    if "--with-tests" in sys.argv[1:]:
        test_errors = run_engine_tests()
        if test_errors:
            print("\nSite check failed:")
            for error in test_errors:
                print(f"- {error}")
            return 1
        print("OK engine unit tests")

    print(f"\nPASS: {len(PAGES)} pages, {html_rows} HTML data rows and {markdown_rows} Markdown data rows passed.")
    print("External source URLs are checked for HTTPS and official hostnames; this script does not fetch the web.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
