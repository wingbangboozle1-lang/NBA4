# Verification pass 13 — eleventh daily refresh cycle (2026-11-19)

Session `arena/76f88812-nba4` · board task **BS** (re-lettered from BR; see [COORDINATION.md](../COORDINATION.md)) · branch `arena/76f88812-nba4`.

Every fetch in this cycle ran between **06:59 and 07:07 UTC on 2026-11-19**. Per-document times were not logged, so the files carry that window, not a precise time. This pass produces no line, price, probability, pick, bet, parlay, prop combination or leaderboard entry. Rights gate G0 and decision D-01 still stand.

## 1. Status of each feed

| Feed | Status | Evidence |
| --- | --- | --- |
| Per-game results, 2026-11-17 (5 games) and 2026-11-18 (12 games) | **Refreshed and settled**: 17 of 17 games, 34 of 34 team lines | [games 11/17](https://www.nba.com/games?date=2026-11-17) · [games 11/18](https://www.nba.com/games?date=2026-11-18) · `data/snapshots/results-2026-11-17.json` · `results-2026-11-18.json` |
| Injury report, newest revision 01:45 AM ET, 11/19 (44 rows) | **File of record is PR #84** (`injuries-2026-11-19-0145am.json`, session `639c095c`). This session re-read the PDF and compared every row. It did not overwrite that file. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) · `data/snapshots/raw/injury-2026-11-19T0145am-et.pipes` |
| Injury report, 01:30 AM ET, 11/19 (44 rows) | **Stored here as a raw extract** | [01:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_30AM.pdf) · `data/snapshots/raw/injury-2026-11-19T0130am-et.pipes` |
| Consecutive revision diff, 01:30 → 01:45 AM ET | **Computed**: 0 status, 0 reason, 0 team changes | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) · `data/snapshots/injuries-2026-11-19-0130-to-0145.diff.json` |
| Schedule, 11/19–11/21 (rows 270–273, 43–51, 274–279) | **Transcribed** as raw rows. The Upcoming slate page is not regenerated from them (BR-S1). | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) · `data/snapshots/raw/schedule-2026-11-20-11-21-rows-43-51-274-279.txt` |
| Standings | **Not re-read** (BR-S2) | [NBA standings](https://www.nba.com/standings) |
| Official team statistics (traditional, opponent, advanced) | **Not re-read** (BR-S2) | [NBA team stats](https://www.nba.com/stats/teams/traditional) |
| Scheduled `daily-refresh` job | **Latest scheduled run failed** (BR-J1) | [Workflow run 44293154114](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/44293154114) |

## 2. Fetch log

| Document | Result | Source |
| --- | --- | --- |
| Games page, 11/18 | 12 Final rows, game ids 0022600258–0022600269 | [nba.com/games?date=2026-11-18](https://www.nba.com/games?date=2026-11-18) |
| Games page, 11/17 | 5 Final rows, game ids 0022600253–0022600257 | [nba.com/games?date=2026-11-17](https://www.nba.com/games?date=2026-11-17) |
| Game summary pages, 17 finals (LINESCORES and GAME INFO) | 17 of 17 read; quarter sums checked against finals | e.g. [NYK–TOR 0022600253](https://www.nba.com/game/nyk-vs-tor-0022600253) |
| Gamebook PDFs for 11/16 ORL@BOS, 11/17 NYK@TOR, 11/18 MEM@CLE | **Fetch error on all three** (BR-G1) | e.g. [11/17 NYK@TOR gamebook](https://statsdmz.nba.com/pdfs/20261117/20261117_NYKTOR_book.pdf) |
| Injury-report index, 11/19 entries | 12:00 a.m. to 1:45 a.m. ET listed; no 11/18 entries transcribed | [official.nba.com injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Injury PDF, 01:30 AM ET, 11/19 | 44 rows, single chunk | [01:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_30AM.pdf) |
| Injury PDF, 01:45 AM ET, 11/19 (second read this cycle) | 44 rows, single chunk, compared with the stored extract and with file of record | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| Schedule PDF, chunk 2 (rows 245–311) | Rows 43–51 (11/20), 274–279 (11/21) transcribed verbatim | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |

## 3. Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Settlement rule: regulation periods plus printed OT equal the printed Final; scoreboard Final equals linescore Final | 11/17: 10 of 10 lines agree. 11/18: 24 of 24 agree. All 17 games agree. | `build_window_2026_11_19.py --check` · [games 11/17](https://www.nba.com/games?date=2026-11-17) |
| Overtime, CHA 114 @ LAL 118 (0022600256) | One OT: CHA 34-32-28-17 + OT 3; LAL 30-29-22-30 + OT 7 | [CHA–LAL summary](https://www.nba.com/game/cha-vs-lal-0022600256) |
| Game count per date | 5 on 11/17 and 12 on 11/18, matching the scoreboards | [games 11/17](https://www.nba.com/games?date=2026-11-17) · [games 11/18](https://www.nba.com/games?date=2026-11-18) |
| Row-by-row, 01:45 AM PDF against the stored extract and the file of record | All 44 rows compared on every printed date, time, matchup, team, player, status and reason. Two differences in *attribution*, not in printed text: Kuminga and Pullin are unattributed in the file of record (flag IR-19-01), and seven three-cell rows place NOT YET SUBMITTED in the reason cell (IR-19-05). Both files now use the same placement. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) · `tests/test_window_2026_11_19.py` |
| 01:30 vs 01:45 raw extracts | Bodies identical (44 rows, 7 cells each) | [01:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_30AM.pdf) · [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) · `tests/test_window_2026_11_19.py` |
| 11/20 matchups against the schedule | The report's nine 11/20 blocks equal schedule GAME 43–51: CHA@ATL, ORL@BKN, IND@CLE, TOR@DET, WAS@CHI, NOP@OKC, PHX@UTA, HOU@DEN, SAC@LAL. Seven of those blocks print no date cell after the page break; their date is the schedule's, not the report's. | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) rows 43–51 · [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| 11/19 matchups against the schedule | Schedule GAME 270–273: GSW@MEM, POR@MIL, NYK@MIN, LAC@SAS (8:00 PM ET local 7:00 PM). The report's 11/19 blocks match these four. | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |

## 4. Corrections made in this pass

* **Injury extract.** The first draft had three wrong time cells and two wrong pipe counts. They were rebuilt from explicit tuples and re-checked against the PDF.
* **Injury file of record.** My first build wrote its own `injuries-2026-11-19-0145am.json` and pointer. Main already carried the same names from PR #84, so this session stopped writing them and reads that file instead. Nothing was overwritten.
* **Schedule claim.** An earlier draft of this log said three 11/20 blocks existed and that the other nine were unverified. The schedule shows nine 11/20 games at GAME 43–51. The earlier claim was wrong and is removed.
* **Overtime.** The period sum includes printed overtime. Without it, the CHA–LAL game would have shown DISAGREES.
* **Time zone.** The 01:45 AM ET revision is 06:45 UTC (New York is UTC−5 in November), not 05:45 UTC as first written.
* **Fetch window.** A precise-looking timestamp (07:04:24Z) was not logged. It is replaced by the session window 06:59–07:07 UTC.

## 5. Flags (open, for review)

| Flag | Irregularity | Owner action | Source |
| --- | --- | --- | --- |
| **BR-S1** | The Upcoming slate page still shows the 17 Nov read. The 11/19–11/21 rows are transcribed (raw file only) but the page has not been regenerated from them. | Regenerate the slate page from the raw rows in the integration step. | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| **BR-S2** | Standings and the three team-stat pages were not re-read. The team-stats freshness gate fails. | Re-read them next cycle. | [NBA standings](https://www.nba.com/standings) · [NBA team stats](https://www.nba.com/stats/teams/traditional) |
| **BR-S3** | The seven 11/20 blocks with a blank date cell after the page break are dated only by the schedule (GAME 43–51), not by the report itself. | Keep as shown; the date is attributed, not printed. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| **BR-G1** | The statsdmz gamebook PDFs returned fetch errors (11/16, 11/17, 11/18). The game-summary LINESCORES table is the source for quarter scores. | Retry the gamebooks from a working path. | [11/17 NYK@TOR gamebook](https://statsdmz.nba.com/pdfs/20261117/20261117_NYKTOR_book.pdf) |
| **BR-J1** | Scheduled `daily-refresh` run 44293154114 failed. The log could not be downloaded from the sandbox (`gh run view --log-failed` returns EOF). This session did not edit the job, which PR #81 owns. | Owner: read the failed step in the Actions UI. | [run 44293154114](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/44293154114) |
| **IR-19-01** | Kuminga, Jonathan and Pullin, Zyon print no date, time, matchup or team cells after the page break. The file of record lists them as unattributed rows; the raw extract keeps them in position. | Keep unattributed. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| **IR-19-02** | Six first-listed team rows print no status and no reason (TOR@DET, NOP@OKC, WAS@CHI, PHX@UTA, HOU@DEN, SAC@LAL). Left blank, not copied. | Re-check against the next revision. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| **IR-19-03** | Game times in the injury report print 24-hour values (for example `08:00 (ET)`). The schedule prints `8:00 PM` for the same 11/19 matchups. Kept as printed. | None; format difference only. | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| **IR-19-04** | Revision gap. The stored 11/17 11:15 AM ET report is followed by an unobserved gap until 11/19 12:00 AM ET. The 12:00–1:15 AM ET revisions were not transcribed, so the only published diff is 1:30 → 1:45 AM. | Read the missing revisions if they are still retrievable. | [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| **IR-19-05** | Seven three-cell continuation rows (Brooklyn, Detroit, Oklahoma City, Chicago, Utah, Denver, Los Angeles Lakers) print NOT YET SUBMITTED with no column header. Both files place it in the reason cell. The printed column is not shown. | Confirm the column against the next revision. | [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |

## 6. Brief items touched by this cycle

| Brief item | This cycle |
| --- | --- |
| Per-game result feed with date, teams, final and quarter scores | Done for 11/17 and 11/18 (17 rows), from the official summary pages. [example](https://www.nba.com/game/nyk-vs-tor-0022600253) |
| Settle only after verified finals | Done. Settlement status is computed per team line. [games 11/18](https://www.nba.com/games?date=2026-11-18) |
| Store every injury PDF with its timestamp and diff consecutive reports | Partly. 01:30 and 01:45 AM are stored and diffed here; the file of record for 01:45 is PR #84's. The 12:00–1:15 AM revisions are a gap (IR-19-04). [01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| Injury revision and retrieval time in the banner | Done. Revision 01:45 AM ET; retrieved in the session window. [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Official schedule, standings and team stats refreshed for each rolling slate | Schedule rows for 11/19–11/21 transcribed (BR-S1). Standings and team stats not re-read (BR-S2). [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Picks, lines, prices, parlays, prop combinations, leaderboard rewards | **Not done.** Refused by rights gate G0. No pick or price is published. [NBA Terms of Use](https://www.nba.com/termsofuse) |

## 7. Not done, and why

The betting-facing parts of the 2026-11-19 brief (originated lines, picks, parlay and prop pricing, the leaderboard with rewards, the bet surface) remain gated. The repository's standing decision is that NBA statistics and derived model values are not published for gambling use without written permission. This cycle keeps that position. [NBA Terms of Use](https://www.nba.com/termsofuse)
