# Verification pass 10 — seventh daily refresh, three new pages, integration (tasks AV, BC, BD)

**Session:** `arena/5a45618f-nba4` · **Date:** 2026-11-16 (UTC) · **Scope:** the snapshot refresh (BD), the three missing site pages plus navigation (AV), and the integration run that re-verifies and publishes (BC).
**Changed:** `data/snapshots/*` (11/16 refresh), `slate.html`, `injuries.html`, `results.html`, `availability.html` (new), `model.html` (new), `ledger.html` (new), all sidebars (12 → 15 links), `scripts/build_snapshots.py`, `scripts/build_brief_data.py`, `scripts/check_site.py` (PAGES), `tests/test_snapshots.py`, `tests/test_site_pages.py` (new), `README.md`, `index.html`, `review.html`.
**Not changed:** engine code, `assets/site.css`, and every other page's body content.

Every figure below was read from the official document named beside it during this pass. Nothing was inferred, and no unconfirmable value was filled.

---

## 1. Sources re-read on 2026-11-16 (all live, all official)

| # | Source | Read at (UTC) | What was taken from it |
| --- | --- | --- | --- |
| 1 | [NBA injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) | 15:03 and 15:05 | 11/16 report sequence 12:00 AM → 10:00 AM ET every 15 minutes; **10:00 AM ET newest at both checks**; policy text (5 p.m. day-before, 1 p.m. B2B, game-day 11 a.m.–1 p.m.) |
| 2 | [Injury-Report_2026-11-16_10_00AM.pdf](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_00AM.pdf) | 15:05 | All **72 rows**, 13 game blocks, every cell verbatim |
| 3 | [Injury-Report_2026-11-16_09_45AM.pdf](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_45AM.pdf) | 15:07 | All **72 rows** for the consecutive-revision diff |
| 4 | [2026-27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) (chunks covering rows 163–313) | 15:25 | Window rows **245–269** (11/16: 245–252; 11/17: 253–257; 11/18: 258–269), printed tip columns, broadcast columns, the "at" token boundary (rows ≤259 print none; 260–269 print it), plus rows 211–244 and 270–273 for the rest window |
| 5 | [NBA standings](https://www.nba.com/standings) (both chunks) | 15:05 | All 30 rows with HOME / ROAD / NEUTRAL / OT / LAST10 / STREAK splits; league totals 394 team-game lines, W = L = 197 |
| 6 | [Games page 11/15](https://www.nba.com/games?date=2026-11-15) + game pages 236–244 | 15:10–15:20 | Nine finals, printed quarter scores (plus OT1 on NYK@TOR), arenas, tips |
| 7 | [Games pages 11/16, 11/17, 11/18](https://www.nba.com/games?date=2026-11-16) | 15:15 | Slugs, game ids and tip clocks for all 25 window games (slug `away-vs-home`; id `00226002` + schedule row) |
| 8 | [NBA Terms of Use §9](https://www.nba.com/termsofuse) | carried forward from pass 9 (re-read 2026-11-16) | Gambling restriction unchanged; G0 still blocks every forecasting output |

A **final index re-read at 16:28 UTC (11:28 a.m. ET)** showed later 11/16 revisions through the 11:15 a.m. ET report. The published snapshot stays the 10:00 a.m. ET cycle it transcribed — the banner records both check times and the final re-read, and no claim says 10:00 a.m. is current.

The 09:15/09:30 AM injury fetches earlier in the session were **superseded** before publication: the index advanced to 10:00 AM, so the published diff pair is **09:45 → 10:00 AM**, and no 09:30 file was written.

## 2. Snapshot files written and verified (BD)

| File | Verification |
| --- | --- |
| `data/snapshots/raw/injury-2026-11-16T1000am-et.pipes` | 72 rows × 7 cells, transcribed twice independently ([report PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_00AM.pdf)) |
| `data/snapshots/raw/injury-2026-11-16T0945am-et.pipes` | 72 rows × 7 cells; meta swapped to the 09:45 revision ([report PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_45AM.pdf)) |
| `data/snapshots/injuries-2026-11-16-1000am.json` | Hand file of record: 72 rows, 13 blocks in document order, ISO `game_date`, 15 `NOT YET SUBMITTED` rows, 7 page-break-lost team cells (flagged, blank), 6 Golden State column-loss rows (status kept, reason blank, flagged), 2 `tip_disagreement` blocks ([report PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_00AM.pdf)) |
| `data/snapshots/injuries-2026-11-16-0945am.cells.json` · `…1000am.cells.json` | `cross_check`: **72 of 72 rows match row for row**, nothing one-sided ([report PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_00AM.pdf)) |
| `data/snapshots/injuries-2026-11-16-0945-to-1000.diff.json` | 0 status changes, 0 reason changes, **1 printing variance**: `Mathurin, Bennedict` → `Mathurin, Benedict` (NOP) ([09:45 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_45AM.pdf), [10:00 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_00AM.pdf)) |
| `data/snapshots/slate-2026-11-16.json` | 25 games; games-page id = `00226002` + row for **25 of 25**; tip matches **21 of 25** (rows 256, 257, 266, 267 keep both printed values); `at_token_printed` on rows 260–269; `LOCAL`/`ET` check 25 of 25 ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games page](https://www.nba.com/games?date=2026-11-16)) |
| `data/snapshots/standings-2026-11-16.json` | 30 rows; every row's HOME + ROAD + NEUTRAL = W + L; LAST10 wins + losses = 10 (or the games-played figure); league 196 + 196 + 2 = 394 lines, W = L = 197; neutral 1 game (DEN 1-0, IND 0-1) consistent with 197 games played; derived home record **102-94 / 196 = 0.5204** ([standings](https://www.nba.com/standings)) |
| `data/snapshots/results-2026-11-15.json` | 9 games, ids `0022600236`–`0022600244`; **18 of 18** period-sum checks agree; NYK@TOR carries five printed periods (OT1 17/13; quarters sum 95/95, 95+17=112, 95+13=108) ([games page](https://www.nba.com/games?date=2026-11-15)) |
| `data/snapshots/rest-window-2026-11-16.json` | 68 schedule rows covering 11/10–11/18; every window team has a prior game inside coverage (no gaps) ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf)) |
| `data/snapshots/aggregates-2026-11-16.json` | Produced by `build_brief_data.py`: home-court pin via `engine.homerate.pin_home_advantage` → **+0.614 pts proposed** (rate 0.5204, sd 12.0, z 0.0512); result feed 18/18 eligible; standings consistency wins = losses = 197 ([standings](https://www.nba.com/standings), [games page](https://www.nba.com/games?date=2026-11-15)) |

## 3. Tip-clock disagreements (kept as printed, never overwritten)

| Row | Matchup | Schedule PDF (Aug 13) | Games page | 11/16 10:00 AM report |
| --- | --- | --- | --- | --- |
| 256 | Indiana at Charlotte | 10:00 PM ET | **11:00 PM ET** | agrees with games page ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games page](https://www.nba.com/games?date=2026-11-17)) |
| 257 | Utah at LA Clippers | 11:00 PM ET | **10:30 PM ET** | agrees with games page (prints `10:30 (ET)`) ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games page](https://www.nba.com/games?date=2026-11-17)) |
| 266 | Boston at Denver | 9:00 PM ET | **9:30 PM ET** | not listed ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games page](https://www.nba.com/games?date=2026-11-18)) |
| 267 | Golden State at Dallas | 9:30 PM ET | **8:00 PM ET** | not listed ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games page](https://www.nba.com/games?date=2026-11-18)) |

Both values live in `slate-2026-11-16.json` (`tip_disagreement`), both are shown on the slate page, and no disagreeing game enters any projection. Flag **P10-04**, extending **AN-02**.

## 4. Away/home basis

`render_slate` shows "at" only where (a) the 10:00 AM report prints the same `AWAY@HOME` code for the same ISO game date (rows **245–257**, 13 codes — the eight 11/16 games including six `NOT YET SUBMITTED` blocks, and the five 11/17 `NOT YET SUBMITTED` blocks), (b) the schedule itself prints the token (rows **260–269**), or neither, in which case rows **258–259** show printed order and are flagged. Code matching stays date-aware: `POR@MIN` appears for 11/16 and again as the 11/17 row 254 (P8-10 regression kept). Rendered result: 23 "at" cells, **2** "(order unverified)" flags.

## 5. Site changes (AV + BC)

- **Three new pages:** `model.html` (component inventory + deliberate refusals), `availability.html` (snapshot summary + rest/B2B/3-in-4 table rendered by `engine.rest.slate_rest_table` over the 11/10–11/18 window), `ledger.html` (pre-registration, pick-hash ledger, seal layer, settlement stamp — all empty by design under G0).
- **Navigation:** 12 → 15 sidebar links on every page, in `check_site.PAGES` order, one `aria-current` per page.
- **Refreshed pages:** slate (25 rows, new window/banner), injuries (10:00 AM revision banner, 09:45→10:00 diff labels, provenance rows), results (2026-11-15 finals, OT column, dynamic pin and feed-lag text, 196/196/2 league totals).
- **Counts:** README and index now state **317** unit tests (`47 + 43 + 32 + 10 + 132 + 48 + 5`, seven suites).

### Checks run after the changes (all green)

- `python3 -m unittest discover -s tests -q` → **Ran 317 tests … OK**
- `python3 scripts/check_site.py` → **PASS: 15 pages, 541 HTML data rows and 824 Markdown data rows**
- `python3 scripts/build_snapshots.py --check` → all blocks in sync

## 6. Flags carried into this pass

| Flag | Status after pass 10 |
| --- | --- |
| BB-01 (injury table one day behind) | **Resolved for the current snapshot** (11/16 10:00 AM published); the untranscribed 11/15 06:30 a.m.–11:45 p.m. interval stays flagged for history ([index](https://official.nba.com/nba-injury-report-2026-27-season/)) |
| BB-02 (slate window behind calendar) | **Resolved** — window is 11/16 15:30 UTC → 11/19 15:30 UTC, rows 245–269 ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf)) |
| BB-03 (index date labels unchecked) | **Resolved** — index read twice, 10:00 AM ET newest at both checks, PDF header matches ([index](https://official.nba.com/nba-injury-report-2026-27-season/)) |
| AN-02 (schedule vs games-page tips) | **Open, extended** — four rows now disagree (P10-04) ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games page 11/18](https://www.nba.com/games?date=2026-11-18)) |
| P8-07 / P7-01 (11/14 05:00 PM rows never transcribed) | Open for history; not scheduled ([index](https://official.nba.com/nba-injury-report-2026-27-season/)) |
| P8-04 (rows with printed order only) | Narrowed to rows 258–259 (11/18); rows 260–269 now carry the schedule's own "at" token ([schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf)) |

New flags this pass: **P10-01 … P10-07**, recorded on the [Flagged for review](https://github.com/wingbangboozle1-lang/NBA4/blob/main/review.html) page in the pass-10 section.

## 7. Irregularities found this pass

1. **Overtime was unrepresentable** in the results table and absent from the settlement rule wording; the official NYK@TOR linescore prints an OT1 column. Fixed in the renderer and the rule text (P10-07); the engine's four-quarter check was left untouched and the OT row is asserted in the snapshot tests instead of being routed through a gate that refuses it.
2. **`render_aggregates` hard-coded the previous pin** (`+0.885 pts`, `12.0 x 0.0738`) and the previous feed lag (`9.78 h`); both now print from the data files, so the next refresh cannot publish a stale number (P10-05).
3. **A last-10 verification bug in this session's standings check** (wins-only comparison produced 29 false flags) was found and fixed before the file was published: games in last-10 are wins + losses, and the published checks report no disagreements.
4. **Column-loss at the GSW@NOP page break** (Butler III reason in the status position; Curry/Moody/Porzingis/Santos/Williams without a reason cell) is published blank and flagged, never repaired (convention unchanged from P8-01).

## 8. What was not done

- No line, price, probability, edge or pick was computed or published (G0 / IR-T4 standing refusal).
- No travel leg was published this cycle (no verified previous-opponent venue chain); the absence is stated on the availability page rather than estimated.
- No minutes or rotation projection was fitted from the injury report.
- The engine layer was not modified; `engine/resultfeed.check_line` still requires exactly four quarter scores, and the OT verification lives in the snapshot tests (P10-07 records the split).
