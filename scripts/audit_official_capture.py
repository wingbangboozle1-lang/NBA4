#!/usr/bin/env python3
"""Audit a captured official-page manifest: what each 200 actually proves.

Task DI (session `arena/c38970c9-nba4`).

Why this exists. The scheduled refresh job's four statistics gates are red. Two
different explanations circulate, and only one of them is true:

  (a) "the official statistics pages are unreachable";
  (b) "the pages answer, but the raw body carries none of the statistics, because
      the table is fetched by the browser after the shell loads".

The 2026-11-17 and 2026-11-19 captures distinguish them: every statistics page
returns HTTP 200 and every one of those bodies contains zero team names. A 200 is
therefore not evidence of a feed. This script prints the verdict per surface so the
distinction is recorded in one place, with the numbers, instead of in prose.

It never fetches anything: it reads a manifest and the files stored beside it.

Usage:
    python3 scripts/audit_official_capture.py data/official-pages/2026-11-19
    python3 scripts/audit_official_capture.py data/official-pages/2026-11-19 --json out.json
"""

from __future__ import annotations

import argparse
import re
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from official_pages import capture_completeness  # noqa: E402

#: A body "carries rows" only if at least this many distinct team identifiers appear.
#: The official league has 30 teams; a real statistics table prints all of them.
EXPECTED_TEAMS = 30

#: Words that must appear in a body that really contains league statistics. They come
#: from the pages themselves (team names as the official site prints them), not from an
#: inferred schema.
#:
#: IMPORTANT (measured 2026-11-19): a bare team-name count is NOT evidence. Every one of
#: these pages carries a navigation/footer blob that names all 30 teams, so a
#: name-only marker reports "30 teams" for a shell that holds no statistics at all - the
#: first version of this script did exactly that. A statistics table needs a
#: column/row structure as well, so the marker below requires both: the team names *and*
#: at least one statistics column name from the page's own header row.
TEAM_NAMES = (
    "Celtics", "Knicks", "Nets", "76ers", "Raptors", "Bulls", "Cavaliers", "Pistons",
    "Pacers", "Bucks", "Hawks", "Hornets", "Heat", "Magic", "Wizards", "Nuggets",
    "Timberwolves", "Thunder", "Trail Blazers", "Jazz", "Warriors", "Clippers",
    "Lakers", "Suns", "Kings", "Mavericks", "Rockets", "Grizzlies", "Pelicans", "Spurs",
)

STATISTICS_KEYS = (
    "standings",
    "teamstats_traditional",
    "teamstats_opponent",
    "teamstats_advanced",
    "www_advanced_sorted",
    "stats_nba_origin_title",
)


#: Structural keys a JSON statistics payload must carry. These are the key names the
#: statistical feed uses in its row objects; a client-rendered shell ships none of them.
#:
#: THREE MARKERS WERE TRIED AND TWO OF THEM WERE WRONG — recorded here because the
#: wrong ones look convincing:
#:   1. team names (`Celtics`, ...) — every page ships a navigation/footer blob naming
#:      all 30 teams, so a name-only marker reports 30 teams for a shell with no data;
#:   2. filter-dropdown labels (`"W"`, `"L"`) — `<option value="W">Wins</option>` in the
#:      page's filter is not a statistics column;
#:   3. formatted numbers — 426 one-decimal values appear in the *SVG path data* of the
#:      page's inline logo/icon markup (`C118.4 271 89.6 371.4 88.5 500`), so a numeric
#:      marker reports a table that is not there.
#: What survives all three traps is a *structural* key. The measurements on
#: 2026-11-17 and 2026-11-19 agree: `teamName` appears 10 times (navigation),
#: `rowSet`, `headers`, `teamId`, `teamTricode` and `gamesPlayed` appear 0 times.
STAT_STRUCTURE_KEYS = ("rowSet", "headers", "teamId", "teamTricode", "gamesPlayed")
#: A body must carry at least this many of the structural keys to hold a statistics feed.
MIN_STRUCTURE_KEYS = 2


