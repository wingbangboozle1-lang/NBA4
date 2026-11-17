# Verification pass 10: tenth daily refresh cycle, 2026-11-17

Session `arena/4326c586-nba4`, board task **BM** ([COORDINATION.md](../COORDINATION.md)). Claimed on 2026-11-17 before any data work and pushed with the claim.

## 1. Scope and what was done

| Item | Result | Source for the item |
| --- | --- | --- |
| Rolling window re-read: official 2026–27 schedule, rows 253–273 (11/17–11/19) | Read, transcribed verbatim to `data/snapshots/raw/schedule-2026-11-17-window-rows-253-273.txt`, generated to `data/snapshots/slate-2026-11-17.json` (21 games) | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Newest injury report: 11/17 10:30 AM ET (index read at about 15:42 UTC; newest listed) | Read, transcribed verbatim to `raw/injury-2026-11-17T1030am-et.pipes`, generated to `data/snapshots/injuries-2026-11-17-1030am.json` (58 attributed rows in 17 games, 1 unattributed) | [Injury report PDF, 11/17 10:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf); [injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Site slate and injury tables | Regenerated from the 11/17 files by `scripts/build_snapshots.py` (`--check` clean after the build) | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf); [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Hand-written banners, status rows and counts on `slate.html`, `injuries.html`, `index.html` | Updated to the 11/17 facts listed in §3 | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf); [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Consecutive-revision diff for 11/17 | **Not done.** Only the 10:30 AM report was transcribed; the 10:15 AM and earlier 11/17 reports are not in the repository (BM-07) | [injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Games-page corroboration for rows 253–273 | **Not done in this cycle** (BM-06). No games-page value is shown for any 11/17–11/19 row | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Standings and the three team-stat pages (traditional, opponent, advanced) | **Not refreshed in this cycle** (BM-08). Repository copies stay dated 11/16 | [NBA.com standings](https://www.nba.com/standings); [traditional](https://www.nba.com/stats/teams/traditional); [opponent](https://www.nba.com/stats/teams/opponent); [advanced](https://www.nba.com/stats/teams/advanced) |

Method. The sandbox's shell cannot reach `nba.com` (its outbound allowlist is GitHub, npm and PyPI only), so every official document was read with the page-fetch tool, which returns PDF text as markdown tables. Times in this log are minute-level, taken from the session clock; they are not second-accurate retrieval stamps.

## 2. Checks performed on the transcription

| Check | Result | Source for the check |
| --- | --- | --- |
| Every raw pipe row has exactly seven cells (`date\|time\|matchup\|team\|player\|status\|reason`) | Pass: 59 data rows in the file (58 attributed to a game, 1 unattributed) | [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Row counts per team against the printed blocks | Pass: NYK@TOR 4 (Toronto only), DET@SAS 11 (Detroit 7, San Antonio 4), POR@MIN 2, UTA@LAC 10 (Utah 6, LA Clippers 4), CHA@LAL 7 (Charlotte 5, Lakers 2), 11/18 games 24 `NOT YET SUBMITTED` lines across 12 games | [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf) |
| Schedule rows 253–273 against the verbatim raw file | Pass (unit test `test_every_slate_row_matches_its_verbatim_raw_line`) | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Each printed AWAY@HOME code matches the same game in the schedule window | Pass: 17 codes printed in the report (rows 253–269) match rows 253–269 one for one; rows 260–273 print the schedule's own `at` token | [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf); [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Printed tip times against the schedule's ET tip | Of 16 games with a printed time: three disagreements (UTA@LAC, CHA@LAL, BOS@DEN) and 13 agreements; GSW@DAL time cell lost (no conflict asserted). The report prints evening times without AM/PM, so `10:30 (ET)` is read as 10:30 PM ET | [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf); [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Site: 487 unit tests, including 6 new window tests | `python3 -m unittest discover -s tests -t .` → 487 OK | Repository tests | [tests folder](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| Site: static checker with tests | `python3 scripts/check_site.py --with-tests` → PASS (16 pages) | Repository checker | [checker script](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |

## 3. Facts stated on the site and where they come from

- **Window:** schedule rows 253–273, dated 11/17, 11/18 and 11/19 (21 games). Observation window 2026-11-17 15:44 UTC to 2026-11-20 15:44 UTC. Source: [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf).
- **Newest report:** the 11/17 10:30 AM ET report, the newest listed on the [injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) at the read time.
- **Order corroboration:** 17 games carry the report's own AWAY@HOME code; 4 games (11/19) carry only the schedule's printed `at` token.
- **Tip conflicts:** UTA@LAC, CHA@LAL and BOS@DEN, both values printed, none chosen.

## 4. Irregularities (full register on [Flagged for Review](../review.html), section pass 10)

BM-01 tip-time conflicts (Medium) · BM-02 unattributed Reaves, Austin row (Medium) · BM-03 Minnesota row attached by printed position (Low) · BM-04 no New York Knicks row for NYK@TOR (Low) · BM-05 dates and times lost at page breaks (Low) · BM-06 games-page corroboration not re-read (Medium) · BM-07 no consecutive diff for 11/17 (Medium) · BM-08 standings and team-stat pages not refreshed (Medium) · BM-09 availability and results pages still show 11/16 as current, outside this claim (High) · BM-10 scheduled refresh gate still fails closed (High) · BM-11 page-break heading not recorded as a row (Low).

Sources for the register: [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf), [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf), [injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/), [NBA.com standings](https://www.nba.com/standings).

## 5. Not in scope, and not claimed

No line, price, probability, pick, parlay, prop or minutes estimate is produced or published. NBA Terms §9 (no use of NBA Statistics in connection with gambling) and the repository's rights gate (G0, D-01, IR-T4) are unchanged. The engine modules (`engine/**`) are not edited.
