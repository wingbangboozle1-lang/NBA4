#!/usr/bin/env python3
"""Task CA (session arena/edfbc063-nba4): derive the 2026-11-19 aggregates
snapshot from the 11/19 injury chain and the current observation files.

Reuses the arithmetic of ``scripts/build_brief_data.py`` (imported, never
modified) so every number is arithmetic on printed cells. Writes ONLY
``data/snapshots/aggregates-2026-11-19.json``; the historical
``aggregates-2026-11-17.json`` and the 11/17 cells/diff files are left untouched.

Inputs:
  - data/snapshots/raw/injury-2026-11-19T0130am-et.pipes  (consecutive pair)
  - data/snapshots/raw/injury-2026-11-19T0145am-et.pipes
  - data/snapshots/results-2026-11-16.json   (current results observation)
  - data/snapshots/standings-2026-11-17.json (current standings observation)
  - data/snapshots/slate-2026-11-17.json     (current 3-day window)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("build_brief_data", ROOT / "scripts" / "build_brief_data.py")
bbd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bbd)

SNAP = ROOT / "data" / "snapshots"
RAW = SNAP / "raw"

OLD_PIPES = "injury-2026-11-19T0130am-et.pipes"
NEW_PIPES = "injury-2026-11-19T0145am-et.pipes"
OLD_ID = "injuries-2026-11-19-0130am"
NEW_ID = "injuries-2026-11-19-0145am"


def main() -> int:
    old_parsed = bbd.parse_report(RAW / OLD_PIPES)
    new_parsed = bbd.parse_report(RAW / NEW_PIPES)
    old = bbd.build_injury_snapshot(old_parsed["rows"], old_parsed["meta"], OLD_ID)
    new = bbd.build_injury_snapshot(new_parsed["rows"], new_parsed["meta"], NEW_ID)

    results = json.loads((SNAP / "results-2026-11-16.json").read_text(encoding="utf-8"))
    standings = json.loads((SNAP / "standings-2026-11-17.json").read_text(encoding="utf-8"))
    slate = json.loads((SNAP / "slate-2026-11-17.json").read_text(encoding="utf-8"))

    agg = bbd.build_aggregates(
        results,
        standings,
        new,
        slate,
        agg_id="aggregates-2026-11-19",
        derived_at="2026-11-19T07:15:00Z",
        input_names={
            "results": "results-2026-11-16.json",
            "standings": "standings-2026-11-17.json",
            "injuries": new["snapshot_id"],
            "slate": slate["snapshot_id"],
        },
    )
    path = SNAP / "aggregates-2026-11-19.json"
    path.write_text(json.dumps(agg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.name}")
    print(f"injury_load: revision={agg['injury_load']['revision']} rows={agg['injury_load']['rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
