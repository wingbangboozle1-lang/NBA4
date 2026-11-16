# Verification pass 9 — session `arena/dab321e7-nba4` (16 Nov 2026)

Board tasks BG–BJ. This pass covers **task BG (the seventh daily refresh, cycle 2026-11-16)**: the
rolling slate, results, standings, team-stat and injury observations were re-read from the official
documents and re-published row by row, every value carrying the document and the retrieval time in
its last cell. Nothing below was inferred: every irregularity found in the documents is listed in
the last section and mirrored on the board ([`COORDINATION.md`](../COORDINATION.md)) rather than
corrected. Per the standing permission (pass-8 note AS), the task letters run to BJ in this session's
re-lettered claim so this refresh can be logged, not skipped.

## What was read, and how

| # | Observation read | How it was checked | What was found | Source |
| --- | --- | --- | --- | --- |
| 1 | NBA Official Injury Report, revision printed as `Injury Report: 11/16/26 09:15 AM` | The PDF text read in full; every row transcribed by hand into `data/snapshots/injuries-2026-11-16-0915am.json` (file of record) and into the raw pipe file `data/snapshots/raw/injury-2026-11-16T0915am-et.pipes` | 72 rows over 13 game blocks: 57 player rows for the eight 11/16 games and 15 `NOT YET SUBMITTED` team rows (five teams in tonight's games had not yet filed; all ten rows of the five 11/17 games are NYS). 7 rows lose the club cell at page breaks (`team: "__lost__"`, blank, flagged); the Golden State block prints one status-or-reason cell per row | [Injury Report 11/16 09:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| 2 | The consecutive revision printed as `Injury Report: 11/16/26 09:00 AM` | Transcribed separately (`injuries-2026-11-16-0900am.json`, `-0900am.cells.json`) and diffed cell for cell by `scripts/build_brief_data.py` | 72 rows on both sides, 72 of 72 aligned; **0 status changes, 0 reason changes, 0 name-cell variances**. The two documents' data rows are identical as extracted | [Injury Report 11/16 09:00 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_00AM.pdf) |
| 3 | The official injury index page | Re-read 2026-11-16 14:41 UTC | For 11/16 the index lists reports every 15 minutes from 12:00 a.m. through 9:15 a.m. ET (the newest listed at the check time); the URL pattern holds under `.../2026-11-17-season/`. Pointer recorded in `injuries-newest-pointer-2026-11-16.json` | [NBA injury report index](https://official.nba.com/nba-injury-report-2026-11-17-season/) |
| 4 | Nine official gamebooks for 2026-11-15 | Each PDF's SCORE BY PERIOD and player lines read; every quarter summed to the printed final | 18 of 18 team lines pass the printed-period check; 9 finals settled. NYK@TOR (`0022600241`) is an overtime game: the gamebook prints `OT1 17-13`, and the sum-check runs over quarters **plus the printed OT** | [Gamebooks 20261115](https://statsdmz.nba.com/pdfs/20261115/20261115_NYKTOR_book.pdf) (each row's source cell links its own book) |
| 5 | The DAL@BOS gamebook (`0022600240`) | The SCORE BY PERIOD away row extracts garbled in both PDF chunks; the official game page's LINESCORES prints the away quarters | The game page's printed lines are cited as `secondary_sources` for that one row (DAL 9-28-34-23=94). **No quarter was reconstructed**; if the second source were missing the row would have been left blank and flagged | [DAL vs BOS game page](https://www.nba.com/game/dal-vs-bos-0022600240) |
| 6 | The 2026–27 schedule PDF, window rows 245–269 | Re-read 2026-11-16 (chunk 2); each row transcribed with its printed cells and document row number | 25 games in the 72-hour window 2026-11-16 14:41:21Z → +72h. Rows 245–259 print no `at` token (two team cells side by side); rows 260–269 print an explicit `at` cell, so those ten rows' order is printed by the document | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 7 | Away-at-home order for rows 245–259 | Corroborated only where the 09:15 AM injury report prints the same `AWAY@HOME` code **for the same game date** | Rows 245–257 corroborated (13 games); rows 258–259 have no printed `at` and no report code — printed order, flagged unverified (P7-02 continues). POR@MIN appears twice (11/16 and 11/17); date-aware keys keep the pairings apart | [Injury Report 11/16 09:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| 8 | Tip-off times for the 13 report-linked games | Report `Game Time` (12-hour, no meridian) compared against the schedule's printed ET column | 11 agree once the meridian is read from the schedule. Two disagree (AN-02, kept from the 11/15 cycle): CHA@LAL report/games-page 11:00 PM vs PDF 10:00 PM; UTA@LAC report/games-page 10:30 PM vs PDF 11:00 PM. Both printed values are stored with dual citations, nothing reconciled | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 9 | Standings page, 2026-11-16 | All 30 rows read with HOME / ROAD / NEUTRAL / OT / LAST10 / STREAK splits; per-row split sums re-derived | 30 of 30 rows pass `HOME+ROAD+NEUTRAL = W+L`. League totals: 196 home, 196 road, 2 neutral team lines = 394 team-game lines; 197 wins = 197 losses; measured home win rate **0.5204 (102–94)** | [NBA standings](https://www.nba.com/standings) |
| 10 | Team stats pages — traditional, opponent, advanced | All 30 team rows read from each page; the model-input cut (GP, W-L, PTS/G, OffRtg, DefRtg, NetRtg, PACE, POSS, Opp PTS/G) extracted with per-row links | 30 rows per page, 3 teams (CHA/MIA/SAS) out of Cup contention so no Cup-group cells — those cells are blank, not zero. Full raw columns stay in the snapshot file only; the site publishes the model-input cut (rights stance D-01/IR-T4, owner review) | [Traditional](https://stats.nba.com/stats/teams/traditional/) · [Opponent](https://stats.nba.com/stats/teams/opponent/) · [Advanced](https://stats.nba.com/stats/teams/advanced/) |

## What was written

- **Data layer** (`1e86f0f`, 13 files): `results-2026-11-15.json` (9 rows incl. the printed-OT
  game), `standings-2026-11-16.json`, `teamstats-2026-11-16.json`, `slate-2026-11-16.json`
  (rows 245–269), the injury pair + pointer + diff, the two raw pipes files,
  `aggregates-2026-11-16.json`, and `scripts/build_brief_data.py` parameterised over the pipes pair
  (`--pair OLD NEW`) with an OT-aware `build_aggregates`.
- **Page layer** (`af6991d`): all `scripts/build_snapshots.py` renderers point at the 2026-11-16
  set; the results table gained a printed `OT` column and per-game gamebook links; the banners on
  `slate.html`, `injuries.html`, `results.html` and `index.html` carry the 11/16 revision time
  (09:15 AM ET), retrieval time (2026-11-16 14:41 UTC) and the new window; `tests/test_snapshots.py`
  follows the current snapshot (298 tests in six suites; README and index counts updated for the
  `check_site.py` guard).

## Verification run (all commands green)

- `python3 -m unittest discover -s tests -t .` → **298 OK**
- `python3 scripts/check_site.py --with-tests` → **PASS: 12 pages, 451 HTML data rows and 824 Markdown data rows**
- `python3 scripts/build_snapshots.py --check` → all blocks in sync
- `python3 scripts/build_brief_data.py --check` → cells/diff/aggregates reproducible; cross-check
  72/72 rows against the file of record; standings 197 = 197; result feed 18/18.

## Irregularities (flagged, not corrected)

1. **R2 – two reports per day.** For 11/16 the index lists ten revisions (12:00 a.m.–9:15 a.m. ET).
   The two newest are transcribed and diffed; the earlier eight are recorded as listed-but-not-
   transcribed, superseded. (Continues P8-07's rule.)
2. **Lost cells at page breaks.** 7 player rows in the 09:15 AM document lose the club cell
   (5 Memphis, 2 New Orleans). Left blank, flagged unverified; never filled from context.
   5 game blocks lose their date/time cells; those are repaired **only** from the official schedule
   PDF with both documents cited (the one repair this repo permits).
3. **Golden State block prints one status-or-reason cell per row.** Butler III has a reason and no
   status; Curry, Moody, Porzingis, Santos and Williams have a status and no reason. The missing
   cell is blank and flagged — not read across from another row or another document.
4. **Gamebook spelling variances.** `Embiid, Joel` (gamebook) vs `Embid, Joel` (report);
   `Schröder, Dennis` / `Niederhäuser, Usman` (gamebook spellings) vs `Schroder, Dennis` /
   `Niederhauser, Usman` (report spellings). Both sides stored as printed; no harmonisation.
5. **CHALAC gamebook lists `Hall (G League - Two-Way)`** among Charlotte's inactives; the CHA rows
   of the 09:15 AM report do not mention him. Both documents recorded as printed.
6. **NYK inactives Akins, Knecht and Nickel** print with no reason cell in the gamebook; the report
   prints no rows for them. Blank, not "no injury".
7. **AN-02 – dual printed tips (kept from the 11/15 cycle).** CHA@LAL 11:00 PM (report/games page)
   vs 10:00 PM (schedule PDF); UTA@LAC 10:30 PM (report/games page) vs 11:00 PM (schedule PDF).
   Both printed values stored with dual citations. The tip-disagreement fields in the report feeds
   are printed fields, not computed clocks (AN-02 refinement).
8. **Slate rows 258–259 print no `at`** and no injury-report code corroborates them: printed order,
   flagged unverified (P7-02 continues). Rows 260–269 carry no game ids in the slate snapshot: the
   row-number id convention held for rows 231–257 but is **not** extended by inference to rows with
   no injury-report code and no games-page fetch (those rows' id cells stay blank).
9. **Overtime rule in force.** NYK@TOR publishes its printed quarters plus the printed `OT1`
   period; the sum-check runs over all printed periods. Overtime is never reconstructed. DAL@BOS
   away quarters come from the game page's LINESCORES (garbled gamebook row), cited, not repaired.
10. **Rights stance unchanged (D-01/IR-T4/G0).** Team-stat pages feed a published model-input cut
    only; full raw columns stay in the snapshot file for owner review; 0 forecasts, 0 picks;
    `[NO INPUT]`, `RIGHTS_NOT_CLEARED`; ledger synthetic-only.
11. **Pipes-file defect (tooling, repaired).** 17 rows per raw pipes file carried a duplicated
    leading blank cell (8 cells) that would abort `parse_report`; both files repaired to exactly 7
    cells per row before any build ran, and the validation now runs before every build.

---

## Task BI — per-player game-log capture (`b50e8fc`)

For every one of the 57 players on the 2026-11-16 09:15 AM ET injury report, one dated,
attributed observation row per game in the window 2026-11-14 – 2026-11-15, captured verbatim
from the official gamebooks (chunk 0 of each prints both teams' full-game box score and the
inactive lists). Rows are evidence with row-level official links, **not betting inputs** (G0;
D-01/IR-T4 stand). Snapshot: [`data/snapshots/player-gamelogs-2026-11-14_to_2026-11-15.json`](../data/snapshots/player-gamelogs-2026-11-14_to_2026-11-15.json);
renderer/verifier: [`scripts/build_gamelogs.py`](../scripts/build_gamelogs.py) (refuses to
render if any mirrored report cell disagrees with the injury file of record; 57/57 verified).

| # | Capture | What was found | Source |
| --- | --- | --- | --- |
| 1 | 5 gamebooks of 2026-11-14 (CHI@MIN, DAL@CLE, BKN@MEM, DET@MIA, DEN@NOP) | 43 game rows: 8 played lines (MIN/PTS/REB/AST as printed strings), 29 inactive-list entries, 4 `DNP - Coach's Decision`, 2 `DND` designations. Every row cites its own gamebook URL | [Gamebooks 20261114](https://statsdmz.nba.com/pdfs/20261114/20261114_BKNMEM_book.pdf) (each row's source cell links its own book) |
| 2 | The 7 injury-report rows whose team cell was lost at a PDF page break (5 in the MEM@WAS block, 2 in GSW@NOP) | All 7 players appear in the 11/14 gamebooks under a printed team header (Grizzlies ×5, Pelicans ×2). The injury snapshot keeps their team cells blank and flagged; only the game-log rows carry the gamebook attribution, flagged per row | [BKN@MEM gamebook](https://statsdmz.nba.com/pdfs/20261114/20261114_BKNMEM_book.pdf) · [DEN@NOP gamebook](https://statsdmz.nba.com/pdfs/20261114/20261114_DENNOP_book.pdf) |
| 3 | Name spellings across the two document families | One variance: the DAL@CLE gamebook inactive list prints `Mobely` where the report prints `Mobley, Evan` (flag SP-01). Both kept as printed; no harmonisation | [DAL@CLE gamebook](https://statsdmz.nba.com/pdfs/20261114/20261114_DALCLE_book.pdf) |
| 4 | The 14 report players on ORL, GSW and POR | All three teams were idle on both window days; no game exists in the window and the previous games (2026-11-13) are outside this cycle's captures. Recorded as a window gap per player — not filled, not inferred | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 5 | Mirrored report cells (status/reason/team-lost) | A first draft of the snapshot carried 26 wrong mirrored values; the build-time mirror check against the injury file of record caught them and they were rebuilt from the file, now 57/57. The check is permanent in `build_gamelogs.py` and pinned by 6 new tests (304 total) | [Injury Report 11/16 09:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |

Irregularities added: **SP-01** (`Mobely`/`Mobley` spelling variance), window gap for ORL/GSW/POR
players (no game 11/14–15; 11/13 books not captured this cycle), and the note that only the
gamebook — never the report — attributes the 7 team-lost rows.

---

## Task BH — AV closure: the three engine-surface pages (`259250d`)

`model.html`, `availability.html` and `ledger.html` publish the implemented reference-engine spec
(`engine/*.py`, pinned by `tests/test_engine_requirements.py`, 132 cases) with every live model
value blank (`[NO INPUT]` / `[NO BASELINE]`) or clearly labelled as a measured observation with its
official link. No NBA-derived model value is invented; G0/D-01/IR-T4 stand. The sidebar of every
page now carries the canonical 15-item navigation enforced by `scripts/check_site.py` (PAGES and
CANONICAL_NAV updated in the same commit); README and `docs/site-spec.md` list the new pages.

| Page | What it renders | Live state published |
| --- | --- | --- |
| `model.html` | Two independent estimators (matchup PPP; point-differential means halved), the disagreement headline with the shared-input audit, the arithmetic blend (never called confidence), the home-court pin (measured 0.5204 (102–94) &rarr; 12.0 &times; &Phi;&sup1;(rate) &asymp; +0.614 pts, `HOME_ADVANTAGE_POINTS` left unset), the market-anchored prior weighted by measured OOS log loss, parlay &rho; beside the naive product (`BOUNDED_NOT_PRICED` without a measured &rho;), totals = possessions &times; PPP beside the naive scoring average, and the luck z-band publication gate | All model values blank; the one number shown is the measured home-win rate, cited to the official standings and the published aggregates |
| `availability.html` | The rotation-availability column (blank = "not sourced", never "healthy"), the top-8 minutes-share redistribution (240-minute budget, caller-supplied replacement weights, `unallocated_minutes` reported), and the injury &rarr; rotation &rarr; game-flow chain that stops at the first blank | Status row sourced (11/16 09:15 AM ET revision); availability, minutes and production rows blank |
| `ledger.html` | Pre-registration freeze rules (four sections, non-defaultable thresholds, `frozen_at` before the first bet, universe check), per-pick SHA-256 hashes, the append-only chain, the Merkle day seal before tip with inclusion proofs, and the settlement stamp from verified finals | NOT FROZEN / zero entries &mdash; the production ledger is empty because G0 is uncleared; the synthetic test fixtures are labelled and never stand in for a published pick |

Verification: `check_site.py --with-tests` PASS on the 15-page tree (542 HTML + 839 Markdown rows,
304 unit tests); every table row on the three pages carries an official HTTPS source cell.
