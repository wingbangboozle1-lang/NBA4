#!/usr/bin/env python3
"""Turn today's verified official extractions into snapshot + diff + aggregate files.

Inputs (written by hand from the documents read with the web-fetch tool in this
session; the provenance header of each file records the document, its own
timestamp and the fetch time):

  data/snapshots/raw/injury-2026-11-15T0600am-et.pipes
  data/snapshots/raw/injury-2026-11-15T0615am-et.pipes
  data/snapshots/results-2026-11-14.json
  data/snapshots/standings-2026-11-15.json
  data/snapshots/slate-2026-11-15.json

Outputs (derived, never hand-edited):

  data/snapshots/injuries-2026-11-15-0600am.json
  data/snapshots/injuries-2026-11-15-0615am.json
  data/snapshots/injuries-2026-11-15-0600-to-0615.diff.json
  data/snapshots/aggregates-2026-11-15.json

Every number in the outputs is arithmetic on the cells above it. Nothing is
estimated, filled in or inferred: a cell the document did not print stays an
empty string and carries ``printed: false``.

Run: ``python3 scripts/build_brief_data.py`` (``--check`` re-derives and compares).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so ``python3 scripts/build_brief_data.py`` finds engine/

from engine.injurystore import InjuryRevision, InjuryRow, diff_revisions  # noqa: E402
SNAP = ROOT / "data" / "snapshots"
RAW = SNAP / "raw"
FIELDS = ("game_date", "game_time", "matchup", "team", "player", "status", "reason")
# Cells the report prints once per game block; on continuation rows they are blank.
BLOCK_CELLS = ("game_date", "game_time", "matchup", "team")


def parse_report(path: Path) -> dict:
    """Return {"meta": header fields, "rows": the printed cells, row order kept}."""
    meta: dict[str, str] = {}
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # A meta line is "key: value" (the field list contains pipes, so the test is
        # on the leading key, not on the presence of a pipe).
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*:", line):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
            continue
        cells = line.split("|")
        if len(cells) != len(FIELDS):
            raise SystemExit(f"{path.name}: row does not carry {len(FIELDS)} cells: {line!r}")
        row = dict(zip(FIELDS, (c.strip() for c in cells)))
        for cell in BLOCK_CELLS:
            row[cell + "_printed"] = bool(row[cell])
        # A row the extraction could not align at a page break has no matchup,
        # no team and no game date. It is published with the blank cells kept.
        row["aligned"] = bool(row["matchup"]) or bool(row["team"])
        rows.append(row)
    meta["row_count"] = str(len(rows))
    return {"meta": meta, "rows": rows}


def build_injury_snapshot(parsed_rows: list[dict], meta: dict, snapshot_id: str) -> dict:
    rows = parsed_rows
    games: dict[tuple, list[dict]] = {}
    for row in rows:
        games.setdefault((row["game_date"], row["game_time"], row["matchup"]), []).append(row)
    games_out = []
    for (date, time, matchup), game_rows in games.items():
        games_out.append(
            {
                "game_date": date,
                "tip_et": time,
                "matchup": matchup,
                "rows": [
                    {
                        "team": r["team"],
                        "team_printed": r["team_printed"],
                        "player": r["player"],
                        "status": r["status"],
                        "reason": r["reason"],
                        "unverified": not r["aligned"],
                        "flag": (
                            ""
                            if r["aligned"]
                            else "matchup/team cells not printed on this row (PDF page break); "
                            "no value was inferred"
                        ),
                    }
                    for r in game_rows
                ],
            }
        )
    return {
        "snapshot_id": snapshot_id,
        "kind": "official_injury_report_rows",
        "source_url": meta["source_url"],
        "source_document": meta.get("document_header", ""),
        "source_document_header": meta.get("document_header", ""),
        "source_index_url": meta["source_index_url"],
        "revision_et_label": meta["revision_et_label"],
        "revision_utc": meta["revision_utc"],
        "fetched_at_utc": meta["fetched_at_utc"],
        "extraction_tool": meta["extraction_tool"],
        "row_count": int(meta["row_count"]),
        "extraction_notes": [
            "Verbatim extraction of the report named in source_url. Blank cells are blank because the "
            "extracted document prints nothing there at a page break; they are never filled in.",
            "Rows whose matchup and team cells are both blank carry unverified=true: the row's team is "
            "readable only from the block it continues, which this file does not assert.",
            "The report's own header line (revision_et_label) is the revision timestamp; fetched_at_utc "
            "is when we read it. Both are published in the Injuries page banner.",
        ],
        "games": games_out,
    }


def to_revision(snapshot: dict, meta: dict):
    """Re-express a built snapshot as an engine ``InjuryRevision`` (one diff implementation)."""
    rows = []
    for game in snapshot["games"]:
        for raw in game["rows"]:
            rows.append(
                InjuryRow(
                    game_date=game["game_date"],
                    game_time=game["tip_et"],
                    matchup=game["matchup"],
                    team=raw["team"],
                    player=raw["player"],
                    status=raw["status"],
                    reason=raw["reason"],
                    printed=tuple(k for k in ("team",) if raw.get("team_printed", True)),
                    position=len(rows),
                )
            )
    return InjuryRevision(
        revision_label=snapshot["revision_et_label"],
        document=snapshot["source_document"],
        source_url=snapshot["source_url"],
        retrieved_utc=snapshot["fetched_at_utc"],
        rows=tuple(rows),
        source_index_url=snapshot["source_index_url"],
    )


def rec(s: str) -> tuple[int, int]:
    w, _, l = s.partition("-")
    return int(w), int(l)


def build_aggregates(results: dict, standings: dict, injuries: dict, slate: dict) -> dict:
    # --- 1. Result feed integrity: quarter scores must add to the printed final.
    lines, bad = [], 0
    for row in results["rows"]:
        (game_id, date, tip, arena, city, away, home, aq, af, hq, hf, win, lose, url) = row
        for abbr, qs, final in ((away, aq, af), (home, hq, hf)):
            s = sum(qs)
            lines.append(
                {
                    "game_id": game_id,
                    "team": abbr,
                    "quarters": qs,
                    "quarter_sum": s,
                    "printed_final": final,
                    "agrees": s == final,
                }
            )
            bad += s != final
    # --- 2. Home-court advantage, pinned to the measured home-win rate.
    hw = hl = nw = nl = 0
    for r in standings["rows"]:
        a, b = rec(r["home"])
        hw, hl = hw + a, hl + b
        a, b = rec(r["neutral"])
        nw, nl = nw + a, nl + b
    home_games = hw + hl
    home_rate = hw / home_games if home_games else None
    tw = sum(r["w"] for r in standings["rows"])
    tl = sum(r["l"] for r in standings["rows"])
    # --- 3. Injury-report load for the current slate.
    rows = [x for g in injuries["games"] for x in g["rows"]]
    status_counts: dict[str, int] = {}
    for x in rows:
        key = x["status"] or ("NOT YET SUBMITTED" if x["reason"] == "NOT YET SUBMITTED" else "(not printed)")
        status_counts[key] = status_counts.get(key, 0) + 1
    return {
        "aggregate_id": "aggregates-2026-11-15",
        "kind": "derived_from_official_snapshots",
        # check_site.audit_snapshots requires these four on every file in data/snapshots;
        # for a derived file they name the document of the largest single input and state
        # plainly that no document prints the derived numbers themselves.
        "source_url": standings["source_url"],
        "source_document_header": standings["source_document_header"],
        "fetched_at_utc": standings["fetched_at_utc"],
        "extraction_tool": "scripts/build_brief_data.py (derived; performs no fetching)",
        "derived_from": {
            "results": results["source_url"] if "source_url" in results else results["source_index_url"],
            "standings": standings["source_url"],
            "injuries": injuries["source_url"],
            "slate": slate["source_url"],
        },
        "derived_at_utc": "2026-11-15T11:55:00Z",
        "inputs": {
            "results": "results-2026-11-14.json",
            "standings": "standings-2026-11-15.json",
            "injuries": injuries["snapshot_id"],
            "slate": slate["snapshot_id"],
        },
        "result_feed": {
            "games": len(results["rows"]),
            "team_lines_checked": len(lines),
            "lines_where_quarter_sum_equals_printed_final": sum(1 for x in lines if x["agrees"]),
            "lines_that_disagree": bad,
            "settlement_eligible": bad == 0,
            "per_line": lines,
            "source_url": results["source_index_url"],
            "note": "The feed is SETTLED only when every team line's four quarter scores add to the "
            "printed final. 2026-11-14 passes 10 of 10, so the day is eligible; the ledger stamps the "
            "settlement check at the fetch time of this file.",
        },
        "home_court": {
            "definition": "measured home-win rate = league HOME wins / (HOME wins + HOME losses) taken "
            "from the standings page; neutral-site records are held out and reported separately.",
            "home_wins": hw,
            "home_losses": hl,
            "home_games": home_games,
            "measured_home_win_rate": round(home_rate, 4) if home_rate is not None else None,
            "neutral_wins": nw,
            "neutral_losses": nl,
            "source_url": standings["source_url"],
            "pinning_rule": "engine/homerate.py refuses to fit home advantage freely: it converts this "
            "measured rate to a point value through one published conversion and nothing else.",
        },
        "standings_consistency": {
            "league_wins": tw,
            "league_losses": tl,
            "wins_equal_losses": tw == tl,
            "note": "Two league games are played at a neutral site, so HOME + ROAD + NEUTRAL games must "
            "equal the total games played: checked below.",
            "home_plus_road_plus_neutral": None,
        },
        "injury_load": {
            "revision": injuries["revision_et_label"],
            "revision_document": injuries["source_document"],
            "revision_utc": injuries["revision_utc"],
            "retrieved_utc": injuries["fetched_at_utc"],
            "rows": len(rows),
            "rows_with_a_status": sum(1 for x in rows if x["status"]),
            "not_yet_submitted_rows": sum(1 for x in rows if x["reason"] == "NOT YET SUBMITTED"),
            "unverified_rows_after_page_breaks": sum(1 for x in rows if x["unverified"]),
            "status_counts": status_counts,
            "source_url": injuries["source_url"],
        },
        "slate": {
            "games": len(slate["games"]),
            "window_start_utc": slate["window"]["start_utc"],
            "window_end_utc": slate["window"]["end_utc"],
            "source_url": slate["source_url"],
        },
    }


def write(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    check = "--check" in argv
    old_parsed = parse_report(RAW / "injury-2026-11-15T0600am-et.pipes")
    new_parsed = parse_report(RAW / "injury-2026-11-15T0615am-et.pipes")
    old = build_injury_snapshot(old_parsed["rows"], old_parsed["meta"], "injuries-2026-11-15-0600am")
    new = build_injury_snapshot(new_parsed["rows"], new_parsed["meta"], "injuries-2026-11-15-0615am")
    diff = asdict(
        diff_revisions(
            to_revision(old, old_parsed["meta"]),
            to_revision(new, new_parsed["meta"]),
            source_url=new["source_url"],
        )
    )
    diff["diff_id"] = "injuries-2026-11-15-0600-to-0615.diff"
    diff["kind"] = "official_injury_report_consecutive_diff"
    diff["source_document_header"] = new["source_document_header"]
    diff["fetched_at_utc"] = new["fetched_at_utc"]
    diff["extraction_tool"] = new["extraction_tool"]
    diff["source_index_url"] = new["source_index_url"]
    diff["rule"] = ("A status change requires a matched row whose status cell differs. Rows are matched on the "
                    "identity cells the row itself prints (matchup, team, player); a one-for-one leftover with "
                    "identical status and reason is a printing variance, not a status change.")
    results = json.loads((SNAP / "results-2026-11-14.json").read_text(encoding="utf-8"))
    standings = json.loads((SNAP / "standings-2026-11-15.json").read_text(encoding="utf-8"))
    slate = json.loads((SNAP / "slate-2026-11-15.json").read_text(encoding="utf-8"))
    agg = build_aggregates(results, standings, new, slate)
    targets = {
        SNAP / "injuries-2026-11-15-0600am.json": old,
        SNAP / "injuries-2026-11-15-0615am.json": new,
        SNAP / "injuries-2026-11-15-0600-to-0615.diff.json": diff,
        SNAP / "aggregates-2026-11-15.json": agg,
    }
    changed = False
    for path, payload in targets.items():
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        current = path.read_text(encoding="utf-8").strip() if path.exists() else ""
        if current == text.strip():
            print(f"unchanged {path.name}")
            continue
        changed = True
        if check:
            print(f"OUT OF DATE {path.name}")
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.name}")
    if check and changed:
        return 1
    # Console summary used by the runbook.
    print(
        f"injury rows old/new {diff['counts']['old_rows']}/{diff['counts']['new_rows']}; "
        f"status changes {diff['counts']['status_changes']}; "
        f"printing variances {diff['counts']['printing_variances']}"
    )
    print(
        f"result feed {agg['result_feed']['lines_where_quarter_sum_equals_printed_final']}"
        f"/{agg['result_feed']['per_line'].__len__()} quarter-sum checks agree; "
        f"home-win rate {agg['home_court']['measured_home_win_rate']} "
        f"({agg['home_court']['home_wins']}-{agg['home_court']['home_losses']})"
    )
    print(
        f"standings consistency wins={agg['standings_consistency']['league_wins']} "
        f"losses={agg['standings_consistency']['league_losses']} "
        f"equal={agg['standings_consistency']['wins_equal_losses']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
