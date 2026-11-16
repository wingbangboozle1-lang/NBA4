# Line-by-line engine review — PR #53 modules (task BD, session arena/7ce5c0cc-nba4)

Date: 2026-11-16. Reviewer: this session, against `docs/verification-pass-7ce5c0cc.md`.
This record answers the PR #52 merge note **"Not silently fixed"**: the four PR #53
modules that no session reviewed line by line (`engine/publishedledger.py`,
`engine/totals.py`, `engine/surfaces.py`, `engine/leaderboard.py` and adjacent
code) are reviewed here against their own tests, their docstrings and the brief.
Every change made as a result of this review is listed below with its regression
test; every issue left alone is flagged, not swallowed.

Method: full read of each module (docstring, every function), cross-check of each
behavioural claim against the test file that covers it
(`tests/test_engine_requirements.py`), and targeted probes where reading alone
could not settle a question. The engine has **no NBA data**; nothing here touches
a published data value.

## 1. `engine/publishedledger.py` (432 lines) — tamper-evident ledger

Checked line by line: `canonical`/`sha256_hex`/`pick_hash` (sorted keys, `ledger_meta`
excluded), `_parse_iso` (tz required, normalised to UTC), the Merkle layer
(`merkle_root` odd-level duplicate pairing, `merkle_proof` mirroring it including
the self-paired last node, `verify_merkle_proof` left/right handling), `LedgerEntry`
(canonical body vs stored `entry_hash`), `_append` (prev-hash linkage, JSONL
append), `publish` (no rewrite of a pick id, https sources, pre-tip enforcement),
`seal_day` (empty-day refusal, earliest-tip enforcement, leaf order recorded),
`settle` (unpublished/unsettled guards, verified-finals requirement via
`engine.officialresults.verify_final`, post-tip settlement stamp), `verify_chain`,
`verify_against_seal` (leaf-order mismatch detection, inclusion proof),
`settlement_stamps`, `audit`.

Findings:

* **F-L1 (defect, FIXED here).** `publish()` did not refuse a pick for a game day
  that already had a `SEAL` entry. A pick could therefore be appended *after* the
  day's pre-tip seal and still `settle()` normally, because `settle()` only checked
  that the day was sealed at some point. The seal's `leaf_order` check would fail
  such a day's `verify_against_seal` (fail-loud), but settlement did not consult
  it. Fix: `publish()` now refuses any pick whose `game_date` is already sealed
  ("a sealed day's pick set is closed so the pre-tip seal cannot be diluted").
  Regression test: `ReviewFixRegressionTests.test_publish_after_the_days_seal_is_refused`.
* **F-L2 (defect, FIXED here).** `settle()` verified only that the day *was
  sealed*, not that *this pick* verifies against the seal. Fix: `settle()` now
  runs `verify_against_seal(pick_id)` and refuses unless it returns `verified`.
  Regression test:
  `ReviewFixRegressionTests.test_settle_refuses_a_pick_that_does_not_verify_against_the_seal`
  (tampered root ⇒ settlement refused).
* **F-L3 (flagged, not changed).** External anchoring: the ledger binds its own
  hashes but cannot bind them to a third-party timestamp; the module docstring
  already says so and marks it an owner decision. Left as an open question
  (see questions.html Q24).
* No other defect found. The Merkle odd-node handling, the chain recomputation and
  the ISO-tz rules match their tests (135-suite incl. the seal/settle tests).

## 2. `engine/totals.py` (267 lines) — possessions × PPP totals

Checked: `ppp_from_rating`, `adjusted_ppp` (both forms declared, none defaulted),
the two candidate pace rules (neither is a default), `model_total`,
`naive_total_from_averages` (kept as the published baseline), `project_total`
(INPUTS_MISSING rows carry no fabricated number), `possessions_from_components`
(both coefficients caller-supplied with an https citation), `compare_totals`
(NaN → blank).

Findings:

* **F-T1 (defect, FIXED here).** `TotalProjection.as_row()` rounded the NaN
  sentinels of an `INPUTS_MISSING` row, producing `NaN` tokens that `json.dumps`
  emits non-standardly. Fix: NaN serialises as `null` in `as_row`.
  Regression test:
  `ReviewFixRegressionTests.test_missing_total_inputs_serialise_as_null_not_nan`.
* The module otherwise matches its claims: no pace rule is silently defaulted, no
  possession coefficient is hard-coded, and the naive baseline stays first-class
  for side-by-side publication. No further defect found.

## 3. `engine/surfaces.py` (256 lines) — projection/bet surface split