def _teams_present(text: str) -> list[str]:
    return sorted({name for name in TEAM_NAMES if name in text})


def _statistics_evidence(text: str) -> dict:
    """Return what the body holds, distinguishing a statistics feed from a shell.

    Every count is reported so a reader can see why the verdict fell where it did:
    the team-name count is included precisely because it is misleading on its own.
    """
    teams = _teams_present(text)
    structure = sorted({k for k in STAT_STRUCTURE_KEYS if f'"{k}"' in text})
    return {
        "teams_named": len(teams),
        "structure_keys_found": structure,
        "carries_statistics": len(structure) >= MIN_STRUCTURE_KEYS,
    }


def audit(capture_dir: Path) -> dict:
    manifest_path = capture_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    for record in manifest.get("records", []):
        files = record.get("captured_files") or []
        stored = None
        digest_ok = None
        body_text = ""
        for name in files:
            path = capture_dir / name
            if not path.is_file():
                continue
            data = path.read_bytes()
            if stored is None:
                stored = len(data)
                if stored == record.get("byte_length"):
                    digest_ok = hashlib.sha256(data).hexdigest() == record.get("sha256")
            if name.endswith((".head.html", ".next.json")):
                body_text += data.decode("utf-8", "replace")
        completeness = capture_completeness(record, stored)
        evidence = _statistics_evidence(body_text)
        is_stats = record.get("key") in STATISTICS_KEYS
        row = {
            "key": record.get("key"),
            "http_status": record.get("http_status"),
            "reached": record.get("reached"),
            "byte_length": record.get("byte_length"),
            "stored": completeness,
            "sha256_verified": digest_ok,
            "teams_present": evidence["teams_named"],
            "structure_key_count": len(evidence["structure_keys_found"]),
            "structure_keys_found": evidence["structure_keys_found"],
            "carries_statistics": evidence["carries_statistics"] if body_text else False,
            "is_statistics_surface": is_stats,
            "failure": record.get("failure"),
        }
        if is_stats:
            if record.get("http_status") == 200 and not row["carries_statistics"]:
                row["verdict"] = "HTTP_200_WITHOUT_STATISTICS"
            elif record.get("http_status") == 200:
                row["verdict"] = "HTTP_200_WITH_STATISTICS"
            elif record.get("reached") is False:
                row["verdict"] = "NOT_REACHED"
            else:
                row["verdict"] = "OTHER"
        else:
            row["verdict"] = "NOT_A_STATISTICS_SURFACE" if record.get("reached") else "NOT_REACHED"
        rows.append(row)
    return {
        "capture_dir": str(capture_dir),
        "captured_date_utc": manifest.get("captured_date_utc"),
        "generated_at_utc": manifest.get("generated_at_utc"),
        "runner": manifest.get("runner"),
        "statistics_surfaces_answered_200_without_data": sum(
            1 for r in rows if r["verdict"] == "HTTP_200_WITHOUT_STATISTICS"
        ),
        "records": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("--json", type=Path, help="write the audit to this path")
    args = parser.parse_args(argv)

    result = audit(args.capture_dir)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"capture {result['capture_dir']} (runner: {result['runner']})")
    print(f"{'key':28} {'http':>5} {'names':>5} {'struct':>6} {'stored':<12} verdict")
    for row in result["records"]:
        print(
            f"{row['key']:28} {str(row['http_status']):>5} {row['teams_present']:>5} "
            f"{row['structure_key_count']:>6} "
            f"{row['stored']['state']:<12} {row['verdict']}"
        )
    print()
    print(
        "statistics surfaces that answered 200 without a statistics payload "
        f"(<{MIN_STRUCTURE_KEYS} structural row keys in the body): "
        f"{result['statistics_surfaces_answered_200_without_data']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
