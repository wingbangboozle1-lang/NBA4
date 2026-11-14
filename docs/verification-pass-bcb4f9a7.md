# Verification pass 7 — session `arena/bcb4f9a7-nba4` (task AM)

**Date (UTC):** 2026-11-14, checks run between 22:07 and 22:12 UTC.
**Branch:** `arena/bcb4f9a7-nba4`, branched from `main` at `71482766` (PR #44 merge).
**Scope:** line-by-line re-read of the official sources behind every published table, the newest official injury report, the away/home basis of the slate rows, the rights gate, and the cited GitHub Pages limits. Owned files: `COORDINATION.md`, this file, `review.html`, `injuries.html`, `slate.html`, `scripts/build_snapshots.py`, `tests/test_snapshots.py`, `data/snapshots/*` (listed in the board row), `README.md`, `index.html` (count only), `docs/engine.md` (count only).

**Method.** The sandbox allows outbound HTTPS only to GitHub and package hosts, so every official NBA page was read with the web-fetch tool, not `curl`. Each statement below was checked against the text returned by the tool in this session. Long documents were read in the chunks that contain the cited text, and the chunks are named.

## 1. Results

| Check | Result | Source |
| --- | --- | --- |
| Newest 11/14 injury report listed on the official index | **5:00 PM ET** is the last 11/14 entry at 22:09 UTC. The site's table is the 04:30 AM report. The index lists entries from 12:00 a.m. to 5:00 p.m. ET. | [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 04:30 AM report, all 49 rows | Re-read cell by cell. All 49 rows match the published snapshot. Lost cells stay blank (Traore, Nolan team; Cleveland, Memphis and the other NOT YET SUBMITTED entries). | [Injury PDF 04:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf) |
| 5:00 PM ET report | Read (both chunks). Not transcribed: the PDF repeats matchup, time and team cells only on some rows and loses them at page breaks. A verified row-level snapshot needs per-row repair. Flag **P7-01**. | [Injury PDF 5:00 PM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_05_00PM.pdf) |
| Schedule rows 231–296 | Read (chunks 1–2). Header unchanged: "AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE". The published values agree with the printed values in the rows read. | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| "at" token on schedule rows | **Rows 215–259 print no "at" token** in the extracted text; rows 260 onward print it. Flag **P7-02** (corrects P6-02). | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| NBA Terms of Use §9 | **Loaded this session** (pass 6 had a 502). §9(ii) and §9(iv) re-quoted. Closes P6-03. | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| NBA Stats FAQ | Quote confirmed. | [Stats FAQ](https://www.nba.com/stats/help/faq) |
| GitHub Pages limits | Quote confirmed (below). | [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |

## 2. Verbatim quotations used in this pass

- **Injury policy (index page).** "By 5 p.m. local time the day before a game (other than the second day of a back-to-back), teams must designate a participation status…" and "Reports are updated on a continual basis throughout the day." Source: [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/).
- **Terms §1.** "No Basketball Content from the Services may be reproduced, republished, uploaded, posted, modified, reused, transmitted, reproduced, distributed, copied, publicly displayed, linked to, or otherwise used except as provided in these Terms of Use without the written permission of the Operator." Source: [NBA Terms of Use](https://www.nba.com/termsofuse), chunk 0.
- **Terms §9(ii).** NBA Statistics "may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes". Source: [NBA Terms of Use](https://www.nba.com/termsofuse), chunk 3.
- **Terms §9(iv).** NBA Statistics "may not be used in connection with any gambling activity (including legal gambling activity)". Source: [NBA Terms of Use](https://www.nba.com/termsofuse), chunk 4.
- **Stats FAQ.** "Our stats are not available for download for either academic or personal use." Source: [Stats FAQ](https://www.nba.com/stats/help/faq).
- **Pages limits.** "GitHub Pages sites have a _soft_ limit of 10 builds per hour. This limit does not apply if you build and publish your site with a custom GitHub Actions workflow." Source: [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

## 3. Flags raised in this pass (also on the Flagged for Review page)

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| P7-01 | High | The published injury table is the 04:30 AM report. The 5:00 PM report is newer. Example: New Orleans Pelicans are "NOT YET SUBMITTED" at 04:30 AM and have eight rows at 5:00 PM. | Banner, topbar note and pointer row added; pointer metadata saved. Row transcription is open. Source: [5:00 PM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_05_00PM.pdf). |
| P7-02 | Medium | Rows 215–259 print no "at" token. All 22 window games are in that range. The site showed "at" for all 22. The 04:30 AM injury report prints the same AWAY@HOME code for 14 window games (rows 231–244), which supports "at". The 8 games of 11/16 (rows 245–252) have no second source. P6-02 said the window was unaffected; that was wrong. | The renderer now shows "at" only where the injury report prints the same code. The other 8 rows show printed order, "(order unverified)" and a flag. Regression tests added (14 and 8). Open: check the printed "at" visually in the PDF; it may be a text-extraction artefact. Source: [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf). |
| P7-03 | Closed | NBA Terms re-read succeeded; closes P6-03. | The gate still governs every output (no picks, no lines). Source: [NBA Terms of Use](https://www.nba.com/termsofuse). |
| P7-04 | Info | 04:30 AM report re-compared: 49 of 49 rows agree. | No value changed. Source: [Injury PDF 04:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf). |
| P7-05 | Info | Stats FAQ and schedule header re-read; both match the citations. | No change. Source: [Stats FAQ](https://www.nba.com/stats/help/faq). |
| P7-06 | Low | Board rows AJ and AK had no status. | Completed with references to PR #39 and `docs/verification-pass-c4d167da.md`. Source: [COORDINATION.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md). |
| P7-07 | Low | Unit-test count drift after the new tests (101 → 103). | Counts corrected in README, landing page and `docs/engine.md`. The checker enforces the landing-page count. Source: [tests/test_snapshots.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_snapshots.py). |
| P7-08 | Info | GitHub's soft limit of 10 Pages builds per hour does not apply to a custom Actions workflow. | Owner decision, not changed. Source: [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits). |
| P7-09 | Medium | Engine duplicates (IR-T1, carried from P6-06) are still open. | Not changed; owner decision. Source: [review record eb9d2e0b](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/review-eb9d2e0b.md). |

## 4. Requirements coverage (project brief → repository artefact)

| Brief item | Where it lives | State |
| --- | --- | --- |
| Originate NBA lines | [`engine/lineorigination.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py), [line-origination.html](https://wingbangboozle1-lang.github.io/NBA4/line-origination.html) | Code exists; synthetic fixtures only. No NBA line is published. Blocked by the rights gate (Terms §9(iv)). |
| Singles, parlays, prop combos | [`engine/parlay.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py), [strategies.html](https://wingbangboozle1-lang.github.io/NBA4/strategies.html) | Method documented; no validated strategy. |
| Validation gates | [`engine/gates.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/gates.py), [validation plan](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/validation-plan.md) | G0–G12 defined; no strategy has passed. |
| Correlation values | [`engine/corrstats.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/corrstats.py), [leaderboard.html](https://wingbangboozle1-lang.github.io/NBA4/leaderboard.html) | No correlation value is published; none is computed from licensed data. |
| Leaderboard and rewards | [`engine/leaderboard.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/leaderboard.py), [docs/leaderboard.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/leaderboard.md) | Design only. Reward legality needs legal review. |
| Picks for every slate, up to 3 days ahead | [`engine/picks.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/picks.py), [slate.html](https://wingbangboozle1-lang.github.io/NBA4/slate.html) | All 22 window games show NO PICK with reason codes. Not possible while §9(iv) applies. |
| Injuries, rotation minutes, production | [injuries.html](https://wingbangboozle1-lang.github.io/NBA4/injuries.html), [`engine/injuries.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injuries.py) | Official status rows only. Minutes and production are blank. The table is stale (P7-01). |
| Game-flow analysis | [`engine/gameflow.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/gameflow.py) | Not estimated. No calibrated model. |
| Executive summary | [index.html](https://wingbangboozle1-lang.github.io/NBA4/), [docs/decision-register.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) | Present. |
| Questions and missing information | [questions.html](https://wingbangboozle1-lang.github.io/NBA4/questions.html), [docs/decision-register.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) | Present. |
| Site suggestions with a decision queue | [suggestions.html](https://wingbangboozle1-lang.github.io/NBA4/suggestions.html), [docs/suggestions.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/suggestions.md) | Present; nothing implemented without a decision. |
| Verified source links on every row | [sources.html](https://wingbangboozle1-lang.github.io/NBA4/sources.html), `scripts/check_site.py` | Checker enforces an official HTTPS source per table row. |
| Flagged for Review | [review.html](https://wingbangboozle1-lang.github.io/NBA4/review.html) | Pass 7 section added (P7-01 to P7-09). |

## 5. Not done, and why

- **No new player rows** from the 5:00 PM report. Transcribing 130-odd rows from page-broken PDF text without a verified count would invent values. It is recorded as a follow-up snapshot (P7-01).
- **No picks, lines, probabilities, correlations or minute estimates.** NBA Terms §9(iv) prohibits using NBA Statistics "in connection with any gambling activity". The rights gate is kept.
- **No change to the Pages deploy method** (P7-08) and **no change to the duplicate engine modules** (P7-09). Both need an owner decision.
