# Verification pass 12 — session `arena/5cca4190-nba4` (2026-11-17 daily refresh)

Board tasks BM–BO (2026-11-17 refresh cycle, verification pass 12, final integration).
Branch `arena/5cca4190-nba4`, based on `main` at `96434de`. This log records every
fetch of the pass, every check that was computed (not asserted), every correction
made before publication, and the flags the pass opens or extends. Post-pass state on
this branch after the rebase onto `main`@`49e7238`: **547 unit tests OK** (47 + 48 + 43 + 32 + 57 + 135 + 38 + 10 + 44 + 27 + 6 + 60,
twelve suites — the +44 transport suite and this file's edits are folded from or reconciled with the parallel sessions below),
site check **PASS (16 pages, 646 HTML data rows, 1275 Markdown data rows)**.
No `engine/**` file was modified (verified with `git diff 96434de --name-only | grep -c '^engine/' = 0`).

Pass numbering note: two earlier sessions each published a "pass 9" (see flag AN-08),
so this pass uses its own number (12) and its own flag sequence (`P12-`).

## 1. Fetches performed (2026-11-17, UTC times as recorded)

| What | URL | Time (UTC) | Outcome | Official source |
| --- | --- | --- | --- | --- |
| Injury-report index | https://official.nba.com/nba-injury-report-2026-27-season/ | 15:42 (10:42 a.m. ET) | newest listed report = 11/17 10:30 a.m. ET; 11/17 entries run every 15 minutes from 12:00 a.m. | [Index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Injury PDF 10:30 AM | https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf | 15:49 | 60 rows across 17 game blocks transcribed verbatim; 12 11/18 blocks print NOT YET SUBMITTED; POR@MIN filed no player rows | [PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Injury PDF 10:15 AM | https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf | 15:44 | 60 rows; content identical to the 10:30 extraction row for row | [PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_15AM.pdf) |
| Schedule PDF (August release) | https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf | 15:45–15:52 (chunks 1–2) | window rows 253–273 transcribed; header "AS OF AUGUST 13, 2026 / SUBJECT TO CHANGE" | [PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Games page 2026-11-17 | https://www.nba.com/games?date=2026-11-17 | 15:45 | 5 cards, rows 253–257; slugs/ids/tips corroborate the schedule rows | [Page](https://www.nba.com/games?date=2026-11-17) |
| Games page 2026-11-18 | https://www.nba.com/games?date=2026-11-18 | 15:46 | 12 cards, rows 258–269 | [Page](https://www.nba.com/games?date=2026-11-18) |
| Games page 2026-11-19 | https://www.nba.com/games?date=2026-11-19 | 15:46 | 4 cards, rows 270–273 | [Page](https://www.nba.com/games?date=2026-11-19) |
| Games page 2026-11-16 | https://www.nba.com/games?date=2026-11-16 | 15:47 (chunks 0–1) | all eight finals; postgame displayed records match the standings page | [Page](https://www.nba.com/games?date=2026-11-16) |
| Game summary HOU@MIA | https://www.nba.com/game/hou-vs-mia-0022600249 (+ /box-score) | 15:47–15:48 | LINESCORES HOU 15/31/35/29, MIA 29/33/39/27 — supplies the visitor quarter line the gamebook loses at its page break | [Page](https://www.nba.com/game/hou-vs-mia-0022600249) |
| Gamebooks 2026-11-16 (7 PDFs + corrected PHXDEN) | https://statsdmz.nba.com/pdfs/20261116/20261116_{ORLBOS,CHICLE,MEMWAS,PHIBKN,HOUMIA,PORMIN,GSWNOP,PHXDEN}_book.pdf | 15:47–15:50 | finals + quarter scores + venues + officials; HOUMIA book loses the visitor SCORE BY PERIOD row at a page break (irregularity recorded on the results snapshot) | [Gamebook index](https://statsdmz.nba.com/pdfs/20261116/20261116_ORLBOS_book.pdf) |
| `20261116_PHDEN_book.pdf` (mistyped id) | https://statsdmz.nba.com/pdfs/20261116/20261116_PHDEN_book.pdf | 15:49 | 404 — the correct identifier is `PHXDEN`; the corrected fetch succeeded. Recorded so nobody retries the mistyped URL | [Gamebook index](https://statsdmz.nba.com/pdfs/20261116/20261116_PHXDEN_book.pdf) |
| Standings | https://www.nba.com/standings | 15:50 (chunks 0–1), re-read 16:05 | 30 rows + tie-break text; re-read confirmed the transcription cell for cell | [Page](https://www.nba.com/standings) |
| Team stats — advanced | https://www.nba.com/stats/teams/advanced | 16:12–16:16 (chunks 0–1) | 30 rows × 20 cells (RANK columns served empty, not transcribed); Miami row split at the chunk seam, rejoined | [Page](https://www.nba.com/stats/teams/advanced) |
| Team stats — opponent | https://www.nba.com/stats/teams/opponent | 16:16–16:20 (chunks 0–1) | 30 rows × 26 cells; Cleveland row split at the chunk seam, rejoined | [Page](https://www.nba.com/stats/teams/opponent) |
| Team stats — traditional | https://www.nba.com/stats/teams/traditional | 16:21 (chunk 0) | this cycle the extraction served the first rows of the data table (5 chunks total); the wide column set is again NOT transcribed and publication stays an owner decision (flag P9-06) | [Page](https://www.nba.com/stats/teams/traditional) |
| Gamebook NYK@TOR 11/15 | https://statsdmz.nba.com/pdfs/20261115/20261115_NYKTOR_book.pdf | 16:28 | box score + inactive list; the four Raptors report players are on the printed inactive list; SCORE BY PERIOD matches results-2026-11-15 | [PDF](https://statsdmz.nba.com/pdfs/20261115/20261115_NYKTOR_book.pdf) |
| Gamebook SAS@UTA 11/15 | https://statsdmz.nba.com/pdfs/20261115/20261115_SASUTA_book.pdf | 16:30 | Jaxson Hayes carries a printed DND designation; the other nine report players are on the printed inactive lists | [PDF](https://statsdmz.nba.com/pdfs/20261115/20261115_SASUTA_book.pdf) |
| Gamebook CHA@LAC 11/15 | https://statsdmz.nba.com/pdfs/20261115/20261115_CHALAC_book.pdf | 16:32 | all nine CHA/LAC report players on the printed inactive lists | [PDF](https://statsdmz.nba.com/pdfs/20261115/20261115_CHALAC_book.pdf) |
| Gamebook LAL@PHX 11/15 | https://statsdmz.nba.com/pdfs/20261115/20261115_LALPHX_book.pdf | 16:34 | Grimes and Kessler have printed played lines; Reaves is on the printed Lakers inactive list (team attribution for the lost report team cell) | [PDF](https://statsdmz.nba.com/pdfs/20261115/20261115_LALPHX_book.pdf) |

No fetch of a betting/market/odds source was performed; the rights gate (G0) remains uncleared
and nothing on the site is a pick.

## 2. Checks computed in this pass (not asserted)

| Check | Result | How | Official source |
| --- | --- | --- | --- |
| Standings internal: HOME+ROAD+NEUTRAL = W+L per row | 30/30 | derived fields on each row of `standings-2026-11-17.json` | [Standings](https://www.nba.com/standings) |
| League W = league L; home+road+neutral = 410 team-game lines | 205 = 205; 204 + 204 + 2 | `standings-2026-11-17.json` `consistency_checks` + `aggregates-2026-11-17.json` | [Standings](https://www.nba.com/standings) |
| Standings vs postgame displayed records | BOS 11-3 and ORL 6-7 on the games page match the standings rows (BOS lost to ORL; ORL won); CLE 8-7, MIA 8-6, GSW 8-6 consistent with the 11/16 finals | manual re-check of the fetched pages | [Games 11/16](https://www.nba.com/games?date=2026-11-16) |
| GP/W/L agree: standings vs advanced vs opponent | 30/30 both pages | computed in `team-stats-2026-11-17.json` `cross_checks`; asserted by `tests/test_snapshots.py::TeamStatsSnapshotTests` | [Advanced](https://www.nba.com/stats/teams/advanced) |
| DefRtg vs Opp PTS best-five sets | same five teams (MIN, BOS, SAS, NYK, OKC), order differs; exact equality NOT claimed (per-100 vs per-game) | computed in the snapshot's `cross_checks` | [Opponent](https://www.nba.com/stats/teams/opponent) |
| 11/16 results: 8 finals, period sums = printed finals | 16/16 team lines | `results-2026-11-16.json` `verification.quarter_sum_check` | [Games 11/16](https://www.nba.com/games?date=2026-11-16) |
| Finals cross-check (games page vs gamebook/summary) | 8/8 games agree on both finals | `verification.finals_cross_check` | [Games 11/16](https://www.nba.com/games?date=2026-11-16) |
| 10:15 → 10:30 injury diff | 60→60 rows; 0 status/reason/team changes; 0 printing variances; alignment "60 of 60 matched" | `engine.injurystore.diff_revisions` via `scripts/build_brief_data.py` | [10:30 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Independent re-extraction of the 10:30 report | 60 of 60 rows match row for row; nothing one-sided | `cross_check` in `injuries-2026-11-17-1030am.cells.json` vs the canonical file | [10:30 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Slate corroboration | 21/21 rows: 17 carry the 10:30 report's AWAY@HOME code for the same date, 4 more (11/19 rows 270–273) print the schedule's own "at" token; every game id equals 00226002 + schedule row | `slate-2026-11-17.json` + `tests/test_snapshots.py::AwayHomeBasisTests` | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Tip disagreements kept, never overwritten | rows 256, 257, 266, 267 (same four as the 11/16 cycle; AN-02 stays open) | `tip_disagreement` on the slate file and page | [Games pages](https://www.nba.com/games?date=2026-11-18) |
| Home-win rate from HOME splits | 106-98 = 0.5196 → +0.59 pts (PROPOSED, NOT APPLIED; `ratings.HOME_ADVANTAGE_POINTS` stays 0.0) | `engine.homerate.pin_home_advantage` via `build_brief_data.py` | [Standings](https://www.nba.com/standings) |
| Gamebook mirror of the 11/17 report | 34/34 printed player rows covered exactly once (26 game rows from 4 gamebooks, 7 Detroit window gaps, 1 page-break fragment with no game log) | `scripts/build_gamelogs.py` mirror check + `tests/test_snapshots.py::GameLogTests` | [Gamebooks](https://statsdmz.nba.com/pdfs/20261115/20261115_LALPHX_book.pdf) |
| Gamebook SCORE BY PERIOD vs results-2026-11-15 | 4/4 games agree period for period (incl. the NYK@TOR double-OT line) | recorded in the gamelogs snapshot's extraction notes | [Games 11/15](https://www.nba.com/games?date=2026-11-15) |
| Derived files re-derive byte-identically | `build_brief_data.py --check`, `build_snapshots.py --check`, `build_gamelogs.py --check` all unchanged | run twice during the pass | [Repo scripts](https://github.com/wingbangboozle1-lang/NBA4/tree/main/scripts) |
| Unit suite | 547 tests OK (60 in the snapshot suite, incl. three tests folded from the parallel BM session and re-pointed at this extraction) | `python3 -m unittest discover -s tests -t .` | [Repo tests](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| Site check | PASS: 16 pages, 646 HTML data rows, 1275 Markdown data rows; engine tests green | `python3 scripts/check_site.py --with-tests` | [Repo site check](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| No engine edits this cycle | 0 engine files in `git diff 96434de --name-only` | verified | [Repo engine](https://github.com/wingbangboozle1-lang/NBA4/tree/main/engine) |

## 3. Corrections made during the pass (transparently, before publication)

* **Slate tip-comparison bug (found and fixed in-session).** The first draft of the
  slate generator compared the games-page tip with the schedule column using
  `gp_tip.replace(" ET", " PM")`, which turned "7:30 PM ET" into "7:30 PM PM" and
  flagged every row as a tip disagreement. The comparison was corrected to strip
  the trailing " ET", the snapshot regenerated, and the pages re-spliced. Exactly
  four disagreements remain (256, 257, 266, 267 — the same four publications as the
  11/16 cycle). The pages were never pushed with the buggy data.
* **`render_results` row unpacking.** The 11/16 results schema stores overtime
  periods in explicit trailing arrays (`away_ot`/`home_ot`) instead of extending the
  quarter array; the renderer crashed with "too many values to unpack" and was
  generalised to read both schemas (the 11/15 file keeps its extended-quarter form).
* **`build_aggregates` neutral-site note.** The derived aggregates carried a
  hard-coded "Two league games are played at a neutral site" note from the 11/16
  build. The note is now computed from the transcribed NEUTRAL column (2 team-game
  lines) and `home_plus_road_plus_neutral` is filled with the computed 410 instead
  of `null`.
* **Hard-coded renderer prose.** `render_availability_summary` still said "Golden
  State rows" and claimed "report and games page agree" for every disagreement; both
  texts are now data-driven/generic (this cycle's column loss is the Minnesota/
  Reaves page-break rows, and GSW@DAL's disagreement is games-page-vs-schedule only).
* **Home-advantage paragraph.** The results-page paragraph was first updated with a
  hand-derived "+0.301 points" that did not match the engine conversion; corrected
  to the value the pin actually computes (+0.59 = 12.0 × Phi⁻¹(0.5196)) before
  publication.
* **`game_label` for a block with no printed tip.** GSW@DAL prints no time cell in
  the 10:30 report; the injuries table now prints "(no tip printed)" instead of an
  empty clock.

## 4. Flags opened or extended by this pass (mirrored on review.html)

| Flag | Status | What | Why it does not block the informational site | Official source |
| --- | --- | --- | --- | --- |
| P12-01 | Resolved | The 2026-11-17 observation set is published (report 60/60 rows incl. both printed page-break rows, diff 0 changes, window 21/21 corroborated, eight 11/16 finals, standings split, team stats, game-log mirror) — see §2 | This closes the pass-10 row's open items (standings, team stats, games-page check) on the rebased tree. | [10:30 AM report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) · [standings](https://www.nba.com/standings) |
| P12-02 | Open (owner) | `scripts/check_site.py::audit_team_stats` still pins `team-stats-2026-11-16.json` | The checker is outside this session's recorded file scope, so the repoint to `team-stats-2026-11-17.json` is logged as a request in COORDINATION.md rather than edited. The gap is covered on this branch by `tests/test_snapshots.py::TeamStatsSnapshotTests`, which asserts the same properties (30 unique rows, no RANK keys, GP/W/L agreement with the standings) for the 11/17 file. The site check still passes because the 11/16 file remains in the repo as dated history. | [Advanced page](https://www.nba.com/stats/teams/advanced) · [checker on main](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| P12-03 | Info | Daily-refresh workflow run 44072241605 failed; its log could not be downloaded (`gh run view --log-failed` ended with EOF) | The cause is unresolved and deliberately not asserted. The site publishes dated observations with their own provenance, so a CI refresh failure cannot publish anything by itself. Owner re-check requested in COORDINATION.md. | [Repository actions](https://github.com/wingbangboozle1-lang/NBA4/actions) |
| P12-04 | Info | Name/spacing variances between the 11/15 gamebooks and the 11/17 report: Nurkić/Nurkic (plus "Right 2nd Plantar Plate Tear" vs "Right Right Foot; 2nd Plantar Plate Tear"), Niederhäuser/Niederhauser, Schröder/Schroder | Both spellings are kept as printed and flagged on the game-log rows (SP-02..SP-04); nothing is normalised. | [SAS@UTA gamebook](https://statsdmz.nba.com/pdfs/20261115/20261115_SASUTA_book.pdf) · [10:30 AM report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| P12-05 | Open | AN-02 extended: the four tip conflicts are re-confirmed by the 11/17 sources; GSW@DAL additionally prints no time cell in the 10:30 report, so its block carries both printed values and no report clock | Both values of every conflict stay published side by side; no disagreeing game is modelled. | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) · [games page 11/18](https://www.nba.com/games?date=2026-11-18) |

The pre-existing open flags BB-01, P8-07 and P9-06 are unchanged this cycle and are
restated in the refreshed page banners where they apply.

## 5. Line-by-line review of this cycle's own diffs

* `scripts/build_brief_data.py` — the current build is now driven entirely by the
  `PAIR` table (pipes names, snapshot ids, diff id, input files, aggregates id and
  `derived_at_utc`); the previously hard-coded file names are gone, so the next
  cycle is a data change, not a code change. `build_aggregates` now takes its
  aggregate id, derived timestamp and input names as parameters.
* `scripts/build_snapshots.py` — the renderer constants point at the 11/17
  snapshots; the results renderer handles both period-score schemas; the summary
  renderer's counts (rows, NOT YET SUBMITTED, lost team cells, column loss, tip
  disagreements) are computed from the files, and its previously hard-coded team
  name is gone.
* `scripts/build_gamelogs.py` — constants repointed (gamelogs file, injury file of
  record, report URL/label); the mirror check is unchanged and passes against the
  11/17 file.
* `tests/test_snapshots.py` — current-file assertions moved to the 11/17 snapshots
  (60 injury rows, 21 slate rows, 16 result lines, aggregates 106-98/0.5196, diff
  with zero changes); the 11/16 assertions are kept as historical classes
  (`InjurySnapshot20261116Tests`, `Aggregates20261116Tests`, `ResultsSnapshot20261115Tests`);
  new classes cover the 11/17 team-stats file and the page-break specifics of this
  cycle's report.
* New snapshot files: `slate-2026-11-17.json`, `standings-2026-11-17.json`,
  `results-2026-11-16.json`, `rest-window-2026-11-17.json`,
  `injuries-2026-11-17-1030am.json` (+ the 10:15/10:30 raw `.pipes` archives),
  `injuries-newest-pointer-2026-11-17.json`, the derived cells/diff/aggregates
  files, `team-stats-2026-11-17.json` and
  `player-gamelogs-2026-11-15_to_2026-11-16.json` — every one carries the four
  provenance fields `check_site.py` audits, and every published row carries an
  official-HTTPS link in its last cell.

## 6. Collision with the parallel sessions on `main` (PRs #70 and #71) and its resolution

While this pass was running, two parallel sessions landed on `main`:

* `arena/4326c586-nba4` (PR #70) independently ran the same 2026-11-17 refresh (also claimed
  as task BM on the board) and published `slate-2026-11-17.json`, `injuries-2026-11-17-1030am.json`
  and the raw schedule transcription, with its own verification log
  ([`docs/verification-pass-4326c586.md`](docs/verification-pass-4326c586.md)).
* `arena/af666c53-nba4` (PR #71) built the official-page transport layer on top (tasks BU–BW)
  and remeasured the suite on that tree.

The rebase of this branch onto `main`@`49e7238` hit conflicts exactly in the shared day-files.
Resolution, per the board's standing union rule (nothing discarded, the published record stays
coherent):

* **`slate-2026-11-17.json` — both versions compared first.** The two independent transcriptions
  agree on every core value (21 rows 253–273, same teams, dates, tips, ids, corroboration codes,
  and all 21 tips equal the verbatim raw lines both sessions transcribed). The versions differ in
  framing metadata only. Resolved to this branch's version because the whole derived stack
  (aggregates, tests, pages) is keyed to it; it carries the window *rule* and the
  `games_page_corroboration` summary blocks.
* **`injuries-2026-11-17-1030am.json` — resolved to this branch's version.** The core named rows
  agree (both extractions have the same 17 blocks and the same status/reason cells). They differ
  in the two printed page-break rows: main's version keeps 58 block rows and moves the Reaves row
  to an `unattributed_rows` side list, and does not publish the printed `Soreness` fragment at
  all; this branch's version keeps all 60 printed rows in place with the lost cells blank and
  flagged, per the repo's lost-cell rule ("a lost cell stays blank and is flagged, never filled").
  Main's version also states it fills lost game-date cells from the schedule — that conflicts
  with the same rule, so the first-pass row's handling was not adopted.
* **The raw 10:30 pipes** — both transcriptions of the same document; resolved to this branch's
  (byte-level peer of main's; the mirror check runs against it).
* **`scripts/build_snapshots.py`, the generated page blocks and the rewritten test file** —
  resolved to this branch's versions, which are the generator of the resolved data files. Main's
  `build_snapshots.py` still pointed at the 11/16 snapshot constants (its 11/17 tables were
  written by its own `build_window_2026_11_17.py`), so adopting it would have desynced the
  checker's `--check` modes from the published 11/17 pages.
* **Folded, not dropped.** Main's three compatible test ideas were folded into the snapshot
  suite (slate rows 253–273, slate-vs-verbatim-raw-lines, revision-is-the-10:30-document), two
  were folded in adapted form (the unattributed-row assertions are re-pointed at this file's
  lost-row structure; the tip-conflict set is the four conflicts this extraction prints, main's
  version listed three), and the transport suite (`tests/test_official_pages.py`, 44 tests),
  the capture workflow and captures, `docs/official-pages-transport.md`, the board rows and the
  pass-10 log all survive the rebase untouched.
* **Counts remeasured on the merged tree** (README/index are coupled by `audit_consistency`):
  547 tests across twelve suites; site check 16 pages / 646 HTML rows / 1275 Markdown rows.
