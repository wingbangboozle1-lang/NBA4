#!/usr/bin/env python3
"""Official-page transport contracts, body classifier and injury-index parser.

Task BU/BV (session `arena/af666c53-nba4`). This module exists because the
scheduled refresh job's four red fetch gates (BH-05 / P11-01) could not be
attributed to a cause: `scripts/scheduled_refresh.py` fetches the standings and
the three team-stat feeds from the `stats.nba.com` JSON API, and no session had
ever observed what that host does from a GitHub-hosted runner.

The observation is now recorded in `data/official-pages/<date>/manifest.json`,
captured by `scripts/capture_official_pages.py` on a runner with unrestricted
egress. The short version:

* `stats.nba.com` times out (no HTTP response at all) from the runner.
* `www.nba.com/standings` and `www.nba.com/stats/teams/{traditional,opponent,
  advanced}` return **HTTP 200**, but their raw bodies carry **none** of the
  statistics: the pages are client-rendered shells and the tables are fetched by
  the browser afterwards.
* `cdn.nba.com/static/json/**` returns **403 for every header set tried**, while
  the schedule PDF on the same host returns 200 — a path-level refusal.
* `official.nba.com` (the injury-report index) is server-rendered and does carry
  its data.

The dangerous reading of "the HTML pages return 200" is to switch the feed to the
HTML URL and declare the gate green. That is exactly the BH-06 false-green
failure mode. So this module does the opposite: it turns "200 OK" into a
*verdict about the body*, and a body without rows is a failure with a reason,
never a pass.

Everything here is offline. No function makes a network call; every function
runs against a captured body, so every claim in the tests is reproducible from
files in this repository.

Usage:
    python3 scripts/official_pages.py --manifest data/official-pages/<date>/manifest.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / "data" / "official-pages"

NEXT_MARKER = b'id="__NEXT_DATA__"'

# Verdicts a body can earn. The only passing verdict is CARRIES_ROWS.
CARRIES_ROWS = "CARRIES_ROWS"
NO_DATA_IN_BODY = "NO_DATA_IN_BODY"
EMPTY_BODY = "EMPTY_BODY"
NOT_THE_DECLARED_SHAPE = "NOT_THE_DECLARED_SHAPE"

REPORT_LINK_RE = re.compile(
    r"Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})(AM|PM)\.pdf"
)
PDF_HOST_RE = re.compile(r"https://[a-z0-9.-]*\.?nba\.com/")


@dataclass(frozen=True)
class PageSpec:
    """The declared contract for one official page.

    ``expected_rows`` is the count the page is required to supply before any
    downstream step is allowed to use it. ``transport`` names the URL the
    scheduled job currently targets; ``page_url`` names the official page a human
    would open — they are deliberately different fields, because the job's
    transport and the cited source have drifted apart.
    """

    key: str
    page_url: str
    transport_url: str
    kind: str  # "html" | "json" | "pdf"
    expected_rows: int
    note: str = ""

    def source_url(self) -> str:
        """The URL to cite in a table row: the page a reader can open."""
        return self.page_url


PAGE_SPECS: dict[str, PageSpec] = {
    spec.key: spec
    for spec in (
        PageSpec(
            key="standings",
            page_url="https://www.nba.com/standings",
            transport_url=(
                "https://stats.nba.com/stats/leaguestandingsv3"
                "?LeagueID=00&Season=2026-27&SeasonType=Regular%20Season"
            ),
            kind="html",
            expected_rows=30,
            note="one row per NBA team",
        ),
        PageSpec(
            key="teamstats_traditional",
            page_url="https://www.nba.com/stats/teams/traditional",
            transport_url=(
                "https://stats.nba.com/stats/leaguedashteamstats"
                "?LeagueID=00&Season=2026-27&SeasonType=Regular%20Season"
                "&PerMode=Totals&MeasureType=Base"
            ),
            kind="html",
            expected_rows=30,
            note="one row per NBA team",
        ),
        PageSpec(
            key="teamstats_opponent",
            page_url="https://www.nba.com/stats/teams/opponent",
            transport_url=(
                "https://stats.nba.com/stats/leaguedashteamstats"
                "?LeagueID=00&Season=2026-27&SeasonType=Regular%20Season"
                "&PerMode=Totals&MeasureType=Opponent"
            ),
            kind="html",
            expected_rows=30,
            note="one row per NBA team",
        ),
        PageSpec(
            key="teamstats_advanced",
            page_url="https://www.nba.com/stats/teams/advanced",
            transport_url=(
                "https://stats.nba.com/stats/leaguedashteamstats"
                "?LeagueID=00&Season=2026-27&SeasonType=Regular%20Season"
                "&PerMode=Totals&MeasureType=Advanced"
            ),
            kind="html",
            expected_rows=30,
            note="one row per NBA team",
        ),
        PageSpec(
            key="injury_index",
            page_url="https://official.nba.com/nba-injury-report-2026-27-season/",
            transport_url="https://official.nba.com/nba-injury-report-2026-27-season/",
            kind="html",
            expected_rows=1,
            note="at least one dated report link; the count varies through the day",
        ),
        PageSpec(
            key="schedule_pdf",
            page_url="https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf",
            transport_url="https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf",
            kind="pdf",
            expected_rows=1,
            note="the official schedule PDF; row counting is the schedule parser's job",
        ),
    )
}


# --------------------------------------------------------------------------
# Next.js payload extraction
# --------------------------------------------------------------------------

def extract_next_data(raw: bytes) -> tuple[bool, dict[str, Any] | None]:
    """Return ``(marker_found, payload)`` for a Next.js ``__NEXT_DATA__`` blob.

    The scan is byte-exact: it walks forward from the first ``{`` after the
    marker, tracking string state, so a brace inside a JSON string cannot end the
    scan early. ``marker_found`` and ``payload`` are reported separately because
    "the page is a Next.js app" and "its payload parsed" are different facts, and
    collapsing them is how a partial read gets mistaken for a complete one.
    """
    start = raw.find(NEXT_MARKER)
    if start < 0:
        return False, None
    open_brace = raw.find(b"{", start)
    if open_brace < 0:
        return True, None
    depth = 0
    in_string = False
    escaped = False
    index = open_brace
    while index < len(raw):
        byte = raw[index : index + 1]
        if in_string:
            if escaped:
                escaped = False
            elif byte == b"\\":
                escaped = True
            elif byte == b'"':
                in_string = False
        elif byte == b'"':
            in_string = True
        elif byte == b"{":
            depth += 1
        elif byte == b"}":
            depth -= 1
            if depth == 0:
                try:
                    payload = json.loads(raw[open_brace : index + 1].decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return True, None
                return True, payload if isinstance(payload, dict) else None
        index += 1
    return True, None


def find_row_lists(payload: Any, expected_rows: int, *, min_fields: int = 3) -> list[str]:
    """Every dotted path in ``payload`` holding a plausible table of rows.

    A "plausible table" is a list of exactly ``expected_rows`` dicts, each with
    at least ``min_fields`` keys. This is deliberately a *search* rather than a
    fixed pointer: the point of the exercise is that nobody knew where (or
    whether) the rows live, and a search reports the truth either way.
    """
    found: list[str] = []

    def walk(node: Any, path: str, depth: int) -> None:
        if depth > 12:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else key, depth + 1)
        elif isinstance(node, list):
            if (
                len(node) == expected_rows
                and node
                and all(isinstance(item, dict) and len(item) >= min_fields for item in node)
            ):
                found.append(path or "[]")
            for position, value in enumerate(node[: expected_rows + 2]):
                walk(value, f"{path}[{position}]", depth + 1)

    walk(payload, "", 0)
    return found


# --------------------------------------------------------------------------
# Body classification
# --------------------------------------------------------------------------

@dataclass
class Verdict:
    spec_key: str
    source_url: str
    transport_url: str
    verdict: str
    rows: int = 0
    evidence: dict[str, Any] = field(default_factory=dict)
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.verdict == CARRIES_ROWS

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.spec_key,
            "source_url": self.source_url,
            "transport_url": self.transport_url,
            "verdict": self.verdict,
            "rows": self.rows,
            "ok": self.ok,
            "detail": self.detail,
            "evidence": self.evidence,
        }


def classify_payload(key: str, payload: dict[str, Any] | None) -> Verdict:
    """Apply the declared row contract to an already-extracted Next.js payload.

    Split out from :func:`classify_body` so a payload captured whole (the
    ``<key>.next.json`` file, extracted from the complete response) can be judged
    without re-reading a body that may have been stored truncated. A truncated
    body is a legitimate input to :func:`classify_body` and must fail there, but
    it must not be mistaken for a complete read.
    """
    if key not in PAGE_SPECS:
        raise KeyError(f"no PageSpec declared for {key!r}")
    spec = PAGE_SPECS[key]
    if payload is None:
        return Verdict(
            key, spec.source_url(), spec.transport_url, NOT_THE_DECLARED_SHAPE,
            evidence={"next_data_marker": True, "payload_parsed": False},
            detail="__NEXT_DATA__ marker present but the payload did not parse as JSON",
        )
    paths = find_row_lists(payload, spec.expected_rows)
    if paths:
        return Verdict(
            key, spec.source_url(), spec.transport_url, CARRIES_ROWS,
            rows=spec.expected_rows,
            evidence={"next_data_marker": True, "row_list_paths": paths[:5]},
            detail=f"found {len(paths)} list(s) of {spec.expected_rows} rows: {paths[:3]}",
        )
    return Verdict(
        key, spec.source_url(), spec.transport_url, NO_DATA_IN_BODY,
        evidence={
            "next_data_marker": True,
            "payload_parsed": True,
            "top_level_keys": sorted(payload)[:10],
            "lists_of_expected_length": 0,
        },
        detail=(
            f"the page returned 200 and its Next.js payload parsed, but no list of "
            f"{spec.expected_rows} rows exists in it: the statistics are loaded by the "
            f"browser after the response, so this body is a rendered shell, not a feed"
        ),
    )


def classify_body(key: str, raw: bytes) -> Verdict:
    """Decide whether a captured body actually carries the rows it must supply.

    A 200 response is not evidence of data. This is the guard that keeps the
    scheduled job from turning green on a rendered shell.
    """
    if key not in PAGE_SPECS:
        raise KeyError(f"no PageSpec declared for {key!r}")
    spec = PAGE_SPECS[key]
    if not raw:
        return Verdict(
            key, spec.source_url(), spec.transport_url, EMPTY_BODY,
            detail="the body is empty; an empty body is never a satisfied feed",
        )

    if spec.kind == "pdf":
        is_pdf = raw[:5] == b"%PDF-"
        return Verdict(
            key, spec.source_url(), spec.transport_url,
            CARRIES_ROWS if is_pdf else NOT_THE_DECLARED_SHAPE,
            rows=1 if is_pdf else 0,
            evidence={"starts_with_pdf_magic": is_pdf, "byte_length": len(raw)},
            detail="PDF magic present" if is_pdf else "body does not start with %PDF-",
        )

    text = raw.decode("utf-8", "replace")

    if key == "injury_index":
        read = parse_injury_index(text)
        required = spec.expected_rows
        ok = read.report_count >= required
        return Verdict(
            key, spec.source_url(), spec.transport_url,
            CARRIES_ROWS if ok else NO_DATA_IN_BODY,
            rows=read.report_count,
            evidence={
                "report_count": read.report_count,
                "dates": read.dates,
                "date_headers": read.date_headers,
                "newest_report": read.newest.url if read.newest else None,
            },
            detail=(
                f"{read.report_count} dated report link(s) parsed from the server-rendered page"
                if ok
                else f"expected at least {required} report link, found {read.report_count}"
            ),
        )

    marker_found, payload = extract_next_data(raw)
    if marker_found:
        return classify_payload(key, payload)
    if not marker_found:
        # Not a Next.js payload: fall back to a direct table scan so a
        # server-rendered <table> would still be honoured.
        rows = len(re.findall(r"<tr", text, re.I))
        return Verdict(
            key, spec.source_url(), spec.transport_url,
            CARRIES_ROWS if rows >= spec.expected_rows else NO_DATA_IN_BODY,
            rows=rows,
            evidence={"next_data_marker": False, "tr_elements": rows},
            detail=f"no __NEXT_DATA__ payload; {rows} <tr> element(s) in the raw body",
        )
    if payload is None:
        return Verdict(
            key, spec.source_url(), spec.transport_url, NOT_THE_DECLARED_SHAPE,
            evidence={"next_data_marker": True, "payload_parsed": False},
            detail="__NEXT_DATA__ marker present but the payload did not parse as JSON",
        )

    paths = find_row_lists(payload, spec.expected_rows)
    if paths:
        return Verdict(
            key, spec.source_url(), spec.transport_url, CARRIES_ROWS,
            rows=spec.expected_rows,
            evidence={"next_data_marker": True, "row_list_paths": paths[:5]},
            detail=f"found {len(paths)} list(s) of {spec.expected_rows} rows: {paths[:3]}",
        )
    return Verdict(
        key, spec.source_url(), spec.transport_url, NO_DATA_IN_BODY,
        evidence={
            "next_data_marker": True,
            "payload_parsed": True,
            "top_level_keys": sorted(payload)[:10],
            "lists_of_expected_length": 0,
        },
        detail=(
            f"the page returned 200 and its Next.js payload parsed, but no list of "
            f"{spec.expected_rows} rows exists in it: the statistics are loaded by the "
            f"browser after the response, so this body is a rendered shell, not a feed"
        ),
    )


# --------------------------------------------------------------------------
# Injury-report index
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ReportLink:
    date: str
    hour: int
    minute: int
    ampm: str
    url: str
    label: str

    @property
    def sort_key(self) -> tuple[str, int, int]:
        hour = self.hour % 12
        if self.ampm.upper() == "PM":
            hour += 12
        return (self.date, hour, self.minute)

    @property
    def clock(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d} {self.ampm.upper()}"


@dataclass
class InjuryIndexRead:
    reports: list[ReportLink]
    date_headers: list[str]

    @property
    def report_count(self) -> int:
        return len(self.reports)

    @property
    def dates(self) -> list[str]:
        return sorted({report.date for report in self.reports})

    @property
    def newest(self) -> ReportLink | None:
        if not self.reports:
            return None
        return max(self.reports, key=lambda report: report.sort_key)


def parse_injury_index(html: str) -> InjuryIndexRead:
    """Parse the dated report links out of the official injury-report index.

    ``official.nba.com`` is WordPress and server-renders its links, so unlike the
    stats pages this page's body really does carry its data. The parser keeps the
    URL as printed (it is the authoritative artefact) and derives the date and
    clock from both the filename and the anchor text, refusing a link where the
    two disagree rather than picking one.
    """
    reports: list[ReportLink] = []
    seen: set[str] = set()
    for match in re.finditer(
        r'<a\s+[^>]*href="(?P<href>[^"]+Injury-Report_(?P<date>\d{4}-\d{2}-\d{2})_'
        r"(?P<hour>\d{2})_(?P<minute>\d{2})(?P<ampm>AM|PM)\.pdf)\"[^>]*>(?P<label>.*?)</a>",
        html,
        re.I | re.S,
    ):
        href = match.group("href")
        if href in seen:
            continue
        seen.add(href)
        if not PDF_HOST_RE.search(href):
            continue
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group("label"))).strip()
        reports.append(
            ReportLink(
                date=match.group("date"),
                hour=int(match.group("hour")),
                minute=int(match.group("minute")),
                ampm=match.group("ampm").upper(),
                url=href,
                label=label,
            )
        )
    headers = [
        re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", header)).strip().rstrip(":")
        for header in re.findall(r"<b>(.*?)</b>", html, re.I | re.S)
    ]
    return InjuryIndexRead(reports=sorted(reports, key=lambda r: r.sort_key), date_headers=headers)


def newest_report_link(html: str) -> ReportLink | None:
    """The newest report on the index page, or None when the page carries none.

    Returning None rather than raising lets the caller record NOT_RETRIEVED; a
    page with no links is not the same thing as a page that was never fetched.
    """
    return parse_injury_index(html).newest


# --------------------------------------------------------------------------
# Reachability reporting
# --------------------------------------------------------------------------

def reachability_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a capture manifest into rows for the transport table.

    A record is reported exactly as captured: REACHED, or NOT REACHED with the
    failure text. A timeout is never rewritten as a zero-row feed.
    """
    rows: list[dict[str, Any]] = []
    for record in manifest.get("records", []):
        rows.append(
            {
                "key": record.get("key"),
                "url": record.get("url"),
                "reached": bool(record.get("reached")),
                "http_status": record.get("http_status"),
                "byte_length": record.get("byte_length"),
                "failure": record.get("failure"),
                "retrieved_at_utc": record.get("retrieved_at_utc"),
            }
        )
    return rows


def classify_capture(capture_dir: Path) -> list[Verdict]:
    """Classify every captured body in a directory against its declared spec."""
    verdicts: list[Verdict] = []
    for key in PAGE_SPECS:
        # Order matters. `<key>.next.json` is the payload extracted from the
        # complete response, so it is judged first. Only if it is absent is the
        # raw body used, and a body stored truncated will (correctly) fail there.
        payload_path = capture_dir / f"{key}.next.json"
        if payload_path.is_file():
            try:
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = None
            verdicts.append(classify_payload(key, payload))
            continue
        for suffix in ("", ".body.json", ".head.html", ".pdf"):
            candidate = capture_dir / f"{key}{suffix}"
            if candidate.is_file():
                verdicts.append(classify_body(key, candidate.read_bytes()))
                break
    return verdicts


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="path to a capture manifest.json to summarise",
    )
    parser.add_argument(
        "--capture-dir",
        type=Path,
        default=None,
        help="directory of captured bodies to classify against the declared specs",
    )
    args = parser.parse_args(argv)

    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        print(f"reachability captured {manifest['generated_at_utc']} on {manifest['runner']}")
        for row in reachability_rows(manifest):
            state = "REACHED" if row["reached"] else "NOT REACHED"
            detail = row["failure"] or f"HTTP {row['http_status']} ({row['byte_length']} bytes)"
            print(f"  {state:12} {row['key']:28} {detail}")
    if args.capture_dir:
        print(f"\nbody verdicts for {args.capture_dir}")
        for verdict in classify_capture(args.capture_dir):
            print(f"  {verdict.verdict:24} {verdict.spec_key:24} rows={verdict.rows}")
            print(f"      {verdict.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
