#!/usr/bin/env python3
"""Scheduled refresh: fetch the official sources for the rolling slate, run the
freshness and provenance gates, and permit the site rebuild only when every gate
passes (brief item, 2026-11-16: "Extend the scheduled job to refresh the official
schedule, standings, team statistics and injury report for each rolling slate,
then rebuild only after freshness and provenance gates pass").

Task BH, session ``arena/cbc8e41a-nba4``. Design rules:

* **Fail closed.** Any gate that cannot be evaluated — unreachable source,
  unparsable document, missing provenance — is a FAIL, never a skip and never a
  default pass. ``rebuild_allowed`` is true only when *every* gate passed.
* **Fetch, freshness, provenance, build** — four phases, in that order. The build
  phase runs ``build_snapshots.py --check`` and ``check_site.py --with-tests``;
  the rebuild itself (re-running ``build_snapshots.py`` for its splice output) is
  performed by the caller only after this script exits 0 in ``gates`` mode.
* **No rights expansion.** The job archives and checks official publications
  (schedule PDF, injury index/PDFs, standings, the three team-stat pages). It
  originates no line, no probability and no pick; gate G0/D-01/IR-T4 are
  untouched. The injury PDF is verified for its printed header, never parsed
  into player rows here — row transcription stays a human-verified step, and
  that limit is recorded as a gate note, not hidden.
* **Modes.** ``gates`` (default, cron): every gate asserted, exit 1 on any
  failure. ``probe``: fetch-phase gates only are asserted (reachability and
  parseability); freshness failures are reported but do not fail the run, so a
  connectivity probe is distinguishable from a real staleness alarm. ``offline``:
  no network at all — provenance and build gates only (used by the unit tests
  and for local pre-push checks).

Only the Python standard library is required for fetching and gating; ``pypdf``
is optional and only needed to read the printed header of a fetched injury PDF
(when it is missing, the header gate fails closed with that exact reason).

Usage::

    python3 scripts/scheduled_refresh.py --mode gates --json run-record.json
    python3 scripts/scheduled_refresh.py --mode probe
    python3 scripts/scheduled_refresh.py --mode offline
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "data" / "snapshots"
RAW = SNAPSHOTS / "raw"

SCHEDULE_URL = "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
INJURY_INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
STANDINGS_API = (
    "https://stats.nba.com/stats/leaguestandingsv3"
    "?LeagueID=00&Season=2026-27&SeasonType=Regular%20Season"
)
TEAMSTAT_API = (
    "https://stats.nba.com/stats/leaguedashteamstats"
    "?LeagueID=00&Season=2026-27&SeasonType=Regular%20Season"
    "&PerMode=Totals&MeasureType={measure}"
)
TEAMSTAT_MEASURES = ("Base", "Advanced", "Opponent")

MAX_TRANSCRIPTION_AGE_H = 24.0
REPORT_LINK_RE = re.compile(r"Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})(AM|PM)\.pdf")
# Tolerant of layout extraction: the printed header can arrive split across
# lines or with irregular spacing ("Injury" + newline + "Report:"), so the text
# is whitespace-collapsed before matching (see parse_report_header).
REPORT_HEADER_RE = re.compile(r"Injury Report:\s*(\d{1,2})/(\d{1,2})/(\d{2})\s+(\d{1,2}):(\d{2})\s*(AM|PM)")

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
JSON_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com/",
    "Accept": "application/json, text/plain, */*",
    "X-NBA-Stats-Origin": "stats",
    "X-NBA-Stats-Token": "true",
}

# Task BV (session `arena/af666c53-nba4`). The four statistics feeds were only
# ever fetched from `stats.nba.com`, and when that host stopped answering the
# gates went red with "unreachable" and stayed red with no diagnosis. A probe run
# on a GitHub-hosted runner (see `data/official-pages/2026-11-17/manifest.json`)
# showed why: `stats.nba.com` returns no HTTP response at all from a runner,
# while the official pages a human opens return 200 but render their tables in
# the browser, so the raw body carries none of the statistics.
#
# The job therefore tries both transports and judges the *body*, not the status
# code. `official_pages.classify_body` returns CARRIES_ROWS only when the body
# really holds the declared number of rows; a 200 carrying a rendered shell is a
# failure with a reason, never a pass. That is the guard against the BH-06
# false-green: switching to a URL that answers 200 without changing what is
# verified would have manufactured a green check out of an empty feed.
HTML_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://www.nba.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _official_pages():
    """Load `scripts/official_pages.py` by path (this file runs as a script)."""
    import importlib.util

    module = sys.modules.get("official_pages")
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(
        "official_pages", Path(__file__).with_name("official_pages.py")
    )
    if spec is None or spec.loader is None:  # pragma: no cover - packaging error
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["official_pages"] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class Gate:
    name: str
    phase: str  # "fetch" | "freshness" | "provenance" | "build"
    passed: bool
    detail: str
    source_url: str = ""
    observed_at_utc: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate": self.name,
            "phase": self.phase,
            "status": "PASS" if self.passed else "FAIL",
            "detail": self.detail,
            "source_url": self.source_url,
            "observed_at_utc": self.observed_at_utc,
        }


@dataclass
class RunRecord:
    mode: str
    now_utc: str
    gates: list[Gate] = field(default_factory=list)
    fetches: dict[str, Any] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        return bool(self.gates) and all(g.passed for g in self.gates)

    @property
    def fetch_phase_ok(self) -> bool:
        fetches = [g for g in self.gates if g.phase == "fetch"]
        return bool(fetches) and all(g.passed for g in self.fetches_gates())

    def fetches_gates(self) -> list[Gate]:
        return [g for g in self.gates if g.phase == "fetch"]

    def failed(self) -> list[Gate]:
        return [g for g in self.gates if not g.passed]

    def exit_code(self) -> int:
        if self.mode == "probe":
            return 0 if self.fetch_phase_ok else 1
        return 0 if self.all_passed else 1

    def rebuild_allowed(self) -> bool:
        return self.mode == "gates" and self.all_passed

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": "scheduled_refresh_run_record",
            "script": "scripts/scheduled_refresh.py",
            "mode": self.mode,
            "now_utc": self.now_utc,
            "gates": [g.as_dict() for g in self.gates],
            "fetches": self.fetches,
            "summary": {
                "gates_total": len(self.gates),
                "gates_passed": sum(1 for g in self.gates if g.passed),
                "gates_failed": len(self.failed()),
                "failed": [g.name for g in self.failed()],
                "all_passed": self.all_passed,
                "rebuild_allowed": self.rebuild_allowed(),
                "exit_code": self.exit_code(),
            },
        }


# --- fetch layer (injectable for tests) -------------------------------------

FetchResult = tuple[int, bytes, str]  # status, body, final url


def default_fetch(url: str, *, headers: dict[str, str] | None = None, timeout: float = 30.0) -> FetchResult:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return int(resp.status), resp.read(), resp.geturl()
        except urllib.error.HTTPError as exc:
            return int(exc.code), exc.read() if exc.fp else b"", url
        except Exception as exc:  # noqa: BLE001 - network layer, fail closed below
            last_error = exc
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"fetch failed for {url}: {last_error}")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- parsers -----------------------------------------------------------------

def parse_newest_report_link(index_html: bytes | str) -> tuple[str, str] | None:
    """Return (url, 'YYYY-MM-DD HH:MM AM/PM') of the newest report listed, else None.

    The index prints one link per revision, grouped under a date heading; the
    newest revision is the maximum (date, time) among the links.
    """
    text = index_html.decode("utf-8", "replace") if isinstance(index_html, bytes) else index_html
    best: tuple[tuple[str, str], str] | None = None
    for match in REPORT_LINK_RE.finditer(text):
        date, hour, minute, ampm = match.groups()
        key = (date, f"{hour}:{minute} {ampm}")
        # Compare within the date first, then by clock time in 12h order.
        if best is None or _report_sort_key(key[0], key[1]) > _report_sort_key(best[0][0], best[0][1]):
            best = (key, match.group(0))
    if best is None:
        return None
    filename = best[1]
    return f"https://ak-static.cms.nba.com/referee/injury/{filename}", f"{best[0][0]} {best[0][1]}"


def _report_sort_key(date: str, clock: str) -> tuple[int, int, int, int, int, int]:
    year, month, day = (int(p) for p in date.split("-"))
    time_part, ampm = clock.split(" ")
    hour, minute = (int(p) for p in time_part.split(":"))
    hour12 = hour % 12
    if ampm == "PM":
        hour12 += 12
    return (year, month, day, hour12, minute, 0)


def parse_report_header(pdf_text: str) -> str | None:
    """Return the printed 'M/D/YY' date from the report header, or None.

    The input is whitespace-collapsed first so a header split across lines by
    the PDF text extractor still matches.
    """
    collapsed = re.sub(r"\s+", " ", pdf_text)
    match = REPORT_HEADER_RE.search(collapsed)
    if not match:
        return None
    month, day, year = match.group(1), match.group(2), match.group(3)
    return f"20{year}-{int(month):02d}-{int(day):02d}"


def header_matches_url(header_date: str | None, url: str) -> bool:
    match = REPORT_LINK_RE.search(url)
    return bool(match) and header_date == match.group(1)


def count_nba_rows(payload: bytes | str, *, expect: int = 30) -> tuple[int, bool]:
    """Row count from an NBA stats API ResultSet (or a pass-through fixture)."""
    try:
        doc = json.loads(payload)
    except Exception:
        text = payload.decode("utf-8", "replace") if isinstance(payload, bytes) else payload
        return text.count("16106127"), False
    try:
        result_sets = doc.get("ResultSet", {}).get("RowSet") or doc["resultSets"][0]["rowSet"]
    except Exception:
        return 0, False
    return len(result_sets), len(result_sets) == expect


def gate_official_feed(
    key: str,
    gate_name: str,
    fetch: Callable[..., Any],
    now: datetime,
) -> tuple[Gate, dict[str, Any]]:
    """Fetch one declared statistics feed, trying both known transports.

    Transport 1 is the ``stats.nba.com`` JSON API the job has always used.
    Transport 2 is the official page a reader opens (``www.nba.com/standings``
    and the three team-stat pages). Neither is trusted on its status code: the
    API body must yield the declared row count and the page body must be
    classified as actually carrying rows.

    Returns the gate and a summary for the run record. The summary always states
    which transport, if any, satisfied the contract, and every attempt that did
    not, so a red gate can be diagnosed from the record alone.
    """
    op = _official_pages()
    if op is None or key not in op.PAGE_SPECS:  # pragma: no cover - packaging error
        return (
            Gate(gate_name, "fetch", False, f"no declared page spec for {key}",
                 observed_at_utc=_iso(now)),
            {"transport_used": None},
        )
    spec = op.PAGE_SPECS[key]
    attempts: list[str] = []
    info: dict[str, Any] = {"transport_used": None, "attempts": attempts}

    # Transport 1: the JSON API.
    api_status = None
    try:
        api_status, body, _ = fetch(spec.transport_url, headers=JSON_HEADERS)
    except Exception as exc:  # noqa: BLE001 - the failure text is the diagnosis
        attempts.append(f"stats_api: {type(exc).__name__}: {exc}")
        body = None
    if body is not None:
        if api_status == 200:
            count, ok = count_nba_rows(body)
            attempts.append(f"stats_api: HTTP 200 rows={count}")
            if ok:
                info.update(transport_used="stats_api", rows=count, status=200)
                return (
                    Gate(gate_name, "fetch", True,
                         f"stats_api HTTP 200, rows={count} (expected {spec.expected_rows})",
                         source_url=spec.page_url, observed_at_utc=_iso(now)),
                    info,
                )
        else:
            attempts.append(f"stats_api: HTTP {api_status}")

    # Transport 2: the official page, judged on its body rather than its status.
    page_status = None
    try:
        page_status, page_body, _ = fetch(spec.page_url, headers=HTML_HEADERS)
    except Exception as exc:  # noqa: BLE001
        attempts.append(f"official_page: {type(exc).__name__}: {exc}")
        page_body = None
    if page_body is not None:
        if page_status == 200:
            verdict = op.classify_body(key, page_body)
            attempts.append(f"official_page: HTTP 200 verdict={verdict.verdict} rows={verdict.rows}")
            info["verdict"] = verdict.verdict
            if verdict.ok:
                info.update(transport_used="official_page", rows=verdict.rows, status=200)
                return (
                    Gate(gate_name, "fetch", True,
                         f"official_page HTTP 200, {verdict.rows} rows carried in the body",
                         source_url=spec.page_url, observed_at_utc=_iso(now)),
                    info,
                )
        else:
            attempts.append(f"official_page: HTTP {page_status}")

    detail = (
        f"no transport supplied {spec.expected_rows} rows; "
        + "; ".join(attempts)
        + " (a 200 that carries no rows is a rendered shell, not a satisfied feed)"
    )
    info["status"] = api_status if api_status is not None else page_status
    return (
        Gate(gate_name, "fetch", False, detail, source_url=spec.page_url,
             observed_at_utc=_iso(now)),
        info,
    )


def parse_slate_window(snapshot: dict[str, Any]) -> tuple[datetime, datetime] | None:
    """Return the slate's UTC half-open window from explicit bounds or its dates list.

    Snapshot producers historically used both ``window.start_utc/end_utc`` and
    ``window.dates``. Dates-only snapshots are interpreted as calendar dates in
    UTC, with the end boundary at midnight after the last listed date.
    """
    window = snapshot.get("window") or {}
    try:
        if window.get("start_utc") and window.get("end_utc"):
            start = datetime.fromisoformat(window["start_utc"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(window["end_utc"].replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
        else:
            dates = window.get("dates")
            if not isinstance(dates, list) or not dates:
                return None
            parsed = []
            for value in dates:
                if not isinstance(value, str):
                    return None
                try:
                    parsed.append(date.fromisoformat(value))
                except ValueError:
                    parsed.append(datetime.strptime(value, "%m/%d/%Y").date())
            if parsed != sorted(set(parsed)):
                return None
            start = datetime.combine(parsed[0], datetime.min.time(), tzinfo=timezone.utc)
            end = datetime.combine(parsed[-1] + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if end <= start:
        return None
    return start, end


def is_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


# --- gates -------------------------------------------------------------------

def gate_provenance(now: datetime) -> list[Gate]:
    """Every snapshot file must carry the provenance chain its kind requires."""
    gates: list[Gate] = []
    files = sorted(SNAPSHOTS.glob("*.json"))
    if not files:
        return [Gate("provenance_files", "provenance", False, "no snapshot files found", observed_at_utc=_iso(now))]
    bad: list[str] = []
    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append(f"{path.name}: unreadable JSON ({exc})")
            continue
        kind = str(doc.get("kind", ""))
        if kind.startswith("derived_"):
            if not doc.get("derived_from"):
                bad.append(f"{path.name}: derived file without derived_from")
            continue
        missing = [key for key in ("source_url", "fetched_at_utc") if not doc.get(key)]
        if missing:
            bad.append(f"{path.name}: missing {', '.join(missing)}")
    passed = not bad
    detail = (
        f"{len(files)} snapshot files carry the required provenance chain"
        if passed
        else "; ".join(bad[:5]) + (f" (+{len(bad) - 5} more)" if len(bad) > 5 else "")
    )
    gates.append(Gate("provenance_chain", "provenance", passed, detail, observed_at_utc=_iso(now)))
    return gates


def gate_build(now: datetime) -> list[Gate]:
    import subprocess

    gates: list[Gate] = []
    for name, argv in (
        ("build_snapshots_check", [sys.executable, "scripts/build_snapshots.py", "--check"]),
        ("site_check_with_tests", [sys.executable, "scripts/check_site.py", "--with-tests"]),
    ):
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or [""]
        gates.append(
            Gate(
                name,
                "build",
                proc.returncode == 0,
                f"exit {proc.returncode}: {tail[0][:200]}",
                observed_at_utc=_iso(now),
            )
        )
    return gates


def gate_freshness(
    now: datetime,
    *,
    pointer: dict[str, Any] | None,
    slate: dict[str, Any] | None,
    newest_report: str | None,
) -> list[Gate]:
    gates: list[Gate] = []

    # 1. The published transcription must be at most 24h old.
    if pointer and pointer.get("fetched_at_utc"):
        try:
            fetched = datetime.fromisoformat(str(pointer["fetched_at_utc"]).replace("Z", "+00:00"))
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=timezone.utc)
            age_h = (now - fetched).total_seconds() / 3600.0
            passed = 0 <= age_h <= MAX_TRANSCRIPTION_AGE_H
            gates.append(
                Gate(
                    "injury_transcription_age",
                    "freshness",
                    passed,
                    f"published transcription fetched_at {pointer['fetched_at_utc']}, age {age_h:.2f}h "
                    f"(limit {MAX_TRANSCRIPTION_AGE_H:.0f}h); newest report listed: "
                    f"{newest_report or 'not parsed'}",
                    source_url=str(pointer.get("source_url", "")),
                    observed_at_utc=_iso(now),
                )
            )
        except Exception as exc:
            gates.append(Gate("injury_transcription_age", "freshness", False, f"unparseable fetched_at: {exc}", observed_at_utc=_iso(now)))
    else:
        gates.append(Gate("injury_transcription_age", "freshness", False, "no injury pointer snapshot with fetched_at_utc", observed_at_utc=_iso(now)))

    # 2. The published slate window must contain the current moment.
    if slate:
        window = parse_slate_window(slate)
        if window:
            start, end = window
            passed = start <= now <= end
            gates.append(
                Gate(
                    "slate_window_current",
                    "freshness",
                    passed,
                    f"window {start.isoformat()} .. {end.isoformat()} vs now {_iso(now)}",
                    source_url=str(slate.get("source_url", "")),
                    observed_at_utc=_iso(now),
                )
            )
        else:
            gates.append(Gate("slate_window_current", "freshness", False, "slate snapshot has no parseable window", observed_at_utc=_iso(now)))
    else:
        gates.append(Gate("slate_window_current", "freshness", False, "no slate snapshot found", observed_at_utc=_iso(now)))
    return gates


def gate_schedule_drift(now: datetime, baseline_path: Path, current_sha: str | None) -> list[Gate]:
    if current_sha is None:
        return [Gate("schedule_pdf_fetch", "fetch", False, "schedule PDF was not fetched", observed_at_utc=_iso(now))]
    if not baseline_path.exists():
        # First run: record the baseline for the caller to persist; fetch provenance
        # still passed, so this gate passes with an explicit note.
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(current_sha + "\n", encoding="utf-8")
        return [
            Gate(
                "schedule_pdf_fetch",
                "fetch",
                True,
                f"schedule PDF fetched (sha256 {current_sha[:16]}…), baseline established",
                source_url=SCHEDULE_URL,
                observed_at_utc=_iso(now),
            ),
            Gate(
                "schedule_pdf_drift",
                "freshness",
                True,
                "no previous baseline on first run; baseline recorded for the next run",
                source_url=SCHEDULE_URL,
                observed_at_utc=_iso(now),
            ),
        ]
    baseline = baseline_path.read_text(encoding="utf-8").strip()
    return [
        Gate(
            "schedule_pdf_fetch",
            "fetch",
            True,
            f"schedule PDF fetched (sha256 {current_sha[:16]}…)",
            source_url=SCHEDULE_URL,
            observed_at_utc=_iso(now),
        ),
        Gate(
            "schedule_pdf_drift",
            "freshness",
            baseline == current_sha,
            (
                "schedule PDF matches the recorded baseline"
                if baseline == current_sha
                else f"schedule PDF CHANGED (baseline {baseline[:16]}… vs {current_sha[:16]}…); "
                "the published slate rows must be re-extracted before any rebuild"
            ),
            source_url=SCHEDULE_URL,
            observed_at_utc=_iso(now),
        ),
    ]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return doc if isinstance(doc, dict) else None


def _latest_snapshot(pattern: str) -> dict[str, Any] | None:
    """Newest matching snapshot by filename sort (file names carry their dates)."""
    for path in sorted(SNAPSHOTS.glob(pattern), reverse=True):
        doc = _load_json(path)
        if doc is not None:
            return doc
    return None


# --- orchestrator ------------------------------------------------------------

def run(
    mode: str,
    *,
    now: datetime | None = None,
    fetch: Callable[..., FetchResult] | None = None,
    baseline_path: Path | None = None,
    pdf_text: Callable[[bytes], str] | None = None,
) -> RunRecord:
    now = now or datetime.now(timezone.utc)
    fetch = fetch or default_fetch
    baseline_path = baseline_path or (RAW / "ci" / "schedule-sha-baseline.txt")
    record = RunRecord(mode=mode, now_utc=_iso(now))

    pointer = _latest_snapshot("injuries-newest-pointer-*.json")
    newest_report: str | None = None

    if mode != "offline":
        # ---- phase 1: fetch ----
        # Schedule PDF
        try:
            status, body, _ = fetch(SCHEDULE_URL)
            if status == 200 and is_pdf(body):
                record.fetches["schedule_pdf"] = {"status": status, "bytes": len(body), "sha256": sha256_hex(body)}
                record.gates.extend(gate_schedule_drift(now, baseline_path, sha256_hex(body)))
            else:
                record.fetches["schedule_pdf"] = {"status": status, "bytes": len(body)}
                record.gates.append(Gate("schedule_pdf_fetch", "fetch", False, f"status {status} or not a PDF", source_url=SCHEDULE_URL, observed_at_utc=_iso(now)))
        except Exception as exc:
            record.gates.append(Gate("schedule_pdf_fetch", "fetch", False, f"unreachable: {exc}", source_url=SCHEDULE_URL, observed_at_utc=_iso(now)))

        # Injury index -> newest listed report
        index_html: bytes | None = None
        try:
            status, body, _ = fetch(INJURY_INDEX_URL)
            index_html = body if status == 200 else None
            record.fetches["injury_index"] = {"status": status, "bytes": len(body)}
            record.gates.append(
                Gate(
                    "injury_index_fetch",
                    "fetch",
                    status == 200 and bool(REPORT_LINK_RE.search(body.decode("utf-8", "replace"))),
                    f"status {status}, report links found: {len(REPORT_LINK_RE.findall(body.decode('utf-8', 'replace')))}",
                    source_url=INJURY_INDEX_URL,
                    observed_at_utc=_iso(now),
                )
            )
        except Exception as exc:
            record.gates.append(Gate("injury_index_fetch", "fetch", False, f"unreachable: {exc}", source_url=INJURY_INDEX_URL, observed_at_utc=_iso(now)))

        newest = parse_newest_report_link(index_html) if index_html else None
        newest_url, newest_label = newest if newest else (None, None)
        newest_report = newest_label

        # Newest listed report PDF: fetchable + printed header matches its URL date.
        if newest_url:
            try:
                status, body, _ = fetch(newest_url)
                pdf_ok = status == 200 and is_pdf(body)
                record.fetches["injury_report_newest"] = {"status": status, "url": newest_url, "label": newest_label}
                record.gates.append(
                    Gate("injury_report_newest_fetch", "fetch", pdf_ok,
                         f"status {status}, pdf_magic={is_pdf(body)}, listed={newest_label}",
                         source_url=newest_url, observed_at_utc=_iso(now))
                )
                if pdf_ok:
                    text = pdf_text(body) if pdf_text else _pdf_text(body)
                    if text is None:
                        record.gates.append(
                            Gate("injury_report_header", "fetch", False,
                                 "no PDF text extractor available (pypdf/pdfminer.six); the printed "
                                 "header cannot be verified (fail closed)",
                                 source_url=newest_url, observed_at_utc=_iso(now))
                        )
                    else:
                        header_date = parse_report_header(text)
                        if header_date is None:
                            sample = re.sub(r"\s+", " ", text)[:120]
                            detail = (
                                f"no printed header found in {len(text)} extracted chars "
                                f"(sample: {sample!r}); URL date from {newest_label}"
                            )
                        else:
                            detail = f"printed header date {header_date!r} vs URL date from {newest_label}"
                        record.gates.append(
                            Gate("injury_report_header", "fetch", bool(header_matches_url(header_date, newest_url)),
                                 detail,
                                 source_url=newest_url, observed_at_utc=_iso(now))
                        )
            except Exception as exc:
                record.gates.append(Gate("injury_report_newest_fetch", "fetch", False, f"unreachable: {exc}", source_url=newest_url, observed_at_utc=_iso(now)))
        else:
            record.gates.append(Gate("injury_report_newest_fetch", "fetch", False, "no report link parsed from the index", source_url=INJURY_INDEX_URL, observed_at_utc=_iso(now)))

        # Standings (official stats API, falling back to the official page; task BV)
        gate, info = gate_official_feed("standings", "standings_fetch", fetch, now)
        record.fetches["standings"] = info
        record.gates.append(gate)

        # The three official team-stat pages (traditional=Base, advanced, opponent)
        for page in ("traditional", "advanced", "opponent"):
            gate, info = gate_official_feed(
                f"teamstats_{page}", f"teamstats_{page}_fetch", fetch, now
            )
            record.fetches[f"teamstats_{page}"] = info
            record.gates.append(gate)

        # ---- phase 2: freshness (uses fetched context) ----
        slate = _latest_snapshot("slate-*.json")
        record.gates.extend(gate_freshness(now, pointer=pointer, slate=slate, newest_report=newest_report))
    else:
        record.fetches["note"] = "offline mode: no network fetches attempted"

    # ---- phase 3: provenance ----
    record.gates.extend(gate_provenance(now))

    # ---- phase 4: build ----
    record.gates.extend(gate_build(now))

    return record


def _pdf_text(data: bytes) -> str | None:
    """Extract text for header verification; None means 'no extractor installed'.

    Tries pypdf first, then pdfminer.six when pypdf's output does not even
    mention the document title (font/layout differences between the two
    extractors are common on these reports). Every page is read: the printed
    header is not guaranteed to survive on page 1 alone.
    """
    text = ""
    try:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:30])
    except Exception:
        text = ""
    if "Injury" not in text:
        try:
            import io

            from pdfminer.high_level import extract_text as _extract

            alt = _extract(io.BytesIO(data))
            if len(alt) > len(text):
                text = alt
        except Exception:
            pass
    return text or None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=("gates", "probe", "offline"), default="gates")
    parser.add_argument("--json", type=Path, help="write the run record to this path")
    parser.add_argument("--now", help="override the current time (ISO-8601 UTC), for tests")
    args = parser.parse_args(argv)

    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else None
    if now is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    record = run(args.mode, now=now)
    payload = record.as_dict()
    if args.json:
        args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"scheduled_refresh mode={record.mode} now={record.now_utc}")
    for gate in record.gates:
        mark = "PASS" if gate.passed else "FAIL"
        print(f"  [{mark}] {gate.phase:<11} {gate.name}: {gate.detail}")
    summary = payload["summary"]
    print(
        f"summary: {summary['gates_passed']}/{summary['gates_total']} passed; "
        f"failed={summary['failed'] or 'none'}; "
        f"rebuild_allowed={summary['rebuild_allowed']}"
    )
    return record.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
