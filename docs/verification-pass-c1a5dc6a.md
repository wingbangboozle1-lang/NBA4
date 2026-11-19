# Verification pass 13 — session `arena/c1a5dc6a-nba4` (2026-11-19 daily refresh)

Board tasks BT (2026-11-19 snapshot refresh, verification pass 13) and BS (final
integration). Branch `arena/c1a5dc6a-nba4`, based on `main` at `8e94c1f` (after
PR #84 merged the parallel session's 01:45 AM file of record onto `main` at
`05baae4`). This log records every fetch of the pass, every check that was
computed (not asserted), every correction made before publication, and the flags
the pass opens, extends or closes. Post-pass state on this branch:
**586 unit tests OK** (47 + 48 + 43 + 32 + 57 + 135 + 38 + 10 + 29 + 44 + 6 + 89 + 8,
thirteen suites), site check **PASS (16 pages, 742 HTML data rows, 1350 Markdown
data rows)**, `scripts/build_snapshots.py --check` unchanged. No `engine/**` file
was modified.

Pass numbering note: pass 12 and pass 12b already exist (and two earlier sessions
each published a "pass 9"; see flag AN-08), so this pass uses its own number (13)
and its own flag sequence (`P13-`).

## 1. Fetches performed (2026-11-19, UTC times as recorded)

| What | URL | Time (UTC) | Outcome | Official source |
| --- | --- | --- | --- | --- |
| Injury-report index | https://official.nba.com/nba-injury-report-2026-27-season/ | 06:58 (1:58 a.m. ET), re-read ~08:00 | at the check time the newest listed report was 11/19 01:45 a.m. ET (11/19 entries run every 15 minutes from 12:00 a.m.; the later re-read also lists 2:00 a.m. ET onward, which supersede this snapshot) | [Index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Injury PDF 01:45 AM (file of record) | https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf | 06:58 (PR #84's transcription), independent re-read 07:35 | 44 rows: 42 across 13 game blocks (four 11/19 games, nine 11/20 games) + 2 continuation-page fragments kept unattributed; the independent read matched the file of record 44 of 44; PHX@UTA block prints `09:30 (ET)` | [PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| Injury PDF 10:30 AM (11/17, previous file of record) | https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf | via `engine.injurystore` for the diff | 60 rows; one-sided against the 01:45 file because the matchup is part of the match key (see checks) | [PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Schedule PDF (August release) | https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf | 07:00 (13 chunks) | window rows 43–51 (NBA Cup, 11/20) and 270–279 (11/19 and 11/21) transcribed verbatim; header "AS OF AUGUST 13, 2026 / SUBJECT TO CHANGE"; every window row prints the "at" token | [PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Games page 2026-11-19 | https://www.nba.com/games?date=2026-11-19 | 07:00 | 4 cards (rows 270–273); slugs/ids/tips corroborate the schedule rows | [Page](https://www.nba.com/games?date=2026-11-19) |
| Games page 2026-11-20 | https://www.nba.com/games?date=2026-11-20 | 07:00 | 9 cards (Cup rows 43–51); row 49 prints 9:00 PM ET against the schedule's 9:30 PM ET | [Page](https://www.nba.com/games?date=2026-11-20) |
| Games page 2026-11-21 | https://www.nba.com/games?date=2026-11-21 | 07:00 | 6 cards (rows 274–279) | [Page](https://www.nba.com/games?date=2026-11-21) |
| Games page 2026-11-17 | https://www.nba.com/games?date=2026-11-17 | 07:00 | 5 finals; each agrees with the gamebook | [Page](https://www.nba.com/games?date=2026-11-17) |
| Games page 2026-11-18 | https://www.nba.com/games?date=2026-11-18 | 07:00 | 12 finals; the board prints no venue cells (arena/city stay blank on the results rows) | [Page](https://www.nba.com/games?date=2026-11-18) |
| Gamebooks 2026-11-17 (5) | https://statsdmz.nba.com/pdfs/20261117/… (`NYKTOR`, `PORMIN`, `DETSAS`, `CHALAC`, `UTALAC`) | 07:00–07:30 | finals, periods, officials, inactives and the named report players' lines; TOR's visitor period line taken from the game page LINESCORES where the book splits it across chunks | [Gamebook index](https://statsdmz.nba.com/pdfs/20261117/20261117_NYKTOR_book.pdf) |
| Gamebooks 2026-11-18 (12) | https://statsdmz.nba.com/pdfs/20261118/… (all twelve finals) | 07:00–07:30 | finals + periods; SAC's book renders a garbled period row summing to 104 against the printed 107, so the game page LINESCORES (31/29/24/23/107) completes the row | [Gamebook index](https://statsdmz.nba.com/pdfs/20261118/20261118_MEMCLE_book.pdf) |
| Standings | https://www.nba.com/standings | 07:10 (chunks 0–1) | 30 rows transcribed; Indiana's row prints `NEUTRAL 0-1` (re-fetched and confirmed after the built-in split check failed on a 0-0 transcription) | [Page](https://www.nba.com/standings) |
| Team stats — advanced | https://www.nba.com/stats/teams/advanced | 07:10 (chunks 0–1) | 30 rows × 20 cells (RANK columns served empty, not transcribed) | [Page](https://www.nba.com/stats/teams/advanced) |
| Team stats — opponent | https://www.nba.com/stats/teams/opponent | 07:10 (chunks 0–1) | 30 rows × 26 cells | [Page](https://www.nba.com/stats/teams/opponent) |
| Team stats — traditional | https://www.nba.com/stats/teams/traditional | not re-read for publication | still not transcribed; publication stays an owner decision (flag P9-06 persists) | [Page](https://www.nba.com/stats/teams/traditional) |