Checked: the `FIELD_SURFACES` registry (every field declared on exactly one
surface; the brief's "never mix them" enforced at field level), `classify`
(undeclared field = build error), `project_view` (bet fields withheld loudly),
`bet_view` (gate-stubs only while `G0_RIGHTS_AND_VALIDATION` is closed),
`assert_not_mixed` (empty/stub values from the other surface allowed so the
absence stays legible), `audit_page_surface`, `surface_summary`.

Findings:

* **F-S1 (flagged, not changed — wiring is an owner/policy decision).**
  `audit_page_surface`'s docstring says "``scripts/check_site.py`` calls
  ``audit_page_surface`` with it", but `scripts/check_site.py` contains no call
  to it. The guard exists and is unit-tested, but it is **not wired into the site
  build check**, so the docstring currently overstates the enforcement. Wiring it
  requires choosing which blocked-field headers each page declares — a policy
  decision, not a silent fix. Flagged as P9-08 on review.html.
* **F-S2 (observation, no change).** `audit_page_surface` matches a blocked
  header anywhere in the page and then checks every numeric cell of every row, so
  it is a conservative page-level guard rather than a column-accurate one. When it
  is wired, false positives should be expected and whitelisted deliberately.
* No surface-registry error found: the brief's field list (lines, prices, edges,
  stakes, parlays, settlements, rewards as bet; observations, rest, injuries,
  disagreement, luck, home basis, ledger/gate state as projection) is faithfully
  declared, and the tests cover classify/projection/bet/mixed paths.

## 4. `engine/leaderboard.py` (193 lines) — gate-aware leaderboard

Checked: `GateOutcome`/`LeaderboardEntry`/`LeaderboardPolicy` (all policy values
caller-supplied; empty policy refused), `evaluate_gates` (an unreported gate is
recorded as failed "not reported", never silently passed; sample-size gate
appended), `_score` (weights from policy, unknown metric = error, zero weight sum
= error), `rank` (empty when nothing passes — intended behaviour).

Findings:

* **F-B1 (pre-existing flag IR-09, confirmed honest).** `policy.tie_breaker` is
  required but not applied; equal scores fall back to (strategy id, model
  version). The docstring says so explicitly and points at IR-09. Left as flagged
  until the owner approves a tie policy — not silently "fixed" into an invented
  policy.
* The `rank` sample-size condition is redundant with the `G-SAMPLE` gate (both
  fire), which is harmless defence in depth. No other defect found.

## 5. Adjacent code (reviewed at API level, listed for completeness)

* `engine/ratings.py` — `home_advantage_from_win_rate` delegation from this
  branch's `homerate.py` is intact (the anti-duplication test
  `test_engine_brief_gaps.py` still passes; 48/48).
* `engine/officialresults.py` — `verify_final`'s two-observation rule is what
  `publishedledger.settle` consumes; the refusal paths (single source,
  disagreeing officials) are tested (ResultFeedTests, 8 tests).
* `engine/__init__.py` — see the decision below.

## 6. Public-API decision for `engine/__init__.py` (AN-09 / IR-T1)

**Decision (documented 2026-11-16, reversible only by an explicit owner entry):**
the repository keeps **one flat public API** — `engine.<module>` for every module,
with `engine.__all__` listing both implementation sets — and does **not** split
into `engine/v1` / `engine/v2`, retire either side, or move names.

Rationale, each point checkable in the tree:

1. Both sets are tested and green (300 tests across six suites); a namespace
   split would break imports in 300 tests, `engine/cli.py`, `engine/selftest.py`
   and the docs for zero functional gain.
2. The two sets are the record of two sessions' readings of the brief (IR-T1 on
   review.html); deleting either would erase provenance the board exists to keep.
3. The one formula that was about to be duplicated (home-advantage points) is
   already resolved by delegation (`homerate` → `ratings.home_advantage_from_win_rate`)
   with a regression test that fails if the delegation is replaced.
4. A future owner decision to consolidate per item ("keep one module per pair and
   migrate its tests", IR-T1's own wording) is a mechanical, test-guided change
   that this decision does not foreclose: the mapping table in `docs/engine.md`
   is the worklist.

The `__init__.__all__` note pointing at IR-T1 stays; this review does not edit
the export list.

## Change summary

| Where | Change | Regression test | Source |
| --- | --- | --- | --- |
| `engine/publishedledger.py` `publish` | refuse a pick for an already-sealed game day (F-L1) | `test_publish_after_the_days_seal_is_refused` | [module](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/publishedledger.py) |
| `engine/publishedledger.py` `settle` | require `verify_against_seal` MATCHES_SEAL (F-L2) | `test_settle_refuses_a_pick_that_does_not_verify_against_the_seal` | [module](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/publishedledger.py) |
| `engine/totals.py` `as_row` | NaN → `null` (F-T1) | `test_missing_total_inputs_serialise_as_null_not_nan` | [module](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/totals.py) |
| `tests/test_engine_requirements.py` | `ReviewFixRegressionTests` (3 tests; suite 132 → 135) | — | [tests](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |

Flagged, not changed: F-L3 (external timestamp anchoring, owner question),
F-S1 (audit_page_surface not wired into check_site.py, P9-08), F-B1 (tie_breaker
unapplied, IR-09). No other finding. No engine behaviour outside the three fixed
defects changed by this review.
