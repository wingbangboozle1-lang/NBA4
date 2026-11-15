# Verification pass 8 — sixth daily refresh cycle (session `arena/aea8c363-nba4`, 2026-11-15)

Board task **AO** (originally claimed as AN at 2026-11-15T11:32Z before any work; re-lettered AO on rebase after session `arena/37a389fa-nba4` had merged its own AN task in PRs #47/#48 — both preserved), on branch `arena/aea8c363-nba4` (base `24d7adf`, the PR #46 merge). Observation time for the refresh window: **2026-11-15T11:29:57Z**.

## 1. What this cycle did

1. Re-read the official sources listed in §2 on 2026-11-15 and quote-checked the sentences the repository relies on.
2. Re-cut the three-day observation window from the new observation time: **2026-11-15T11:29:57Z → 2026-11-18T11:29:57Z** = schedule rows **236–257** (9 games on 11/15, 8 on 11/16, 5 on 11/17). Published as `data/snapshots/slate-2026-11-15.json` and rendered on `slate.html`.
3. Fully transcribed the current newest official injury report — **Injury Report: 11/15/26 06:15 AM ET** — row by row (100 rows: 84 player/status rows across 9 games on 11/15, plus 16 `NOT YET SUBMITTED` rows for the 8 games of 11/16). Published as `data/snapshots/injuries-2026-11-15-0615am.json` and rendered on `injuries.html`. This resolves flag P7-01 for the current report.
4. Recorded the index check in `data/snapshots/injuries-newest-pointer-2026-11-15.json` (metadata only).
5. Found and fixed a date-blind matchup-corroboration defect (P8-10) before publishing anything: `scripts/build_snapshots.py` now corroborates away/home order on **(game date, matchup code)** pairs, not codes alone.
6. Refreshed the Injuries banner with the report's **revision time** (11/15/26 06:15 AM ET, per the document header) and the **retrieval time** (2026-11-15 11:33–11:34 UTC), per the project requirement.
7. Added an "Official results feed & settlement" status row to `slate.html` documenting that the 11/14 games are past their tips but no score, result or settlement row exists anywhere (rights decision D-01/IR-T4 still open; P8-05).
8. Kept the 2026-11-14 snapshot files as dated historical snapshots, covered by their own tests.

No engine code, no odds, no probabilities, no picks and no NBA statistics values were added or changed. Every generated table is re-derived from the provenance JSONs by `scripts/build_snapshots.py`.

## 2. Sources re-read on 2026-11-15 (method: web-fetch page/PDF text extraction, same as all prior passes)

| # | Source | Verified statement (as read this cycle) | URL |
| --- | --- | --- | --- |
| S1 | NBA injury-report index | "November 15:" entries list reports every 15 minutes from "12:00 a.m ET report" through "6:15 a.m ET report"; the 6:15 a.m. ET report was the newest listed at the 11:31 UTC check (6:31 a.m. ET). Policy text on the same page: teams must report by 5 p.m. local the day before a game (1 p.m. game day for the second of a back-to-back) and submit a game-day report between 11 a.m. and 1 p.m. local (8–10 a.m. for tip-offs 5 p.m. or earlier); "Reports are updated on a continual basis throughout the day." | [NBA injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| S2 | Injury report PDF, 11/15/26 06:15 AM | Header "Injury Report: 11/15/26 06:15 AM"; columns Game Date / Game Time / Matchup / Team / Player Name / Current Status / Reason; 9 games on 11/15/2026 (IND@PHI 01:00, LAL@PHX 04:00, CHA@LAC 04:30, SAS@UTA 05:00, DAL@BOS 06:00, NYK@TOR 06:00, HOU@WAS 07:00, ATL@MIL 08:00, OKC@SAC 09:00 ET) and 16 NOT YET SUBMITTED rows for 8 games on 11/16/2026. All 100 published rows transcribed from this document. | [Injury report PDF 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| S3 | 2026–27 schedule PDF | Header "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE" re-read on the fresh fetch; column header "GAME \| DAY \| DATE \| TEAM 1 \| TEAM 2 \| LOCAL \| ET \| NAT TV \| R \| #". Rows 236–257 read verbatim (chunk 1: rows 236–245; chunk 2: rows 246–257); rows 258–269 (11/18) confirmed out-of-window. The extracted text prints no "at" token on rows 215–259 while rows 260+ print "at" (re-confirms P7-02). | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| S4 | NBA.com Terms of Use, §9 | Re-read successfully this cycle (passes 6/6b recorded HTTP 502; pass 7 re-read §§9(ii)/9(iv)). Clause (iv): NBA Statistics "may not be used in connection with any gambling activity (including legal gambling activity)". Clause (vii): no use "in connection with any website, product, or service that features a database (in any medium or format) of comprehensive, regularly updated statistics from NBA, WNBA or G-League games, competitions, or events without the Operator's express prior consent." | [NBA.com Terms of Use](https://www.nba.com/termsofuse) |

Cross-checks performed (all against S2 + S3):

- The report's 9 AWAY@HOME codes for 11/15 and 8 codes for 11/16 match schedule rows 236–252 one-for-one.
- The report's Game Time equals the schedule's ET column on all 17 corroborated rows (meridiem from the schedule, documented as inferred).
- LOCAL|ET consistency: for all 22 window rows the ET value equals the home venue's local time converted to ET (venue time zones, a consistency check, not a document statement).
- 11/15 games in the report = the 9 games the schedule lists for 11/15; 11/16 NOT YET SUBMITTED games = the 8 games the schedule lists for 11/16.

## 3. Irregularities found (published on review.html, section "Verification pass 8")

| Flag | Severity | Finding | Action | Source |
| --- | --- | --- | --- | --- |
| P8-01 | Medium | 13 player rows lost their team cell at PDF page breaks (2 LAL@PHX, 5 SAS@UTA, 3 HOU@WAS, 2 ATL@MIL, 1 OKC@SAC). | Published with blank team cell + unverified flag; team never inferred from context. | [injury PDF 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| P8-02 | Low | Extracted text prints "Embid, Joel" (Philadelphia 76ers). PDF-vs-extractor spelling cannot be distinguished from extracted text. | Transcribed verbatim; flagged for manual PDF review. | [injury PDF 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| P8-03 | Low | Sorber reason cell spans a page boundary ("Injury/Illness - " + "Right Knee Surgery"). | Fragments joined verbatim; row flagged unverified with the join documented. | [injury PDF 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| P8-04 | Low | Rows 253–257 (11/17) print no "at" and have no corroborating injury code yet. | Published as printed order with "(order unverified)". | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| P8-05 | High | Results-feed/settlement requirement for the now-completed 11/14 games remains blocked by the open rights decision (D-01/IR-T4). | No scores stored; status row added to slate.html; owner decision unchanged. | [NBA.com Terms of Use](https://www.nba.com/termsofuse) |
| P8-06 | Low | NYK@TOR lists only Raptors rows; no Knicks rows and no NOT YET SUBMITTED marker for New York in the extracted text. | Recorded as observed; nothing inferred. | [injury PDF 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| P8-07 | Info | P7-01 resolved for the current report (full transcription); the historical 11/14 05:00 PM rows remain untranscribed. | Banner/pointer updated; stale history stays flagged, not transcribed. | [NBA injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| P8-08 | Info | NBA Terms §9 re-read succeeded this cycle (prior 502s closed). | Recorded; §9 gate unchanged. | [NBA.com Terms of Use](https://www.nba.com/termsofuse) |
| P8-09 | Info | Report cadence at retrieval: index listed 11/15 reports every 15 minutes through 6:15 a.m. ET; game-day reports still to come. | Snapshot labelled with revision + retrieval times; supersession expected. | [NBA injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| P8-10 | Medium | Date-blind matchup corroboration: codes repeat across dates (NYK@TOR, POR@MIN in the 11/15 report and again as 11/17 slate rows), so a code-only check falsely corroborated rows 253/254. | Fixed to (date, code) matching before publication; regression tests assert corroborated rows are exactly 236–252. | [scripts/build_snapshots.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/build_snapshots.py) |

## 4. Checks run on the final tree

- `python3 -m unittest discover -s tests -t .` → **107 tests, all passing** (47 + 43 + 17; the snapshot suite grew from 13 to 17 tests and now covers both the current and historical snapshots).
- `python3 scripts/build_snapshots.py --check` → in sync (pages re-generated from the new provenance files first).
- `python3 scripts/check_site.py --with-tests` → PASS with the updated counts (README "107 passing unit tests (47 + 43 + 17)", index.html "107 unit tests").
- No page shows an away/home "at" that is not corroborated by (date, code) from an official document; 17 rows corroborated, 5 rows flagged unverified order.

## 5. Scope notes

- The 2026-11-14 snapshot files are kept unchanged as historical provenance (their own tests keep them honest); only the render targets and page prose moved to the 2026-11-15 snapshot.
- No engine module was modified. The pipeline's rights gate (G0) is untouched; no forecast, pick, line, price, probability or score exists anywhere in the repository.