No fetch of a betting/market/odds source was performed; the rights gate (G0)
remains uncleared and nothing on the site is a pick.

## 2. Checks computed in this pass (not asserted)

| Check | Result | How | Official source |
| --- | --- | --- | --- |
| Independent re-read of the 01:45 report | 44 of 44 rows match the file of record; 0 one-sided after the 7 page-break NYS rows are attached to their blocks by position | `cross_check` in `injuries-2026-11-19-0145am.cells.json` | [01:45 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| Day-apart injury diff (10:30 → 01:45) | 60 old → 42 new rows; 60 `REMOVED_OR_REALIGNED` + 42 `ADDED_OR_REALIGNED`; 0 of 102 matched on the identity key; status/reason/team/printing counts 0 because nothing pairs | `engine.injurystore.diff_revisions` via `scripts/_gen_bt_2026_11_19_b.py` | [10:30 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Slate window and ids | 19 games, rows {43–51} ∪ {270–279}, dates 11/19–11/21; every games-page id equals `00226000`+row for Cup rows and `0022600`+row for date-window rows (19/19) | `slate-2026-11-19.json` + `tests/test_snapshots.py::SlateSnapshotTests` | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Away/at corroboration | every row prints the schedule's "at" token (19/19); 13 of 19 also carry the 01:45 report's matchup code for the same date; no row shows printed order alone | `tests/test_snapshots.py::AwayHomeBasisTests` | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Tip disagreements kept, never overwritten | one conflict: row 49 PHX–UTA — games page 9:00 PM ET vs schedule PDF 9:30 PM ET vs report `09:30 (ET)`; both clocks published | `tip_disagreement`, `tip_disagreements_kept_as_printed = [49]` on the slate file | [Games 11/20](https://www.nba.com/games?date=2026-11-20) |
| 11/17 results | 5 finals; 10/10 team lines sum to the printed finals; winner/loser arithmetic on every row; one OT game (CHA@LAL, 114–118 with OT periods 3/7) kept in `away_ot`/`home_ot` | `results-2026-11-17.json` `verification.quarter_sum_check` | [Games 11/17](https://www.nba.com/games?date=2026-11-17) |
| 11/18 results | 12 finals; 24/24 team lines sum to the printed finals; no game went to OT; both documents agree on both finals 12/12 | `results-2026-11-18.json` `verification` | [Games 11/18](https://www.nba.com/games?date=2026-11-18) |
| Standings internal | 30/30 rows: HOME+ROAD+NEUTRAL = W+L; league W = league L = 222; 221 home + 221 road + 2 neutral = 444 team-game lines | `standings-2026-11-19.json` `consistency_checks` | [Standings](https://www.nba.com/standings) |
| GP/W/L agree: standings vs advanced vs opponent | 30/30 both pages | `team-stats-2026-11-19.json` + `tests/test_snapshots.py::TeamStatsSnapshotTests` | [Advanced](https://www.nba.com/stats/teams/advanced) |
| Rest window | 87 prior-game rows, 11/10–11/21; every window team has a prior game inside the window with ≥1 day of rest | `rest-window-2026-11-19.json` + `RestWindowTests` | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Home-win rate from HOME splits | 111–110 over 221 home games = 0.5023 (neutral 1–1 held out) → +0.068 pts (PROPOSED, NOT APPLIED; `ratings.HOME_ADVANTAGE_POINTS` stays 0.0) | `engine.homerate.pin_home_advantage` via `build_brief_data.build_aggregates` | [Standings](https://www.nba.com/standings) |
| Settlement feed | 12 finals of 11/18, 24 team lines checked, 0 disagreements, settlement-eligible | `aggregates-2026-11-19.json` `result_feed` | [Games 11/18](https://www.nba.com/games?date=2026-11-18) |
| Injury load counts | 42 block rows, 21 with a status, 15 NOT YET SUBMITTED, 13 unverified after page breaks | `aggregates-2026-11-19.json` `injury_load` | [01:45 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| Gamebook mirror of the 01:45 report | 21 named report rows covered exactly once (21 dated observation rows: 6 played lines, 14 inactive-list entries, 1 DND), plus the 2 nameless GSW/MEM NOT YET SUBMITTED rows recorded as gaps with no invented names; every observation date falls inside the 11/17–11/18 window | `scripts/build_gamelogs.py` mirror check + `tests/test_snapshots.py::GameLogTests` | [Gamebooks](https://statsdmz.nba.com/pdfs/20261117/20261117_UTALAC_book.pdf) |
| Derived files re-derive byte-identically | `build_snapshots.py --check`, `build_gamelogs.py --check` unchanged; `check_site.py --with-tests` PASS | run at the end of the pass | [Repo scripts](https://github.com/wingbangboozle1-lang/NBA4/tree/main/scripts) |
| Full suite | 586 tests OK | `python3 -m unittest discover -s tests -t .` | [Repo tests](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |

## 3. Corrections made during the pass (transparently, before publication)

1. **DET@NOP home Q4 (11/18).** The transcription read 23; the built-in check
   failed because the quarters must sum to the printed final 109. The source row
   was re-fetched and re-read: Q4 is 34 (109 = 20+29+26+34). Corrected from the
   document, never by arithmetic adjustment.
2. **Indiana NEUTRAL cell.** The standings transcription read `0-0`; the split
   check failed because the row's games played must equal W+L+NEUTRAL games.
   Re-fetched standings chunk 0: the page prints `NEUTRAL 0-1`. Corrected from
   the document.
3. **Game-log window label.** The first build labelled the game-log snapshot
   `2026-11-18_to_2026-11-19` while every observation in it is dated 2026-11-17.
   The window follows the prior cycle's rule — the two days before the slate day
   — so the file, its `observation_window` and the page heading were re-dated to
   `2026-11-17_to_2026-11-18`, and a suite assertion now pins every observation
   date inside the window.
4. **Played-line schema.** The re-run of the game-log generator initially wrote
   played entries without the `line_printed` cell `build_gamelogs.py` requires
   (and with a non-null `designation_printed`). Fixed to the established schema
   (`line_printed` = the verbatim box line, `designation_printed` = null) and
   re-generated.
5. **`review.html` markup.** The BX-01 row rewrite dropped its closing `</tr>`,
   which the HTML-nesting audit caught; restored.
6. **Stated counts.** README's unit-test total and per-suite breakdown and the
   index metric were re-derived from the suite (586) after the new-cycle tests
   landed, per the standing rule that counts land last.

## 4. Flags opened, extended or closed by this pass (mirrored on review.html)

| Flag | State | Note | Source for review |
| --- | --- | --- | --- |
| P13-01 | opened (open) | Row-49 tip conflict is now three-way: games page 9:00 vs schedule 9:30 vs report `09:30 (ET)`; two of three documents agree on 9:30; both clocks kept, no disagreeing game modelled | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games 11/20](https://www.nba.com/games?date=2026-11-20), [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| P13-02 | opened (info) | Day-apart injury diff cannot pair any row (matchup in the identity key); the zero change counts mean "nothing paired", not "nothing changed" | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf), [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| P13-03 | opened (info) | Page-break cells kept blank and flagged: 2 unattributed fragments, 6 lost reason cells, 7 block-position NYS rows | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| P13-04 | opened (info) | Persistent gaps: BB-01, P8-07, P9-06 stay open; the index already lists 11/19 2:00 a.m. ET and later revisions this snapshot does not transcribe | [injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/), [traditional team-stat page](https://www.nba.com/stats/teams/traditional) |
| P13-05 | opened (info) | Game-log mirror reads exactly three gamebooks because every named report player's team last played on 11/17 | [gamebook UTALAC](https://statsdmz.nba.com/pdfs/20261117/20261117_UTALAC_book.pdf) |
| P13-06 | opened (resolved) | The two transcription errors of §3 were caught by built-in checks before publication | [games 11/18](https://www.nba.com/games?date=2026-11-18), [standings](https://www.nba.com/standings) |
| P12-02 | **closed** | `check_site.py`'s team-stats audit now follows the newest dated `team-stats-*.json` instead of a fixed pin | [check_site.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| BX-01 | **closed** | Banner and pointer now follow the newest stored revision (01:45 AM), re-dated each cycle | [11:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_15AM.pdf), [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| AN-02 | extended | One conflict in the current window (row 49); the prior window's four conflicts are historical | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [games 11/20](https://www.nba.com/games?date=2026-11-20) |

## 5. Snapshots published this cycle (`data/snapshots/`)

- `schedule-2026-11-19-window-rows-43-51-270-279.txt` (raw verbatim window rows)
- `slate-2026-11-19.json` (19 games; `tip_disagreements_kept_as_printed = [49]`)
- `injuries-2026-11-19-0145am.json` (file of record, PR #84) and
  `injuries-2026-11-19-0145am.cells.json` (independent re-read, 44/44)
- `injuries-2026-11-17-1030-to-1119-0145.diff.json` (day-apart diff)
- `results-2026-11-17.json` (5 finals), `results-2026-11-18.json` (12 finals)
- `standings-2026-11-19.json` (30 rows), `team-stats-2026-11-19.json` (30+30)
- `rest-window-2026-11-19.json` (87 rows), `aggregates-2026-11-19.json`
- `player-gamelogs-2026-11-17_to_2026-11-18.json` (23 players, 21 game rows)
- `raw/injury-2026-11-19T0145am-et.txt` (PR #84's raw text, kept for provenance)

## 6. Gates and rights stance (unchanged)

Rights gate G0 is uncleared: no licensed feed, no validated strategy, no pick.
Every page still carries `NO PICKS ISSUED`. The `daily-refresh` workflow keeps
its documented standing failure (BH-01/BH-05 transport and cadence gates fail
closed by design); this pass does not weaken any gate to make a check green.

## 7. Integration record (BS)

- PR #72 (stale, from an earlier session with no activity) is closed with a
  comment pointing at this pass's work.
- This branch's integration PR carries the snapshots, page re-dates, suite
  extension (586 tests), the pass-13 review section and this log; the merge
  record is appended below once the PR number exists.

### Merge record

(to be appended after the integration PR opens and merges)
