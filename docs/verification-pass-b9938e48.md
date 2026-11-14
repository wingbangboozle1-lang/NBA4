# Verification pass 6: line-by-line re-check of the published official observations

**Session:** `arena/b9938e48-nba4` · **Board task:** AG (first written as AF; re-lettered because PR #36 merged task AF first) · **Date:** 14 Nov 2026, read between 10:20 and 10:50 UTC (the 04:30 AM injury snapshot was fetched at 10:20 UTC; `date -u` at the start of the injury comparison read 10:25:56 UTC).

## 1. Scope and method

- **In scope:** the 22 schedule rows the site publishes (rows 231–252), the 49 rows of the 14 Nov 2026 04:30 AM official injury report that the site publishes, the open schedule-column question (Q21), the matchup notation, the NBA Terms §9 gate, the NBA Stats FAQ quotation, and the coordination board.
- **Method:** each official PDF was read through the web-fetch tool (PDF text extraction). Every published row was transcribed into a scratch file and compared field by field with the provenance JSON by script. The scratch files were **not** committed, because they would duplicate the player rows that are already published; the comparison result is recorded here instead.
- **Time-zone check (Q21):** for each window game, the ET column was compared with the home venue's local time converted to Eastern time using the IANA time-zone database. This is an arithmetic consistency check on the printed values, not a statement from the league.
- **Limits:** this pass did not re-fetch every external link on the site. The NBA Terms page could not be read (see row 6 below). Earlier passes (T, W, AB) quote-checked the other primary sources.

## 2. Results

| # | Check | Result | Official source |
| --- | --- | --- | --- |
| 1 | Schedule rows 231–252 (22 games): row, weekday, date, away, home, LOCAL time, ET time | **22 of 22 agree, 0 mismatches.** Dates run 11/14 to 11/16. | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 2 | Schedule header and column header | Header reads "AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE". Column header reads "LOCAL \| ET" (chunk 0 of the PDF text, read this session). | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 3 | Q21: which time column is which | **Answered (consistency-checked):** the ET value equals the home venue's local tip time converted to ET in **22 of 22** rows. The away team's time zone fits **7 of 22**. The first column is therefore home-venue local time and the second is ET. | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 4 | Injury report 14 Nov 2026 04:30 AM: team, player, status and reason, all 49 rows in order | **49 of 49 agree.** The report covers 14 matchups (5 on 11/14 and 9 on 11/15). Of the 49 rows, 23 are "NOT YET SUBMITTED" team-level rows. One player row (Traore, Nolan) lost its team cell at a page break and stays unasserted, as already flagged. | [Injury report PDF, 04:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf) |
| 5 | Latest 14 Nov report on the official index | The index lists 12:00 AM to 4:30 AM ET reports for 14 Nov. The 04:30 AM report is the last one listed at the time of this check. A later report would supersede it. | [NBA injury report index 2026–27](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 6 | NBA Terms of Use §9 (gambling restriction) | **Not re-read. The page returned "502 Bad Gateway" on both attempts.** The §9 gate still governs every output. Flag P6-03. | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| 7 | NBA Stats FAQ: statistics not available for download | Quotation still present: "Our stats are not available for download for either academic or personal use." | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| 8 | Engine duplicate modules (IR-T1) | Still present on `main`. No change in this pass. Flag P6-06. | [Review record eb9d2e0b](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/review-eb9d2e0b.md) |

### 2.1 Time-zone check for the 22 window games

Each home venue was mapped to its IANA zone. After 1 Nov 2026 all US zones are on standard time, and Phoenix has no daylight saving time.

| Home venues in the window (games) | IANA zone used | Games | Result | Source |
| --- | --- | --- | --- | --- |
| New Orleans (2), Memphis (1), Minnesota (2), Milwaukee (1) | America/Chicago | 6 | 6 of 6 agree | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Cleveland (2), Miami (2), Philadelphia (1), Boston (2), Toronto (1), Washington (2), Brooklyn (1) | America/New_York | 11 | 11 of 11 agree | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Utah (1), Denver (1) | America/Denver | 2 | 2 of 2 agree | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Phoenix (1) | America/Phoenix | 1 | 1 of 1 agree | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| LA Clippers (1), Sacramento (1) | America/Los_Angeles | 2 | 2 of 2 agree | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| **Total** |  | **22** | **22 of 22 agree** | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |

Zone rules come from the public IANA time-zone database (a reference, not an NBA source; it is cited here in prose only). Per-game results: 22 of 22 agree. Rejected alternative (away team's zone): 7 of 22.

**Self-caught error.** The first run mapped Milwaukee to Eastern time and reported 21 of 22. Milwaukee is on Central time, so the mapping was corrected and the re-run gave 22 of 22. The mapping above is the corrected one.

## 3. Changes made in this pass

| File | Change | Reason | Source |
| --- | --- | --- | --- |
| `scripts/build_snapshots.py` | Column headers relabelled: "Tip-off: home-venue local / ET (PDF header LOCAL \| ET)" and "Date (as printed)". | The old header said "schedule columns 1 / 2". The old date header asserted an ET time zone that the PDF does not state. | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `slate.html` (generated table block only) | Regenerated by `scripts/build_snapshots.py`. | Follows the header change. `--check` reports the tables in sync. | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `slate.html` (note paragraph) | The 11/17 matchups are listed in printed order, with no "@" and no away/home assertion. | The PDF prints no "at" on those rows. | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `data/snapshots/slate-2026-11-14.json` (`extraction_notes` only) | The two notes now record the LOCAL \| ET header, the 22 of 22 check, and printed-order 11/17 times. | The old note said the header was not reproduced. | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `questions.html`, `docs/decision-register.md` (Q21) | Q21 changed from "Unverified" to "Answered (consistency-checked)". | Sections 2 and 2.1. | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `review.html` | New section "Verification pass 6" with flags P6-01 to P6-07. | Publishes the flags for review. | [Pass log](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/verification-pass-b9938e48.md) |
| `index.html` (hero paragraph closing tag) | Added the missing `</p>`. | Flag P6-09. | [Landing page](https://github.com/wingbangboozle1-lang/NBA4/blob/main/index.html) |
| `review.html` (V4-09 cell only) | Raw `<id>`/`<task>` escaped so the sentence renders in full. | Flag P6-08. | [Review page](https://github.com/wingbangboozle1-lang/NBA4/blob/main/review.html) |
| `scripts/check_site.py` | New nesting audit on every page (stack check; void elements excluded). | Prevents the P6-08 and P6-09 class of error from returning. | [Checker](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| `COORDINATION.md` | Task AG claimed and recorded. Row AA was already done on `main` (PR #28, PR #36); not changed here. | Board hygiene. | [Board](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md) |

**No model output, line, probability, pick or player-level value was added or changed.** The injury rows and the 22 slate rows are unchanged.

## 4. Irregularities for review

| ID | Severity | Finding | Status | Source |
| --- | --- | --- | --- | --- |
| P6-01 | Low | The schedule column header was described as missing. It is present in the PDF text. | Closed by Q21 answer | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| P6-02 | Low | 11/17 matchups were given with "@" although the PDF prints no "at" on those rows. Printed rows 215–230 and 253–259 also lack "at". None is in the published window. | Corrected for 11/17. The rest are out of window and unused. | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| P6-03 | Medium | NBA Terms of Use returned 502 on both attempts, so §9 was not re-read today. | Open. Re-read before the next publication change. | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| P6-04 | Low | "Date (ET)" asserted a time zone the schedule PDF does not state. | Relabelled "Date (as printed)". | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| P6-05 | Low | Board row AA showed "in progress" in the copy this session started from, although its audit was on `main`. | `main` already shows AA as done (PR #28 and PR #36). No further change. | [Release audit](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/release-audit-607c89a8.md) |
| P6-06 | Medium | Duplicate engine modules (IR-T1) are still on `main`. | Open. Owner decision needed. | [Review record eb9d2e0b](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/review-eb9d2e0b.md) |
| P6-07 | Info | Re-comparison: 22 of 22 schedule rows and 49 of 49 injury rows agree with the official PDFs. | Result only. | [Injury report PDF, 04:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf) |
| P6-08 | Low | Page rendering: the pass-4 row V4-09 on `review.html` contained raw `<id>` and `<task>`, which the browser read as tags, so part of the sentence was lost. The page also failed a nesting check there. | Fixed by escaping (`&lt;id&gt;`, `&lt;task&gt;`). | [Review page](https://github.com/wingbangboozle1-lang/NBA4/blob/main/review.html) |
| P6-09 | Low | Markup: the landing-page hero paragraph (`index.html`) was not closed before the button group. Browsers recover, but the nesting is invalid. | Fixed (closing tag added). A nesting audit was added to `scripts/check_site.py`; a negative test (removing the tag) makes it exit 1. | [Landing page](https://github.com/wingbangboozle1-lang/NBA4/blob/main/index.html) |

## 5. Requirement coverage (what the site can and cannot support today)

| Requirement | Where it lives | Status | Blocker | Source |
| --- | --- | --- | --- | --- |
| Originated lines and fair prices | [line-origination.html](https://wingbangboozle1-lang.github.io/NBA4/line-origination.html) | Mechanics only (synthetic fixtures) | No rights-cleared input or market quote; no fitted model | [NBA Terms of Use §9](https://www.nba.com/termsofuse) |
| Picks for each slate up to 3 days ahead | [slate.html](https://wingbangboozle1-lang.github.io/NBA4/slate.html) | Every game is NO PICK with reason codes | Rights gate (G0), no licensed market quote | [NBA Terms of Use §9](https://www.nba.com/termsofuse) |
| Single bets, parlays, prop combos and their validation | [strategies.html](https://wingbangboozle1-lang.github.io/NBA4/strategies.html) | Gates defined, no strategy trained | No licensed settled history | [Release audit](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/release-audit-607c89a8.md) |
| Correlation values | [leaderboard.html](https://wingbangboozle1-lang.github.io/NBA4/leaderboard.html) | Blank and flagged | No settled legs | [Release audit](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/release-audit-607c89a8.md) |
| Injury effects on rotation minutes and production | [injuries.html](https://wingbangboozle1-lang.github.io/NBA4/injuries.html) | Official status rows published; effects blank | No licensed minutes or production history; the NBA Stats FAQ says its stats are not available for download | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| Game-flow analysis | [injuries.html](https://wingbangboozle1-lang.github.io/NBA4/injuries.html) | Blank | No licensed game data | [NBA Terms of Use §9](https://www.nba.com/termsofuse) |
| Executive summary, questions and suggestions | [index.html](https://wingbangboozle1-lang.github.io/NBA4/), [questions.html](https://wingbangboozle1-lang.github.io/NBA4/questions.html), [suggestions.html](https://wingbangboozle1-lang.github.io/NBA4/suggestions.html) | Built; Q21 answered in this pass | Owner decisions still open | [Decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Flagged for Review page with source links | [review.html](https://wingbangboozle1-lang.github.io/NBA4/review.html) | Built; pass 6 added | None | [Review page](https://github.com/wingbangboozle1-lang/NBA4/blob/main/review.html) |

## 6. Checks run on the changed tree

- `python3 scripts/build_snapshots.py --check` (in sync) and `python3 scripts/check_site.py --with-tests` (the result is recorded in the board row AF).
- `python3 -m unittest discover -s tests -t .` (101 tests on synthetic fixtures).
- The live GitHub Pages result is recorded in the board row AG after the merge.
