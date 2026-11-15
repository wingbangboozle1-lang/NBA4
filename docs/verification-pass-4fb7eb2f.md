# Verification pass 8 — brief-gap closure: results layer, injury revisions, refusal-by-default engine

Session branch `arena/4fb7eb2f-nba4`, work dated **2026-11-15 UTC**. Board tasks **AP**
(engine gaps), **AQ** (eighth official-source pass), **AR** (surface split, partially),
**AS** (integration, PR, Pages) — these four were claimed on this branch at 11:35 UTC as
AN/AO/AP/AQ, and renumbered after merge because the parallel session's PR #47 and #49 took
AN and AO in between. The flag ids below keep the AN- prefix they were written with. Base commit `24d7adf85f85ee4c73f10ea3ddcf4a3379db6650` (`main`, the merge of PR #46). Merged
against `main` at `dfaf997` (PR #51) on this branch before opening PR #52, and §3a records
what that merge found.

This pass is deliberately narrow: it closes the *data-layer* gaps earlier passes
identified as blocking, adds the engine modules that consume them, and records every
place where the authorized inputs stop short of what the brief asks. No pick, line,
price or probability is published by anything described here.

## 1. What was read, and when

All fetches 2026-11-15 between **11:35 and 11:49 UTC**, HTTP 200, via the sandbox
web-fetch tool (the sandbox shell has no route to `nba.com`; see §7).

| Document | Read | What came out of it | Source of record |
| --- | --- | --- | --- |
| Injury-report index, 2026-27 season | 11:35 UTC | Policy text re-read; the 11/15 listing runs 12:00 AM → **6:15 AM ET**, so two revisions of the same morning exist to diff | [official.nba.com](https://official.nba.com/nba-injury-report-2026-27-season/) |
| `Injury-Report_2026-11-15_06_00AM.pdf` chunks 0–1 | 11:45 UTC | All 101 rows transcribed verbatim | [06:00 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_00AM.pdf) |
| `Injury-Report_2026-11-15_06_15AM.pdf` chunks 0–1 | 11:45 UTC | All 101 rows transcribed verbatim | [06:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| 2026–27 schedule PDF chunks 1–2 (rows 215–273) | 11:44 UTC | Rows 236–257 = the current 72-hour window; header still `AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE` | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Scoreboard 2026-11-14 and 2026-11-17 | 11:46 UTC | Game ids and slugs for the window; the 11/17 tip conflict (flag AN-02) | [scoreboard 11/17](https://www.nba.com/games?date=2026-11-17) |
| Five 11/14 game-summary pages (chunk 2 = `# LINESCORES`), plus `den-vs-nop-0022600231/box-score` chunks 2, 4–5 | 11:47 UTC | Q1–Q4 and the printed final for ten team lines; player lines and inactives for DEN@NOP; recaps used only as cross-checks | [game page DEN@NOP](https://www.nba.com/game/den-vs-nop-0022600231) |
| Standings, chunks 0–2 | 11:49 UTC | 30 rows verbatim (incl. HOME/ROAD/NEUTRAL/OT/LAST10/STREAK) and the printed tie-break procedures L.2.a / L.2.b | [nba.com/standings](https://www.nba.com/standings) |
| Team traditional / advanced / opponent stats pages | between 11:44 and 11:52 UTC (the minute is not recorded for these three; no snapshot file was written from them) | Traditional: all 30 rows. Advanced and opponent each return **2 chunks**; only chunk 0 was read (13 of 30 rows) → flag AN-04, no all-30 claim made | [team advanced](https://www.nba.com/stats/teams/advanced) |

## 2. Gap (1): a per-game result feed with quarter scores — **closed**

The finding that unblocked it: **quarter scores are not on the box-score page.** That
document carries player rows and team totals only; the linescore table is printed on the
*game-summary* page under the heading `LINESCORES`, which the extractor places in chunk
2. An earlier working note in this session called the quarter scores "unverified"
because the summary page had only been read at chunk 0.

Result: `data/snapshots/results-2026-11-14.json`, one row per team line, with the
settlement rule stated in the file itself:

```
game 0022600231  DEN 29/27/30/30 = 116  printed final 116  agrees
game 0022600231  NOP 23/28/31/26 = 108  printed final 108  agrees
… (five games, ten lines)
lines_where_quarter_sum_equals_printed_final: 10 of 10
```

Checks recorded in that file: quarter sums equal the printed final for **10 of 10** team
lines; each final matches the scoreboard page and the recap headline printed on the same
official page (5 of 5, 0 disagreements); away/home order comes from the page's own
`away-vs-home` slug and row order and agrees with the schedule PDF's printed order for
rows 231–235. No spread, total, price or pick appears in the file.

`engine/resultfeed.py` implements the gate: a day is `SETTLED` only when every team
line's four printed quarters add to the printed final; a line with a missing quarter is
`INCOMPLETE` and blocks settlement rather than being repaired. `load_results_snapshot`
reads the snapshot file, so the published table and the gate consume the same bytes.

**Feed delay stays unmeasured, on purpose.** The results document prints a tip time and
quarter scores but no clock at the final whistle, so "hours between game end and our
retrieval" has no numerator in the authorized set. `feed_delay_hours` returns `None`
(rendered `[NO INPUT]`) and the page prints the retrieval lag *after the printed tip*
instead: 9.78 h (last tip 2026-11-15 02:00 UTC → fetch 11:47 UTC).

## 3. Gap (2): injury-report store and consecutive-report diff — **closed**

Both revisions were extracted cell-for-cell into
`data/snapshots/raw/injury-2026-11-15T{0600,0615}am-et.pipes` (header block + seven
pipe-separated cells per row), then converted to snapshot JSONs by
`scripts/build_brief_data.py`. The machine diff, run through `engine/injurystore.py`:

| Measure | Value | Why it is stated this way | Source of record |
| --- | --- | --- | --- |
| rows, 06:00 / 06:15 | 101 / 101 | row count, not name equality, is the alignment signal | [06:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| status changes | **0** | a status change needs a matched row whose status cell differs | [06:00 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_00AM.pdf) |
| reason changes | **0** | same rule applied to the reason cell | [06:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| team-cell changes | **0** | team cells are dropped at page breaks, so a change here would mean a realignment | [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| name-cell (printing) variances | **1** — `Embiid, Joel` → `Embid, Joel` | same status, same reason, so it is an extraction artifact and not an availability change | [06:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| rows with a printed status | 85 | 62 `Out`, 17 `Questionable`, 2 `Probable`, 2 `Available`, 1 `Doubtful` | [repository file](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/snapshots/injuries-2026-11-15-0615am.json) |
| `NOT YET SUBMITTED` rows | 17 | a reporting state, never "no injuries" | [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| rows that lost matchup **and** team cells at a page break | 3 | published blank and flagged; never re-attributed | [repository file](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/snapshots/raw/injury-2026-11-15T0615am-et.pipes) |

The two revisions differ in **exactly one cell**, which a direct line-by-line comparison
of the two extractions confirms independently of the module.

## 3a. Cross-session cross-check of the same document — one published row was missing

`main` (PR #49) had published its own extraction of the **same** 06:15 AM document as
`data/snapshots/injuries-2026-11-15-0615am.json`, with 100 rows. This branch's independent
extraction of the same PDF has 101. The merge did not pick a winner by precedence: the
document was re-read, and the `IND@PHI` / Philadelphia 76ers block prints

```
row 9 : 11/15/2026 ; 01:00 (ET) ; IND@PHI ; Philadelphia 76ers ; Embid, Joel     ; Out ; Injury/Illness - Right Foot Plantar Fascia Injury Management
row 10: 11/15/2026 ; 01:00 (ET) ; IND@PHI ; Philadelphia 76ers ; Hukporti, Ariel ; Out ; Injury/Illness - Right Achilles Tendon Rupture / Tear
```
(cell separators shown as `;` so this document's own tables stay the only pipe tables on the page; the
extracted document prints one row per line with seven cells, and row 10 is the row that was missing.)

so `Hukporti, Ariel` was **omitted from the published table**, not absent from the report.
Resolution: the row was restored to main's file in document order (main's schema and keys
kept, so the published table and its tests move 100 → 101), this branch's own extraction was
moved to `injuries-2026-11-15-0615am.cells.json` so one file one schema stays true, and
`scripts/build_brief_data.py` now generates a `cross_check` block from the two files rather
than asserting agreement: **101 rows in each, 101 matching row for row, nothing one-sided on
either side** after the correction. Flag **AN-07**. The report is never
described as "unchanged" (the league says reports update continually), and the name
difference is never described as a status change.

Alignment rule, because it decides what counts as a change: rows are matched on the
identity cells each row prints (matchup, team, player) with positional proximity as the
tie-break; a one-for-one leftover whose status **and** reason are identical is a printing
variance. Unequal row counts push the entire diff into `ADDED_OR_REALIGNED` /
`REMOVED_OR_REALIGNED` rather than inventing a change.

## 4. Gap (3): standings, the home-court anchor, and the seal layer

`data/snapshots/standings-2026-11-15.json` holds all 30 rows as printed plus derived
per-row counts and three league-level checks, all of which pass:

* per row: `HOME + ROAD + NEUTRAL` games = `W + L` (30 of 30 rows);
* league: 187 home + 187 road + 2 neutral team lines = 376 team-game lines;
* league: 188 wins = 188 losses; `LAST10` covers `min(10, GP)` for all 30 rows.

Measured home-win rate **0.5294** (99–88 across 187 home games; the 2 neutral-site games
held out). `engine/homerate.py` converts it through the model's own normal approximation,
inverted: `points = MARGIN_SD_DEFAULT × Φ⁻¹(0.5294) = 12.0 × 0.0738 = +0.885`. It is a
*pin*, not a fitted parameter — `for_ratings()` raises unless the caller asserts both
`pre_registered=True` (from `engine/prereg.py`) and `rights_cleared=True` (from
`engine/contracts.require_allowed_use`, gate G0), and `engine/ratings.py` still ships
`HOME_ADVANTAGE_POINTS = 0.0`. `arena_adjustment()` returns `REFUSED`: no authorized
per-arena split exists, so no arena, altitude or travel coefficient is fitted.

`engine/seallayer.py` implements the tie-break chain printed on the same page (L.2.a for
two clubs, L.2.b for three or more): head-to-head → same-division winner → own division →
own conference → playoff-eligible own conference → playoff-eligible other conference →
point differential, applied **in order**, stopping at a criterion whose input is not
printed rather than skipping ahead. The only permitted skip is the inapplicable-division
step the rule itself prints, and it needs an explicit flag.

## 5. Gap (4): current slate, corroborated twice

`data/snapshots/slate-2026-11-15.json`: 22 games (9 on 11/15, 8 on 11/16, 5 on 11/17)
inside the 72-hour window from 11:35 UTC. Away/home order now has **two** independent
official readings for all 22 rows: the injury report's `AWAY@HOME` code (17 rows) and the
games-page slug `away-vs-home` (22 rows), whose game id equals `00226002` + the schedule
row number (22 of 22). This closes the open half of P7-02: the 11/16 games are no longer
order-unverified.

Tip time agrees between the two publications for 20 of 22 rows. The two exceptions are
kept as printed, both values, and flagged **AN-02**: the August schedule PDF prints
UTA–LAC at 11:00 PM ET and CHA–LAL at 10:00 PM ET; the games page prints 10:30 PM ET and
11:00 PM ET. Neither game is carried into a projection until a refreshed schedule
publication settles it. [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) ·
[Games page 11/17](https://www.nba.com/games?date=2026-11-17)

## 6. Engine additions

Eleven new modules plus functions on `engine/parlay.py`, one shared refusal type (`engine/inputs.py` → `MissingInput`, sentinel
`[NO INPUT]`), and a table of what each computes versus refuses in
[`docs/engine.md`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/engine.md).
Coverage: result feed, injury store, pre-registration freeze file, seal layer, dual
estimation with a disagreement headline, pinned home-court measure, per-team luck
against an exact-binomial band, travel/rest with a coverage requirement, minutes-share and
replacement-minutes behind a printed denominator, market prior behind G0, and parlay
push/void re-pricing with a `rho_from_feed` that refuses a correlation below 20 pairs.

Two standing rules were respected while adding them: the duplicate-module irregularity
(IR-T1) was **not** widened — `engine/parlay.py` gained functions instead of a second
module — and IR-T4 was **not** bypassed — no module manufactures a pick to make a table
look complete, and the new pages print `NO PICK` / `NONE`.
[Module table](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/engine.md) ·
[Terms of Use](https://www.nba.com/termsofuse)

## 7. Tests and checks run after these writes

| Check | Command | Result | Script under test |
| --- | --- | --- | --- |
| Engine unit tests | `python3 -m unittest discover -s tests -t .` | **OK** — `Ran 165 tests` (47 + 43 + 17 + 10 + 48; the count on the merged tree is 297, see §11; the added suite is `tests/test_engine_brief_gaps.py`, 48 tests, on top of the suites main gained in PRs #47 and #49) | [tests/](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| Site, table and link check | `python3 scripts/check_site.py --with-tests` | **PASS: 12 pages, 467 HTML data rows and 751 Markdown data rows passed.** | [check_site.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| Snapshot tables in sync | `python3 scripts/build_snapshots.py --check` | in sync; eight blocks across `slate.html`, `injuries.html`, `results.html`, all reporting `unchanged` | [build_snapshots.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/build_snapshots.py) |
| Derived files reproducible | `python3 scripts/build_brief_data.py --check` | `unchanged` for all four derived outputs, exit 0 | [build_brief_data.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/build_brief_data.py) |
| Row-count re-derivation | inline re-count of the `.pipes` files | 101 data rows per revision, every row exactly 7 cells; the document's own header line is metadata, not a row | [raw extractions](https://github.com/wingbangboozle1-lang/NBA4/tree/main/data/snapshots/raw) |

`check_site.py` grew two things on this pass: `results.html` in `PAGES` / `CANONICAL_NAV`
(the sidebar is now 12 links and the duplicate-navigation guard passes), and the
snapshot-provenance audit now covers the new files — which is what caught that
`results-2026-11-14.json` and `standings-2026-11-15.json` needed `source_url` and
`source_document_header` recorded honestly (a dated HTML page prints no clock, so the
file says so instead of inventing one).

## 8. Count audit

| Item | Count | Where the count comes from | Source of record |
| --- | --- | --- | --- |
| Site pages | 12 (was 11; `results.html` added) | `PAGES` in the site checker | [check_site.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| HTML data rows, all source-linked | 467 (526 before the two duplicate tables this branch had added were removed at merge; 347 before the pass) | printed in the checker's own PASS line | [results.html](https://github.com/wingbangboozle1-lang/NBA4/blob/main/results.html) |
| Markdown data rows in `docs/` | 730, including this file's own tables (675 before it) | same script, `docs/` scan | [docs/](https://github.com/wingbangboozle1-lang/NBA4/tree/main/docs) |
| Engine lines | 6,141 before this pass; `engine/` gained 11 modules | `wc -l engine/*.py tests/*.py scripts/*.py` | [engine/](https://github.com/wingbangboozle1-lang/NBA4/tree/main/engine) |
| Unit tests | 297 (165 on this branch alone; +132 from the parallel requirements suite in PR #53) | unittest discovery count, printed above | [tests/](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| Snapshot files | 9 JSON + 2 `.pipes` intermediates | directory listing | [data/snapshots/](https://github.com/wingbangboozle1-lang/NBA4/tree/main/data/snapshots) |

## 9. Requirements map for the items this pass touched

| Brief requirement | State after this pass | Where | Source of record |
| --- | --- | --- | --- |
| Result feed with quarter scores and settlement integrity | **met** for 11/14; the loader is generic over dated snapshots | `data/snapshots/results-2026-11-14.json`, `engine/resultfeed.py` | [game page](https://www.nba.com/game/den-vs-nop-0022600231) |
| Feed-delay measurement | **not met, with the reason published**: the authorized document prints no game-end clock | `results.html` aggregate table, `feed_delay_hours` | [scoreboard](https://www.nba.com/games?date=2026-11-14) |
| Injury store + consecutive-revision diff | **met**, two revisions diffed mechanically | `engine/injurystore.py`, `injuries.html` | [06:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| Pre-registration freeze | **met as a mechanism** (append-only file + gate); no production cycle registered yet | `engine/prereg.py` | [prereg.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/prereg.py) |
| Two independent estimators + disagreement headline | **mechanism met, data half-missing**: bands and per-variant counts compute; no licensed quote source exists, so every pair is `NO MARKET` | `engine/dualestimate.py`, `engine/marketprior.py` | [Terms of Use](https://www.nba.com/termsofuse) |
| Home-court from a measured home-win rate | **met as a measured pin** (0.5294 → +0.885 pts), not applied | `engine/homerate.py`, `standings-2026-11-15.json` | [standings](https://www.nba.com/standings) |
| Luck against a baseline | **met with a refusal path**: the record computes; the baseline is `[NO BASELINE]` without forecast history | `engine/luckscore.py` | [luckscore.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/luckscore.py) |
| Travel / rest load | **mechanism met**; 11/17 coverage is incomplete in the window and no authorized disruption notice exists, so counts refuse and the penalty stays 0.0 | `engine/travel.py` | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Minutes share / replacement minutes | **mechanism met**; no box-score minutes in the authorized input set, so it runs on synthetic rows only | `engine/minutesshare.py` | [minutesshare.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/minutesshare.py) |
| Seeding / tie-break layer | **met as an implementation of the printed procedure**; no end-of-season data exists to run it on | `engine/seallayer.py` | [standings](https://www.nba.com/standings) |
| Pick-hash tamper evidence | unchanged: still `contracts.snapshot_hash`, no new duplicate module added | `engine/contracts.py`, pass 6b §6 | [contracts.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/contracts.py) |

Every row's last cell links either the official publication the requirement is measured
against or the file in this repository that implements it, because
[`scripts/check_site.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py)
requires an official HTTPS link in the final cell of every published data row — this
document holds its own tables to the same rule.

## 10. Open items carried forward

| ID | Item | State | Source of record |
| --- | --- | --- | --- |
| AN-02 | Schedule vs games-page tip conflict for two 11/17 games | open; both values printed, neither game modelled | [games page 11/17](https://www.nba.com/games?date=2026-11-17) |
| AN-07 | Two sessions extracted the same 06:15 AM report; main's published table omitted the `Hukporti, Ariel` row the document prints | **corrected**: row restored in document order, both extractions now agree 101/101, `cross_check` generated into the `.cells.json` file | [06:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| AN-04 | Opponent and advanced team pages are 2-chunk documents; 17 of 30 rows unread | open; no league-wide defensive table published or consumed | [team advanced](https://www.nba.com/stats/teams/advanced) |
| IR-T4 | Rights gate G0 still blocks any bet surface | open; unchanged by this pass | [Terms of Use](https://www.nba.com/termsofuse) |
| IR-T1 | `validation.py`/`gates.py` and `correlation.py`/`corrstats.py` duplicates | open, owner decision; no third copy added | [engine/](https://github.com/wingbangboozle1-lang/NBA4/tree/main/engine) |
| AP remainder | `projections.html`, `team-stats.html`, `ledger.html` not created | standings/results material is on `results.html`; team-stats is blocked on AN-04 and the ledger page needs a real ledger | [board](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md) |

Reproduce: check out `arena/4fb7eb2f-nba4` and run the §7 commands. The sandbox shell has
no route to `nba.com`, so re-reading a document needs the fetch tool (or a networked
machine); that limitation is recorded rather than worked around.


## 11. Second merge of `main`: the same items, twice (12:24–12:27 UTC)

Before PR #52 could merge, `main` had advanced again to `cb820ae` (PR #53, session
`arena/7dfeb9eb-nba4`), whose task AS implemented the same enumerated requirement items this branch
had built as task AP, under different module names, plus `engine/publishedledger.py`,
`engine/totals.py`, `engine/surfaces.py` and `engine/ledger.py`. `git merge origin/main` reported
only two content conflicts — `README.md` and `index.html`, both the test-count sentence — because the
two sessions never wrote the same path. [PR #53](https://github.com/wingbangboozle1-lang/NBA4/pull/53)

| Item | This branch | `main` after PR #53 | Decision |
| --- | --- | --- | --- |
| Result feed / quarter sums | [`engine/resultfeed.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/resultfeed.py) | [`engine/officialresults.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/officialresults.py) | both kept; this branch also keeps the data the item needs |
| Injury revision diff | [`engine/injurystore.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injurystore.py) | [`engine/injurydiff.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injurydiff.py) | both kept; `InjuryRow` exists in both modules, which is legal because neither is re-exported at package level |
| Home-court pin | [`engine/homerate.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/homerate.py) | [`engine/ratings.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/ratings.py) `measured_home_win_rate` + `home_advantage_from_win_rate` | **de-duplicated**: this branch now calls main's conversion, and a test fails if the call is replaced by a local formula |
| Estimator disagreement | [`engine/dualestimate.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/dualestimate.py) | [`engine/estimators.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/estimators.py) + [`engine/confidence.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/confidence.py) | both kept; this one bands model-vs-market, that one model-vs-model |
| Luck, rest/travel, minutes, market prior, parlay rho | [`luckscore`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/luckscore.py), [`travel`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/travel.py), [`minutesshare`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/minutesshare.py), [`marketprior`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/marketprior.py), `parlay.rho_from_feed` | [`luck`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/luck.py), [`rest`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/rest.py) + [`venues`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/venues.py), [`rotations`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/rotations.py), [`markets`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/markets.py) | both kept; a later pass should pick one per item and retire the other with its tests |
| Pick-hash ledger, totals, surface separation | not built here | [`publishedledger`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/publishedledger.py), [`totals`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/totals.py), [`surfaces`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/surfaces.py) | main's work stands, unreviewed by this session and neither endorsed nor corrected |
| Playoff tie-break chain | [`engine/seallayer.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/seallayer.py) | — | unique to this branch |
| [`results.html`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/results.html) | built here | [board row AV](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md) still records it as undelivered by anyone | row AV annotated with the correction; the page and its renderer are on this branch |

**Verification on the merged tree.** `python3 -m unittest discover -s tests -t .` → **`Ran 297 tests ... OK`**
(47 + 43 + 17 + 10 + 132 + 48, six suites); `python3 scripts/check_site.py --with-tests` →
**PASS: 12 pages, 470 HTML data rows, 789 Markdown data rows**; `scripts/build_snapshots.py --check` and
`scripts/build_brief_data.py --check` both report every rendered table in sync. Two page-level defects
were found while merging and fixed here: a duplicated `id="pass8-title"` anchor (flag AN-08) and
`engine/__init__.py` describing only one of the two module sets.
