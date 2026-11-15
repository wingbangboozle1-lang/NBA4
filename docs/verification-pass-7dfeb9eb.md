# Verification pass 8 — session `arena/7dfeb9eb-nba4` (15 Nov 2026)

Board tasks AO–AS. Two things were done in this pass: the requirement list in the project brief was implemented in
the engine (twelve modules, 132 new tests, 246 in the repository), and the published official observations were
re-cut from the two newest injury reports and the schedule. Every value on the site comes from one of the documents
in the last column of this file; nothing here was inferred, and every irregularity found in the documents is
listed in [Flagged for review](../review.html) rather than corrected.

## What was read, and how

| # | Observation read | How it was checked | What was found | Source |
| --- | --- | --- | --- | --- |
| 1 | NBA Official Injury Report, revision printed as `Injury Report: 11/15/26 06:15 AM` | Both chunks of the PDF text read in full; every row transcribed by hand into `data/snapshots/injuries-2026-11-15-0615am.json` | 101 rows over 17 game blocks (nine games on 11/15, eight on 11/16). 87 rows print fewer than seven cells; 13 lose the club cell too | [Injury Report 11/15 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| 2 | NBA Official Injury Report, revision printed as `Injury Report: 11/14/26 05:00 PM` | Both chunks read in full and transcribed into `data/snapshots/injuries-2026-11-14-1700pm.json`; this is the file the 11/14 pass recorded as "listed but not transcribed" | 99 rows over 14 game blocks, 77 with lost cells, 12 `NOT YET SUBMITTED` markers, no New York block at all | [Injury Report 11/14 05:00 PM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_05_00PM.pdf) |
| 3 | The two consecutive reports, compared row by row | `engine/injurydiff.py` keyed on the normalised printed name; 58 change rows, of which 56 are clubs filing rows they had not filed at the earlier deadline | Los Angeles, Phoenix, Charlotte, the Clippers, San Antonio, Utah, Atlanta, Milwaukee, Oklahoma City and Sacramento all filed between the two reports; the two spelling differences are surfaced, not merged | [Injury Report 11/15 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| 4 | Printed player names across the two revisions | String comparison of the same club and position between the two documents | `Embid, Joel` (11/15) vs `Embiid, Joel` (11/14), and `Champagne, Justin` vs `Champagnie, Justin`. Both spellings are stored as printed; flag P8-04 | [Injury Report 11/14 05:00 PM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_05_00PM.pdf) |
| 5 | Tip-off times, which the report prints on a 12-hour clock with no meridian | Each report time compared with the ET column of the official schedule PDF for the same date and matchup | 17 of 17 11/15–11/16 blocks agree once the meridian is read from the schedule; the schedule's own revision is unchanged (13 Aug 2026), so the repair is stable | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 6 | Away-at-home order for the new window rows (rows 236–257) | The schedule PDF text prints no `at` token on rows 215–259; corroborated only where an injury report prints the same `AWAY@HOME` code on the same date | Rows 236–252 corroborated (11/15 against the 05:00 PM and 04:30 AM reports, 11/16 against the 06:15 AM report), which closes P7-02 for those eight; rows 253–257 stay unverified and print no local time | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 7 | New York @ Toronto appearing twice | Schedule rows 241 and 253 compared with the injury-report blocks for both days | Both documents are internally consistent: the pairing is listed on 11/15 and again on 11/17. Flagged (P8-06), not corrected, and the corroboration key was changed to (date, matchup) so one day cannot vouch for the other | [Injury Report 11/15 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| 8 | Reporting deadlines and update cadence quoted on the injury pages | Re-read of the index page text used by the earlier passes | The 5 p.m. local day-before deadline, the 1 p.m. back-to-back deadline, the game-day 11 a.m.–1 p.m. window and "updated on a continual basis throughout the day" are the basis for the freshness gate in the engine and for the page's "newest retrieved, not newest that exists" banner | [NBA Injury Report 2026-27 index](https://official.nba.com/nba-injury-report-2026-27-season/) |

## Requirement items implemented in the engine

Each row names the module, the rule it enforces, and the test file that pins it
([`tests/test_engine_requirements.py`](../tests/test_engine_requirements.py), 132 cases, synthetic fixtures on
`synthetic.invalid` only — no NBA data is used in any test).

| Brief item | Module | The rule that is actually enforced | Source of the rule |
| --- | --- | --- | --- |
| Verify line by line; never infer a value | `engine/officialresults.py` | One row per game; quarter scores must sum to the final; two officials that disagree produce **no** row; a stale feed is refused. `observation_count` counts distinct source documents, not repeated quotes of one document | [NBA Stats FAQ: stats are not available for download](https://www.nba.com/stats/help/faq) |
| Irregularities must be visible | `engine/injurydiff.py` | Consecutive reports are diffed; added / removed / status / reason / name-drift are separate kinds, and the archive verifies each file against its recorded SHA-256 before it can be cited | [Injury Report 11/15 06:15 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-15_06_15AM.pdf) |
| No moving the goalposts after a bet | `engine/preregistration.py` | All four sections must be non-placeholder; `minimum_edge`, `minimum_sample`, `maximum_trials` and `significance_alpha` may not be defaulted; `frozen_at` must precede the first recorded bet | [Time-based cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| Publish before tip, settle after verified finals | `engine/publishedledger.py` | A prediction dated after tip-off is refused; a day seal dated after the earliest tip in that day is refused; settlement requires verified finals **and** a sealed day, and the seal records leaf order so a re-ordered day cannot pass | [NBA.com Terms of Use §1](https://www.nba.com/termsofuse) |
| Disagreement value between independent estimators | `engine/confidence.py` | Banding of the spread gap with sign disagreement as a split; a shared-input audit that refuses a headline when two "estimators" read the same inputs; a blend that is permanently footnoted as arithmetic, never a probability; a home-court value in use that must equal the pinned win-rate mapping | [Probability calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| Luck removal | `engine/luck.py` | A per-team luck z-score against a **registered** noise band, refusing when the band, the sample or the declared universe is missing; de-luck output carries the inflation factor it used | [NIST ITL handbook on statistical validation](https://itl.nist.gov/) |
| Injury → rotation → game flow | `engine/rotations.py` | Top-8 minutes-share redistribution that must conserve 240 team minutes and report `unallocated_minutes`; a published availability column whose blank means "not sourced", never "healthy" | [NBA Injury Report 2026-27 index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Travel and rest context | `engine/venues.py`, `engine/rest.py` | Arena coordinates are an empty table until sourced, so travel prints `TRAVEL_NO_SOURCE`; rest days, back-to-back, 3-in-4 and 4-in-6 come from slate rows only | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Originate a line, and price a parlay honestly | `engine/markets.py`, `engine/totals.py` | The closing-line anchor is weighted by out-of-sample log loss, not by confidence; a parlay always prints the naive product beside the correlated price and returns `BOUNDED_NOT_PRICED` when rho is missing or ranged; a totals model is published beside the naive scoring-average baseline with the gap between them | [NBA.com Terms of Use §9](https://www.nba.com/termsofuse) |
| Projection surface vs bet surface | `engine/surfaces.py` | Every published field is declared on exactly one surface; a gated field renders as `{"value": None, "status": "GATED", reason_codes}`; a page that shows a number under a bet-gated heading fails the audit | [NBA.com Terms of Use §1](https://www.nba.com/termsofuse) |

## Corrections made while verifying

1. **A real engine defect (P8-01).** `engine/parlay.py` priced a copula leg with the threshold Φ⁻¹(p) instead of
   Φ⁻¹(1 − p). Every marginal other than 0.5 was inverted, and the 103 tests that predate this pass could not see
   it because their fixtures used 0.5 legs. Fixed here; the naive product beside the correlated price is now
   comparable again.
2. **Two test expectations were wrong and were corrected rather than the code** — the anchor weight is only
   accurate to four decimal places against the hand value, and a same-sign four-point gap is a material gap, not
   a split. Recorded so a later session does not "fix" the code back.
3. **`docs/estimators.md` says "The site and existing snapshot tables remain unchanged."** That was true of the
   merge it documents (PR #48) and is not true of the published site after this pass: the slate and injury tables
   were re-cut from the 11/15 documents. The file is left to its owning session; this note is the correction.
4. **A cross-session collision was resolved by moving, not deleting.** This session's disagreement/confidence
   layer was written to `engine/estimators.py`, the same path session `arena/37a389fa-nba4` used for its estimator
   comparison. PR #48 merged first, so its module keeps the path and this layer now lives in
   `engine/confidence.py`. It is a reporting and policy layer: it consumes their `EstimatorComparison` and
   `engine/ratings.py` rather than adding a second estimator or a second home-court mapping.

## Still blank, and why

| Item | State | Blocking input | Source checked |
| --- | --- | --- | --- |
| Per-player game logs for injured players | blank | none — the league's stats pages state their data is not available for download or personal use, so no licensed log source is registered | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| Availability probability, minutes, production impact | blank | no point-in-time history and no validated model; the engine refuses to publish an estimate it cannot source | [NBA Injury Report 2026-27 index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Originated lines, prices, picks, leaderboard and any reward row | blank, every row reason-coded | the rights gate (G0) filters inputs without a registered `allowed_use`, and every bet-surface field must pass `engine/surfaces.py` before it can appear | [NBA.com Terms of Use](https://www.nba.com/termsofuse) |
| Venue coordinates and travel legs | blank | no official arena-coordinate table has been transcribed | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 11/17 home-venue local tip times | blank for rows 253–257 | the first time column was not transcribed at retrieval, and a conversion from the Eastern value would be arithmetic presented as an observation | [2026-27 schedule by date](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
