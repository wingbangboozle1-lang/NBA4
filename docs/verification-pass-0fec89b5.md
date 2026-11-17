# Verification pass 12 — tenth daily refresh, re-anchored game logs and final integration (tasks BM + BN, session `arena/0fec89b5-nba4`)

**Date:** 2026-11-17 (UTC) · **Branch:** `arena/0fec89b5-nba4` (branched from `96434de`) · **Board rows:** BM (refresh), BN (integration)

**Scope.**

1. **BM — the 2026-11-17 snapshot cycle.** Official sources re-read at measured times (§1), the
   slate / injury / standings / results / rest / aggregates snapshots regenerated for the
   10:30 AM ET cycle, every static banner and section heading on slate/injuries/results/availability
   re-dated, the per-player game-log block re-anchored to the current injury file of record
   (33 players, five official gamebooks), the test suite re-pointed (481 → 485), and the new
   untranscribed-revisions flag **BM-01** published on `review.html` with the freshness notice on
   `injuries.html`.
2. **BN — final integration.** Combined re-verification, PR to `main`, merge without waiting,
   Pages deploy confirmation, and the PR/merge/Pages record written back to `COORDINATION.md`
   (§5).

## 1. What was verified before publishing

| Check | Result | Evidence / source |
| --- | --- | --- |
| Injury-report index, first read | 2026-11-17 15:52 UTC (10:52 a.m. ET): 11/17 reports listed every 15 minutes 12:00 a.m. → 10:30 a.m. ET; the 10:30 a.m. file was newest | [NBA injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Injury-report index, final read | 2026-11-17 16:54 UTC (11:54 a.m. ET): later 11/17 revisions exist through 11:45 a.m. ET (10:45, 11:00, 11:15, 11:30, 11:45 a.m.) — all supersede the published snapshot; recorded in the freshness notice and flag BM-01 | [NBA injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Report pair transcribed | 10:15 AM and 10:30 AM ET PDFs fetched 15:52–15:53 UTC; 59 rows each; header "Injury Report: 11/17/26 10:15 AM" / "…10:30 AM"; cells cross-checked 59/59 (`.pipes` → `.cells.json` → file of record) | [10:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf) · [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Consecutive-revision diff | `engine/injurystore` mechanical diff 10:15 → 10:30: 59/59 rows matched, 0 status changes, 0 reason changes, 0 printing variances — published as a measured zero-change result, not an assumption | [diff snapshot](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/snapshots/injuries-2026-11-17-1015-to-1030.diff.json) |
| Untranscribed revisions (BM-01 evidence) | Three 11/16 revisions after the transcribed 10:00 AM file read directly: 10:15 AM, 7:45 PM, 11:45 PM PDFs each exist with their own headers and already differ in status cells (Edey Questionable→Available, Smith Questionable→Available between the 10:15 a.m. and 7:45 p.m. reads) | [11/16 10:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_15AM.pdf) · [11/16 7:45 PM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_07_45PM.pdf) · [11/16 11:45 PM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_11_45PM.pdf) |
| Schedule window | Schedule PDF rows 253–273 = 21 games (11/17 ×5, 11/18 ×12, 11/19 ×4); rows 253–259 print no "at", rows 260–273 print the "at" token | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Games-page corroboration | Game ids for all 21 window rows = `00226002`+(row−200) confirmed on the 11/17–11/19 games pages; 4 tip disagreements kept as printed (rows 256, 257, 266, 267) and flagged, never reconciled | [games 11/17](https://www.nba.com/games?date=2026-11-17) · [games 11/18](https://www.nba.com/games?date=2026-11-18) · [games 11/19](https://www.nba.com/games?date=2026-11-19) |
| Standings (home-court pin) | 2026-11-17 16:03 UTC: home **106–98 over 204** (rate 0.5196), road 98–106, neutral 1–1, league W = L = 205; pin = 0.59 pts; derived, not authored | [NBA standings](https://www.nba.com/standings) |
| Result feed | Eight 11/16 finals read 16:00–16:04 UTC from the official game pages: ORL@BOS, CHI@CLE, MEM@WAS, PHI@BKN, HOU@MIA, POR@MIN, GSW@NOP, PHX@DEN; 16/16 quarter-sum checks agree; no overtime period printed in any game | [scoreboard 11/16](https://www.nba.com/games?date=2026-11-16) and the eight game pages |
| Game ids for the log window | Official games page 11/15 read: `lal-vs-phx-0022600237`, `cha-vs-lac-0022600238`, `sas-vs-uta-0022600239`, `nyk-vs-tor-0022600241`; `det-vs-mia-0022600233` from `results-2026-11-14.json` (official game page recorded there) | [games 11/15](https://www.nba.com/games?date=2026-11-15) · [results-2026-11-14.json](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/snapshots/results-2026-11-14.json) |
| Per-player game logs | Chunk 0 of five official gamebooks read 16:40 UTC (DET@MIA 11/14; LAL@PHX, CHA@LAC, SAS@UTA, NYK@TOR 11/15): 33 report players covered exactly once — 5 printed box lines, 27 inactive-list entries, 1 DND row, 0 gaps (no report player's team played on 11/16); mirrored report cells re-verified 33/33 against the file of record | [DET@MIA](https://statsdmz.nba.com/pdfs/20261114/20261114_DETMIA_book.pdf) · [LAL@PHX](https://statsdmz.nba.com/pdfs/20261115/20261115_LALPHX_book.pdf) · [CHA@LAC](https://statsdmz.nba.com/pdfs/20261115/20261115_CHALAC_book.pdf) · [SAS@UTA](https://statsdmz.nba.com/pdfs/20261115/20261115_SASUTA_book.pdf) · [NYK@TOR](https://statsdmz.nba.com/pdfs/20261115/20261115_NYKTOR_book.pdf) |
| Page-break handling preserved | Kessler reason joined verbatim across the page 2/3 boundary and flagged; Reaves team cell stays `__lost__` in the injury snapshot with a flagged attribution note in the game log; the 6 page-4/date-less blocks stay `cells_source: "report-context"`; nothing back-filled | [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) · [injury snapshot](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/snapshots/injuries-2026-11-17-1030am.json) |
| Stale-identifier sweep | Grep over all 16 root pages: zero occurrences of `2026-11-16_10_00AM`, `10:00 AM ET report`, `results-2026-11-15`, `standings-2026-11-16`, `slate-2026-11-16`, `72 rows` outside `review.html`'s historical flags and `docs/` history | repository grep over the [published pages](https://github.com/wingbangboozle1-lang/NBA4/tree/main) |
| Builders in sync | `build_snapshots.py --check` → all blocks unchanged; `build_brief_data.py --check` → unchanged; `build_gamelogs.py --check` → unchanged | [scripts directory](https://github.com/wingbangboozle1-lang/NBA4/tree/main/scripts) |
| Baseline before any edit | `python3 -m unittest discover -s tests -t .` → **481 OK**; `check_site.py --with-tests` → PASS (16 pages, 661 HTML rows, 1172 Markdown rows at the previous cycle's state) | [tests directory](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| After edits (this branch) | `unittest` → **485 OK** (test_snapshots 38 → 42: re-pointed to the 11/17 files, golden-state replaced by page-break/lost-team/report-context tests, winners-follow-finals added, BI's game-log capture kept covered as a historical snapshot); `check_site.py --with-tests` → **PASS (16 pages, 610 HTML rows, 1189 Markdown rows)**; README/index state 485 | [checker](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |

## 2. Snapshots published this cycle

| File | Content | Official source |
| --- | --- | --- |
| `injuries-2026-11-17-1015am.json` / `…1030am.json` (+ `.pipes`, `.cells.json`) | 59 rows each; cross-check 59/59; page-break losses kept blank and flagged | [10:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf) · [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| `injuries-2026-11-17-1015-to-1030.diff.json` | measured 0/0/0 with 59/59 matched rows | [10:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf) · [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| `injuries-newest-pointer-2026-11-17.json` | freshness pointer for `scheduled_refresh.py` (`fetched_at_utc` 15:53Z) | [NBA injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| `slate-2026-11-17.json` | 21 games, rows 253–273; 17 code matches, 14 "at"-token rows, 4 tip disagreements kept as printed | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `standings-2026-11-17.json` | 30 rows; home 106–98/204 (0.5196) | [NBA standings](https://www.nba.com/standings) |
| `results-2026-11-16.json` | 8 finals, 16/16 quarter-sum checks, no OT column | [scoreboard 11/16](https://www.nba.com/games?date=2026-11-16) |
| `rest-window-2026-11-17.json` | 72 rows, 2026-11-10 → 2026-11-19 | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `aggregates-2026-11-17.json` | derived from the four inputs it names; pin 0.59 | [NBA standings](https://www.nba.com/standings) |
| `player-gamelogs-2026-11-14_to_2026-11-15-anchor-2026-11-17.json` | 33 players × 1 game; BI's earlier capture kept unchanged alongside | [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) · [DET@MIA gamebook](https://statsdmz.nba.com/pdfs/20261114/20261114_DETMIA_book.pdf) |

## 3. Irregularities recorded

| ID | Finding | Status | Source |
| --- | --- | --- | --- |
| BM-01 | The revisions between the transcribed cycles (11/16 10:15 a.m.–11:45 p.m. ET, 11/17 12:00–10:00 a.m. ET) are not transcribed, and five later 11/17 revisions (10:45–11:45 a.m. ET) supersede the published 10:30 a.m. snapshot. Three of the 11/16 files were read directly and already show real status changes between them. | Open — published on `review.html` and in the `injuries.html` freshness notice with revision + retrieval times; snapshot never relabelled; flagged items publish and do not block the merge | [index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| (extends AN-02 / P9-04) | Four tip clocks still disagree between the August schedule PDF and the report/games pages (UTA@LAC, CHA@LAL, BOS@DEN, GSW@DAL); the 10:30 report sides with the games pages on three and prints no time for GSW@DAL | Open — both values printed everywhere, none reconciled | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) · [games 11/17](https://www.nba.com/games?date=2026-11-17) · [games 11/18](https://www.nba.com/games?date=2026-11-18) |
| (recorded in the game-log file) | The gamebook designations print `Schröder`, `Nurkić`, `Niederhäuser` and "Right 2nd Plantar Plate Tear" where the report prints `Schroder`, `Nurkic`, `Niederhauser` and "Right Right Foot; 2nd Plantar Plate Tear"; each side keeps its own print, never merged | Recorded in `extraction_notes`; no cell reconciled | [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) · [SAS@UTA gamebook](https://statsdmz.nba.com/pdfs/20261115/20261115_SASUTA_book.pdf) |

## 4. Gates and rights stance (unchanged)

`engine.cli status` → `NO AUTHORIZED INPUTS`. No line, probability, pick, minute estimate or
production impact was written anywhere in this cycle (G0 / D-01 / IR-T4). Every published table
row carries its official source link or is blank and flagged; nothing inferred.

## 5. Integration record (BQ)

Filled in after the PR is opened, merged and Pages-confirmed — see `COORDINATION.md` rows BP/BQ
for the PR link, merge result and Pages build.

## 6. Merge reconciliation (2026-11-17, before the integration PR)

`origin/main` advanced during this session's work (PRs #75, #77, #78, #79 from
`arena/5cca4190-nba4`, `arena/af666c53-nba4` and `arena/3648982b-nba4`), so `origin/main` was
**merged into this branch** (not rebased — the content conflicts were per-file, and merging kept
every side's rows) and the following decisions were made, recorded in full in the collision
record in `COORDINATION.md`:

| Item | Decision |
| --- | --- |
| Shared snapshots (`slate-2026-11-17`, `standings-2026-11-17`, `rest-window-2026-11-17`, `results-2026-11-16`, `aggregates-2026-11-17`, the 10:15/10:30 injury pair, `.cells`/`.pipes`/diff, newest pointer) | **main's versions win** — they belong to the merged injury chain whose file of record is now the [11:15 AM ET revision](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_15AM.pdf) (task BX) |
| The 59-vs-60 row difference on the same 10:30 AM PDF | Recorded, not merged: this session joined the Kessler page-break reason fragments into one flagged row (59); main keeps the fragment as a separate lost row (60, phantom `Soreness` row flagged `__lost__`). Main's reading stands on the site; both readings are in the collision record. The 10:15→10:30 diff on main is therefore 60/60, 0/0/0 (this session's §1/§2 tables above describe its own 59-row branch state before the merge). Source: [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| `injuries-2026-11-17-1015am.json` (this session's file-of-record JSON) | Not carried: main's chain stores that revision as `.cells` + diff only, and a second JSON with a different row count would contradict it. Source: [10:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf) |
| `tests/test_snapshots.py`, `scripts/build_*.py`, `README.md`, `index.html`, `injuries.html`, `slate.html`, `results.html`, `availability.html` | **main's versions win** (547-test suite, 11:15 chain constants, 547 count lines, banner state). This session's test edits and banner rewrites are not carried. Source: [repository on main](https://github.com/wingbangboozle1-lang/NBA4/tree/main) |
| Carried from this session | `docs/verification-pass-0fec89b5.md` (this file), flag **BZ-01** in the new `pass12b-title` section of `review.html`, `player-gamelogs-2026-11-14_to_2026-11-15-anchor-2026-11-17.json` (adds the DET@MIA coverage main's 11/15-only window file lacks), the snapshot-registry rows in `data/snapshots/README.md`, `scripts/_gen_0fec89b5.py` and `scripts/_gen_gamelogs_0fec89b5.py`. Source: [review.html pass 12b](https://github.com/wingbangboozle1-lang/NBA4/blob/main/review.html) |
| Letters | BM/BN were claimed by `arena/5cca4190-nba4` five minutes earlier; this session's rows are re-lettered **BP/BQ** on the board (collision record answers request R-3). Source: [COORDINATION.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md) |

Post-merge verification on the merged tree (2026-11-17 17:18 UTC): `python3 -m unittest discover
-s tests -t .` → **547 OK**; `check_site.py --with-tests` → **PASS (16 pages, 652 HTML rows,
1304 Markdown rows)**; `build_snapshots.py --check`, `build_brief_data.py --check` and
`build_gamelogs.py --check` → all unchanged; `scheduled_refresh.py --mode offline` → **3/3 PASS**
(`rebuild_allowed=False` by design, provenance chain 53 files); `engine.cli status` →
`NO AUTHORIZED INPUTS`.
