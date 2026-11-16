#!/usr/bin/env python3
"""One-shot COORDINATION.md bookkeeping update for tasks BB-BE (2026-11-16)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "COORDINATION.md"
t = p.read_text(encoding="utf-8")

# --- BB done ---
old = "| BB. Ninth daily refresh cycle (2026-11-16): official-source re-read of the rolling schedule window (11/16\u201311/18), newest injury-report index/PDF + consecutive-revision diff, standings re-check, and completion of the half-read advanced/opponent team-stat pages (closes AN-04) | **in progress** (claimed 2026-11-16T14:32Z, before work) |"
assert old in t, "BB status fragment not found"
new = ("| BB. Ninth daily refresh cycle (2026-11-16): official-source re-read of the rolling schedule window (11/16\u201311/18), "
       "newest injury-report index/PDF + consecutive-revision diff, standings re-check, and completion of the half-read "
       "advanced/opponent team-stat pages (closes AN-04) | **done** (claimed 2026-11-16T14:32Z, before work; evidence: "
       "`docs/verification-pass-7ce5c0cc.md`) |")
t = t.replace(old, new, 1)

old = ("half-read. Publish dated snapshots with row-level source links only; no model output, no inference. |")
new = ("pages that AN-04 left half-read. Publish dated snapshots with row-level source links only; no model output, no inference. "
       "**DONE 2026-11-16.** Fetched 14:31\u201315:0x UTC: injury index (newest listed 09:15 a.m. ET), both 11/16 PDFs "
       "(09:15 + 09:00 AM; 72 rows / 13 blocks each; diff = 0 status changes, 1 printing variance P9-01), schedule PDF "
       "rows 245\u2013269 (window 11/16\u201311/18), games-page cards for 11/15\u201311/18 (all card records match the standings "
       "transcription; tip conflicts P9-04 rows 266/267 and AN-02 rows 256/257 kept as dual readings), standings "
       "(30 rows; HOME+ROAD+NEUTRAL=GP 30/30; league W 197 = L 197), advanced + opponent team-stat pages read to the "
       "last row (30\u00d720 + 30\u00d726 cells, RANK dropped; GP/W/L vs standings 30/30 computed; Off\u2212Def=Net 30/30 computed; "
       "DefRtg vs Opp PTS compared as sets, not values \u2014 different denominators). Traditional page re-checked but NOT "
       "transcribed (extraction serves only filter controls; flag P9-06, no row count claimed). Snapshots written with "
       "full provenance: `slate-2026-11-16.json`, `standings-2026-11-16.json`, `results-2026-11-15.json` (9 finals, "
       "quarters blank + flagged P9-05), `team-stats-2026-11-16.json`, `injuries-2026-11-16-0900am/0915am.json` + diff + "
       "pointer + raw `.pipes`, `aggregates-2026-11-16.json` (home rate 0.5204 \u2192 +0.614 pts PROPOSED, NOT APPLIED). "
       "AN-04 **closed**. No pick, line, probability or settlement published. |")
assert old in t, "BB description tail not found"
t = t.replace(old, new, 1)

# --- BC done ---
old = "| BC. Site build-out: `team-stats.html` from the completed BB reads, `model.html` / `availability.html` / `ledger.html` as honest projection-vs-bet surfaces, nav + checker updates | **in progress** (claimed 2026-11-16T14:32Z, before work) |"
assert old in t, "BC status fragment not found"
new = ("| BC. Site build-out: `team-stats.html` from the completed BB reads, `model.html` / `availability.html` / `ledger.html` "
       "as honest projection-vs-bet surfaces, nav + checker updates | **done** (claimed 2026-11-16T14:32Z, before work) |")
t = t.replace(old, new, 1)

old = "the projection/bet split is expressed in navigation and per-page labels; no synthetic fixture is ever presented as live. |"
new = ("the projection/bet split is expressed in navigation and per-page labels; no synthetic fixture is ever presented as live. "
       "**DONE 2026-11-16.** Four pages built: `team-stats.html` (30 teams \u00d7 2 official pages, row-level source links, "
       "provenance table incl. the P9-06 gap, `model_inputs_status: REFUSED` notice), `model.html` (10-row component gate "
       "ledger: implemented / gated / refused, no forecast), `availability.html` (availability state + the minutes-"
       "redistribution rule recorded, not applied), `ledger.html` (chain procedure + honest empty state). Rotation "
       "availability added as its own column on the picks table (slate.html), counted from the 09:15 AM report rows. "
       "Canonical 16-page nav on every page; `check_site.py` page list extended + `audit_team_stats()` (30 unique teams "
       "per page, RANK columns dropped, GP/W/L cross-page agreement). Checks: 300 unit tests OK; `check_site.py` PASS "
       "(16 pages, 517 HTML data rows, 831 Markdown data rows). |")
assert old in t, "BC description tail not found"
t = t.replace(old, new, 1)

# --- BD done ---
old = "| BD. Line-by-line review of the PR #53 engine modules never reviewed (`publishedledger.py`, `totals.py`, `surfaces.py`, `leaderboard.py` + adjacent) and the `engine/__init__.py` public-API decision | **in progress** (claimed 2026-11-16T14:32Z, before work) |"
assert old in t, "BD status fragment not found"
new = ("| BD. Line-by-line review of the PR #53 engine modules never reviewed (`publishedledger.py`, `totals.py`, "
       "`surfaces.py`, `leaderboard.py` + adjacent) and the `engine/__init__.py` public-API decision | **done** "
       "(claimed 2026-11-16T14:32Z, before work; record: `docs/engine-modules-7ce5c0cc.md`) |")
t = t.replace(old, new, 1)

old = ("and decide/document whether the two parallel implementation sets stay as one public API or are namespaced. |")
new = ("and decide/document whether the two parallel implementation sets stay as one public API or are namespaced. "
       "**DONE 2026-11-16 \u2014 nothing silently fixed.** All four modules reviewed line by line against their tests and the "
       "brief: 3 defects fixed with 3 regression tests (F-L1 `publish()` now refuses a pick for an already-sealed game "
       "day; F-L2 `settle()` now requires `verify_against_seal` MATCHES_SEAL; F-T1 `as_row()` serialises missing inputs "
       "as null, never NaN), 3 items flagged not fixed (F-L3 external timestamp anchoring \u2192 Q24; F-S1 "
       "`surfaces.audit_page_surface` unit-tested but NOT wired into `check_site.py` although its docstring claims it \u2192 "
       "P9-08/S-24; F-B1 IR-09 tie_breaker declared-but-unapplied stays flagged). **Public-API decision (AN-09/IR-T1): "
       "keep one flat API** (`engine.<module>`; `__all__` lists both sets; no v1/v2 split; per-item consolidation stays "
       "open for an owner decision, mapping tables in `docs/engine.md` are the worklist) \u2014 rationale in "
       "`docs/engine-modules-7ce5c0cc.md` \u00a76. Suite now 300 tests (test_engine_requirements 132\u2192135). |")
assert old in t, "BD description tail not found"
t = t.replace(old, new, 1)

# --- session entry 12 update ---
old = ("and the final integration with the Pages confirmation queued since PR #54. Scope: `COORDINATION.md`")
assert old in t
new = ("and the final integration with the Pages confirmation queued since PR #54. **Status 2026-11-16: BB\u2013BD done** "
       "(snapshots + AN-04 closed; four pages built; engine review with 3 fixes + 3 flags; API decision recorded); "
       "BE completing with the integration PR. Flags for owner decision opened by this pass: P9-04 (tip authority), "
       "P9-05 (11/15 quarter-score gap blocks settlement), P9-06 (traditional page extraction), P9-08 (surface audit "
       "wiring). Scope: `COORDINATION.md`")
t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")
print("COORDINATION.md rows BB-BD + session entry updated")
