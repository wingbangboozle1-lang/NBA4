# Verification pass 13 — eleventh daily refresh cycle (2026-11-19)

Session `arena/76f88812-nba4` · board task **BR** (see [COORDINATION.md](../COORDINATION.md)) · branch `arena/76f88812-nba4`.

Every fetch in this cycle ran between **06:59 and 07:07 UTC on 2026-11-19**. Per-document times were not logged, so the files carry that window, not a precise time. This pass produces no line, price, probability, pick, bet, parlay, prop combination or leaderboard entry. Rights gate G0 and decision D-01 still stand.

## 1. Status of each feed this cycle

| Feed | Status | Evidence |
| --- | --- | --- |
| Per-game results, 2026-11-17 (5 games) and 2026-11-18 (12 games) | **Refreshed and settled**: 17 of 17 games, 34 of 34 team lines | [games 11/17](https://www.nba.com/games?date=2026-11-17) · [games 11/18](https://www.nba.com/games?date=2026-11-18) · `data/snapshots/results-2026-11-17.json` · `results-2026-11-18.json` |
| Injury report, newest revision 01:45 AM ET, 11/19 | **Refreshed**, 44 rows | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) · `data/snapshots/injuries-2026-11-19-0145am.json` |
| Consecutive revision diff, 01:30 → 01:45 AM ET | **Computed**: 0 status, 0 reason, 0 team changes | [01:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_30AM.pdf) · `data/snapshots/injuries-2026-11-19-0130-to-0145.diff.json` |
| Schedule window beyond 11/19 (11/20 to 11/21) | **Not refreshed**: flag BR-S1 | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Standings | **Not refreshed**: flag BR-S2 | [NBA standings](https://www.nba.com/standings) · last stored `data/snapshots/standings-2026-11-17.json` |
| Official team statistics (traditional, opponent, advanced) | **Not refreshed**: flag BR-S2 | [NBA team stats](https://www.nba.com/stats/teams/traditional) |
| Per-player game logs | **Not refreshed** | [NBA.com game summaries](https://www.nba.com/games?date=2026-11-19) |
| Scheduled `daily-refresh` job | **Latest scheduled run failed**: flag BR-J1 | [Workflow run 44293154114](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/44293154114) |

## 2. Fetch log

| Document | Result | Source |
| --- | --- | --- |
| Games page, 11/18 | 12 Final rows, game ids 0022600258–0022600269 | [nba.com/games?date=2026-11-18](https://www.nba.com/games?date=2026-11-18) |
| Games page, 11/17 | 5 Final rows, game ids 0022600253–0022600257 | [nba.com/games?date=2026-11-17](https://www.nba.com/games?date=2026-11-17) |
| Game summary pages, 17 finals (LINESCORES and GAME INFO) | 17 of 17 read; quarter sums checked against finals | e.g. [NYK–TOR 0022600253](https://www.nba.com/game/nyk-vs-tor-0022600253) |
| Gamebook PDFs for 11/16 ORL@BOS, 11/17 NYK@TOR, 11/18 MEM@CLE | **Fetch error on all three**: flag BR-G1 | e.g. [11/17 NYK@TOR gamebook](https://statsdmz.nba.com/pdfs/20261117/20261117_NYKTOR_book.pdf) |
| Injury-report index, 11/19 entries | 12:00 a.m. to 1:45 a.m. ET listed; no 11/18 entries transcribed | [official.nba.com injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Injury PDFs, 01:30 and 01:45 AM ET, 11/19 | 44 rows each, single chunk | [01:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_30AM.pdf) · [01:45 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |

## 3. Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Settlement rule (regulation periods plus printed OT equal the printed Final; scoreboard Final equals linescore Final) | 11/17: 10 of 10 lines agree. 11/18: 24 of 24 lines agree. All 17 games agree. | `build_window_2026_11_19.py --check`; [games 11/17](https://www.nba.com/games?date=2026-11-17) |
| Overtime, CHA 114 @ LAL 118 (0022600256) | One OT: CHA 34-32-28-17 + OT 3; LAL 30-29-22-30 + OT 7 | [CHA–LAL summary](https://www.nba.com/game/cha-vs-lal-0022600256) |
| Game count per date | 5 on 11/17 and 12 on 11/18, matching the scoreboards | [games 11/17](https://www.nba.com/games?date=2026-11-17) · [games 11/18](https://www.nba.com/games?date=2026-11-18) |
| Injury revisions, format | 01:30 and 01:45 AM ET each parse to 44 rows of 7 cells; bodies identical | `tests/test_window_2026_11_19.py` · [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| Row-by-row re-read, 01:45 AM PDF against the stored extract | Second fetch of the PDF this cycle. Every printed date, time, matchup, team, player, status and reason cell matches the stored extract for the 37 rows that print them. The 7 three-cell continuation rows print their NOT YET SUBMITTED text with no column header; the extract places it in the status column by position (flag IR-19-05). | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| 11/19 matchups vs the schedule | The four schedule rows for 11/19 are GSW@MEM, POR@MIL, NYK@MIN, LAC@SAS (8:00 PM ET). The report's 11/19-dated blocks match those four. Seven blocks (HOU@DEN, NOP@OKC, PHX@UTA, SAC@LAL, TOR@DET, WAS@CHI, and POR@MIL) have a blank date cell after the page break. Three blocks are dated 11/20 (CHA@ATL, IND@CLE, ORL@BKN). | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) rows 270–273 · [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |

## 4. Flags

| Flag | Irregularity | Owner action | Source |
| --- | --- | --- | --- |
| **BR-S1** | The Upcoming slate page shows the 11/17 read of the schedule (rows 253–273). The 11/19–11/21 window is not re-read. | Re-read the schedule PDF next cycle. | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| **BR-S2** | Standings and the three team-stat pages were not re-read. The team-stats freshness gate fails. | Re-read them next cycle. | [NBA standings](https://www.nba.com/standings) · [NBA team stats](https://www.nba.com/stats/teams/traditional) |
| **BR-S3** | The 01:45 AM report prints 3 blocks dated 11/20 and 7 blocks with blank date cells. None of the blank-date matchups except POR@MIL is in schedule rows 253–273, and their dates are not verified here. | Read the 11/20 schedule rows and re-check the blank-date blocks against the official PDF. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| **BR-G1** | The statsdmz gamebook PDFs returned fetch errors (11/16, 11/17, 11/18). The game-summary LINESCORES table is the source for quarter scores. | Retry the gamebooks from a working path. | [11/17 NYK@TOR gamebook](https://statsdmz.nba.com/pdfs/20261117/20261117_NYKTOR_book.pdf) |
| **BR-J1** | Scheduled `daily-refresh` run 44293154114 failed. The log could not be downloaded from the sandbox (`gh run view --log-failed` returns EOF). This session did not edit the job, which PR #81 owns. | Owner: read the failed step in the Actions UI. | [run 44293154114](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/44293154114) |
| **IR-19-01** | Kuminga, Jonathan and Pullin, Zyon print no date, time, matchup or team cells after the page break. They are attributed by position only. | Keep flagged. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| **IR-19-02** | Six first-listed team rows print no status and no reason (TOR@DET, NOP@OKC, WAS@CHI, PHX@UTA, HOU@DEN, SAC@LAL). Left blank, not copied. | Re-check against the next revision. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| **IR-19-03** | Game times in the injury report print 24-hour values (for example `08:00 (ET)`). The schedule prints `8:00 PM` for the same 11/19 matchups. Kept as printed. | None; format difference only. | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| **IR-19-05** | Seven three-cell continuation rows (Brooklyn, Detroit, Oklahoma City, Chicago, Utah, Denver, Los Angeles Lakers) print NOT YET SUBMITTED with no column header. The extract places it in the status column by position; the column is not printed. | Keep flagged; confirm the column against the next revision. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| **IR-19-04** | Revision gap. The stored 11/17 11:15 AM ET report is followed by an unobserved gap until 11/19 12:00 AM ET. The 12:00–1:15 AM ET revisions were not transcribed, so the only published diff is 1:30 → 1:45 AM. | Read the missing revisions if they are still retrievable. | [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |

## 5. Corrections made before publication

* **Injury extract.** The first draft had three wrong time cells (TOR@DET, WAS@CHI, SAC@LAL) and two wrong pipe counts (Kuminga, Pullin). They were rebuilt from the captured text before any output was built.
* **Injury flags.** The first flag rule over-flagged rows that print NOT YET SUBMITTED. It now fires only when no status and no reason are printed.
* **Results renderer.** The period sum now includes printed overtime. Without that, the OT game would have shown DISAGREES.
* **Time zone.** The 01:45 AM ET revision is 06:45 UTC (New York is UTC−5 in November), not 05:45 UTC as first written.
* **Fetch window.** The files had a precise-looking timestamp (07:04:24Z) that was not logged. It is replaced by the session window 06:59–07:07 UTC.

## 6. Brief items touched by this cycle

| Brief item | This cycle |
| --- | --- |
| Per-game result feed with date, teams, final and quarter scores | Done for 11/17 and 11/18 (17 rows), from the official summary pages. [example](https://www.nba.com/game/nyk-vs-tor-0022600253) |
| Settle only after verified finals | Done. Settlement status is computed per team line. [games 11/18](https://www.nba.com/games?date=2026-11-18) |
| Store every injury PDF with its timestamp and diff consecutive reports | Partly. 01:30 and 01:45 AM are stored and diffed. The 12:00–1:15 AM revisions are a gap (IR-19-04). [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| Injury revision and retrieval time shown in the banner | Done. Revision 01:45 AM ET; retrieved in the session window. [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Official schedule, standings and team stats refreshed for each rolling slate | Not done this cycle (BR-S1, BR-S2). [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Picks, lines, prices, parlays, prop combinations, leaderboard rewards | **Not done.** Refused by rights gate G0. No pick or price is published. [NBA Terms of Use](https://www.nba.com/termsofuse) |

## 7. Not done, and why

The betting-facing parts of the 2026-11-19 brief (originated lines, picks, parlay and prop pricing, the leaderboard with rewards, the bet surface) remain gated. The repository's standing decision is that NBA statistics and derived model values are not published for gambling use without written permission (see [docs/sources.md](sources.md) and [questions.html](../questions.html)). This cycle keeps that position.
