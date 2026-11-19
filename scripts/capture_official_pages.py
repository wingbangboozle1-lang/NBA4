#!/usr/bin/env python3
"""Task BU: capture what an unrestricted host actually retrieves from the official pages.

Run inside the `capture-official-pages` workflow. Earlier observations of these
URLs came from a sandbox whose egress is restricted to GitHub, npm and PyPI
(recorded as BH-05 and P11-03), so the `daily-refresh` job's red fetch gates
could not be attributed to a cause. This module is the missing observation: it
records, for every URL the scheduled job depends on, the HTTP status, the
content type, the byte length, the sha256 and whether the body parses as the
declared shape.

Nothing here interprets the data. A URL that is not reached is recorded as
NOT REACHED with the failure text; it is never recorded as an empty feed, and no
row, team or statistic is extracted here.

Usage:
    python3 scripts/capture_official_pages.py          # from the workflow env
    CAPTURE_DATE=2026-11-17 CAPTURE_TARGETS=standings python3 scripts/capture_official_pages.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "data" / "official-pages"

HEAD_BYTES = 300_000
NEXT_JSON_BYTES = 2_000_000
TIMEOUT = 25

# The User-Agent and Referer below are the ones `scripts/scheduled_refresh.py`
# already sends, so this probe measures the same request the job makes.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com/",
}

TARGETS: dict[str, dict[str, str]] = {
    "standings": {
        "url": "https://www.nba.com/standings",
        "kind": "html",
        "note": "official standings page; the job's standings feed",
    },
    "teamstats_traditional": {
        "url": "https://www.nba.com/stats/teams/traditional",
        "kind": "html",
        "note": "official traditional team-stat page",
    },
    "teamstats_opponent": {
        "url": "https://www.nba.com/stats/teams/opponent",
        "kind": "html",
        "note": "official opponent team-stat page",
    },
    "teamstats_advanced": {
        "url": "https://www.nba.com/stats/teams/advanced",
        "kind": "html",
        "note": "official advanced team-stat page",
    },
    "injury_index": {
        "url": "https://official.nba.com/nba-injury-report-2026-27-season/",
        "kind": "html",
        "note": "official injury-report index",
    },
    "stats_api_standings": {
        "url": (
            "https://stats.nba.com/stats/leaguestandingsv3"
            "?GroupBy=conf&LeagueID=00&Season=2026-27&SeasonType=Regular+Season&Section=overall"
        ),
        "kind": "json",
        "note": "the stats.nba.com JSON endpoint the job currently targets for standings",
    },
    "stats_api_teamstats": {
        "url": (
            "https://stats.nba.com/stats/leaguedashteamstats"
            "?Conference=&DateFrom=&DateTo=&Division=&GameScope=&GameSegment=&LastNGames=0"
            "&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome="
            "&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience="
            "&PlayerPosition=&PlusMinus=N&Rank=N&Season=2026-27&SeasonSegment="
            "&SeasonType=Regular+Season&ShotClockRange=&StarterBench=&TeamID=0&TwoWay=0"
            "&VsConference=&VsDivision="
        ),
        "kind": "json",
        "note": "the stats.nba.com JSON endpoint the job currently targets for team stats",
    },
    "schedule_pdf": {
        "url": "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf",
        "kind": "pdf",
        "note": "official 2026-27 regular-season schedule PDF",
    },
    # ---- batch 2: candidate data endpoints -------------------------------
    # Batch 1 showed the four official HTML pages return 200 but carry no
    # statistics in their raw bodies (client-rendered). These candidates are
    # probed so the transport question is settled with evidence rather than a
    # guess: each is recorded as REACHED or NOT REACHED, and a 404 is reported
    # as a 404, never as an empty feed.
    "cdn_live_scoreboard": {
        "url": "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
        "kind": "json",
        "note": "cdn.nba.com live scoreboard JSON (candidate results transport)",
    },
    "cdn_static_schedule": {
        "url": "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
        "kind": "json",
        "note": "cdn.nba.com static full-season schedule JSON (candidate schedule transport)",
    },
    "data_nba_today": {
        "url": "https://data.nba.net/prod/v1/today.json",
        "kind": "json",
        "note": "data.nba.net today index (candidate, historically public)",
    },
    "stats_api_scoreboard": {
        "url": (
            "https://stats.nba.com/stats/scoreboardv3"
            "?GameDate=2026-11-16&LeagueID=00"
        ),
        "kind": "json",
        "note": "stats.nba.com scoreboard endpoint, same host as the two feeds that timed out",
    },
    "nba_api_standings": {
        "url": "https://www.nba.com/api/v1/standings",
        "kind": "json",
        "note": "www.nba.com JSON API guess, probed to be recorded as 404 rather than assumed",
    },
    # ---- batch 3: is the 403 on cdn.nba.com path-driven or header-driven? --
    # Batch 2 returned 403 for the two cdn.nba.com JSON paths while the schedule
    # PDF on the same host returned 200. A 403 is a refusal, not a missing file,
    # so the same URL is retried with different headers to separate "this path is
    # blocked" from "this request is blocked". Each variant keeps its own record.
    "cdn_live_scoreboard_minimal": {
        "url": "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
        "kind": "json",
        "note": "same URL as cdn_live_scoreboard, browser-plain headers only",
        "headers": {
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "*/*",
        },
        "drop_default_headers": True,
    },
    "cdn_live_scoreboard_no_ua": {
        "url": "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
        "kind": "json",
        "note": "same URL, urllib default headers (no User-Agent, no Referer)",
        "headers": {},
        "drop_default_headers": True,
    },
    "cdn_schedule_pdf_minimal": {
        "url": "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf",
        "kind": "pdf",
        "note": "control: the same PDF that returned 200, requested with minimal headers",
        "headers": {
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "*/*",
        },
        "drop_default_headers": True,
    },

    # ---- batch 4: client-rendered page data endpoints (task DI, 2026-11-19) ---
    # Batches 1-3 established that the four www.nba.com pages return a shell and that
    # cdn.nba.com/static/json/** is refused with HTTP 403 whatever the headers are.
    # What was never probed is the JSON a browser requests after that shell loads.
    # These are candidates, not sources: nothing is parsed from them, and a failure
    # is recorded as NOT REACHED.
    "stats_nba_origin_title": {
        "url": "https://stats.nba.com/",
        "kind": "html",
        "note": "stats.nba.com origin document: does the host answer at all, and with what status?",
    },
    "cdn_boxscore_live": {
        "url": "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_0022600253.json",
        "kind": "json",
        "note": "cdn.nba.com per-game boxscore JSON for one real 11/17 game id (0022600253 = NYK@TOR)",
    },
    "cdn_playbyplay_live": {
        "url": "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_0022600253.json",
        "kind": "json",
        "note": "cdn.nba.com play-by-play JSON for the same game (game-flow input candidate)",
    },
    "cdn_schedule_leaguedate": {
        "url": "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",
        "kind": "json",
        "note": "older cdn static schedule path (batch 2 probed scheduleLeagueV2_1.json)",
    },
    "www_advanced_sorted": {
        "url": "https://www.nba.com/stats/teams/advanced?dir=-1&sort=PTS",
        "kind": "html",
        "note": "the advanced page with its own query string: does the shell ever server-render rows?",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_next_json(raw: bytes) -> tuple[bool, str | None]:
    """Return (found, json_text) for a Next.js __NEXT_DATA__ payload.

    The parser is deliberately structural and reports only whether the marker is
    present and whether the extracted text parses as JSON. It does not reach into
    the payload for values: that is the job of the parsers in
    ``scripts/official_pages.py``, which run against the captured file.
    """
    marker = b'id="__NEXT_DATA__"'
    start = raw.find(marker)
    if start < 0:
        return False, None
    open_brace = raw.find(b"{", start)
    if open_brace < 0:
        return False, None
    depth = 0
    in_string = False
    escaped = False
    for index in range(open_brace, min(len(raw), open_brace + NEXT_JSON_BYTES)):
        byte = raw[index : index + 1]
        if in_string:
            if escaped:
                escaped = False
            elif byte == b"\\":
                escaped = True
            elif byte == b'"':
                in_string = False
            continue
        if byte == b'"':
            in_string = True
        elif byte == b"{":
            depth += 1
        elif byte == b"}":
            depth -= 1
            if depth == 0:
                candidate = raw[open_brace : index + 1]
                try:
                    return True, json.dumps(json.loads(candidate.decode("utf-8")), indent=1)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return True, None
    return True, None


def _headers_for(spec: dict) -> dict[str, str]:
    """The headers this target is probed with.

    A target may declare ``drop_default_headers`` to start from an empty set so
    the probe can tell a path-level refusal (403 with every header set) from a
    request-level one (403 only with our usual browser-imitating headers).
    """
    if spec.get("drop_default_headers"):
        return dict(spec.get("headers") or {})
    headers = dict(HEADERS)
    headers.update(spec.get("headers") or {})
    return headers


def capture_one(key: str, spec: dict, out_dir: Path) -> dict:
    url = spec["url"]
    record: dict = {
        "key": key,
        "url": url,
        "kind": spec["kind"],
        "note": spec["note"],
        "retrieved_at_utc": None,
        "reached": False,
        "http_status": None,
        "content_type": None,
        "byte_length": None,
        "sha256": None,
        "captured_files": [],
        "shape_check": None,
        "failure": None,
        "headers_sent": _headers_for(spec),
    }
    request = urllib.request.Request(url, headers=record["headers_sent"])
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read()
            record["http_status"] = int(response.status)
            record["content_type"] = response.headers.get("Content-Type")
    except urllib.error.HTTPError as exc:  # a real HTTP error response
        record["http_status"] = int(exc.code)
        record["content_type"] = exc.headers.get("Content-Type") if exc.headers else None
        record["retrieved_at_utc"] = _now_iso()
        record["failure"] = f"HTTPError {exc.code} {exc.reason}"
        return record
    except Exception as exc:  # noqa: BLE001 - the failure text is the evidence
        record["retrieved_at_utc"] = _now_iso()
        record["failure"] = f"{type(exc).__name__}: {exc}"
        return record

    record["retrieved_at_utc"] = _now_iso()
    record["reached"] = True
    record["byte_length"] = len(raw)
    record["sha256"] = hashlib.sha256(raw).hexdigest()
    prefix = spec["url"].split("//", 1)[-1].split("/", 1)[0]
    record["host"] = prefix

    if spec["kind"] == "html":
        head_path = out_dir / f"{key}.head.html"
        head_path.write_bytes(raw[:HEAD_BYTES])
        record["captured_files"].append(head_path.name)
        found, payload = _extract_next_json(raw)
        record["shape_check"] = {
            "has_next_data_marker": found,
            "next_data_parses_as_json": payload is not None,
        }
        if payload is not None:
            next_path = out_dir / f"{key}.next.json"
            next_path.write_text(payload, encoding="utf-8")
            record["captured_files"].append(next_path.name)
    elif spec["kind"] == "json":
        body_path = out_dir / f"{key}.body.json"
        body_path.write_bytes(raw)
        record["captured_files"].append(body_path.name)
        try:
            parsed = json.loads(raw.decode("utf-8"))
            record["shape_check"] = {
                "parses_as_json": True,
                "top_level_keys": sorted(parsed)[:10] if isinstance(parsed, dict) else None,
            }
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            record["shape_check"] = {"parses_as_json": False, "error": str(exc)}
    elif spec["kind"] == "pdf":
        pdf_path = out_dir / f"{key}.pdf"
        pdf_path.write_bytes(raw)
        record["captured_files"].append(pdf_path.name)
        record["shape_check"] = {
            "starts_with_pdf_magic": raw[:5] == b"%PDF-",
            "page_marker_count": raw.count(b"/Type /Page"),
        }
    return record


def main() -> int:
    date_label = os.environ.get("CAPTURE_DATE") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    wanted = os.environ.get("CAPTURE_TARGETS") or "all"
    keys = list(TARGETS) if wanted.strip() == "all" else [k.strip() for k in wanted.split(",")]
    unknown = [k for k in keys if k not in TARGETS]
    if unknown:
        print(f"unknown target(s): {unknown}", file=sys.stderr)
        return 2

    out_dir = OUT_ROOT / date_label
    out_dir.mkdir(parents=True, exist_ok=True)
    records = [capture_one(key, TARGETS[key], out_dir) for key in keys]

    manifest = {
        "captured_date_utc": date_label,
        "generated_at_utc": _now_iso(),
        "generator": "scripts/capture_official_pages.py",
        "runner": "GitHub-hosted ubuntu-latest (unrestricted egress)",
        "headers_sent": HEADERS,
        "records": records,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for record in records:
        state = "REACHED" if record["reached"] else "NOT REACHED"
        detail = record["failure"] or f"{record['http_status']} {record['byte_length']} bytes"
        print(f"{state:12} {record['key']:24} {detail}")
    print(f"\nmanifest: {out_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
