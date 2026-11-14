# Fourth verification pass — session `arena/c6ae3e43-nba4` (task V)

**Board note.** This session claimed task T. Task T was already taken on `main` by PR #14 (`arena/eb9d2e0b-nba4`), so this task is recorded as **V** on [`COORDINATION.md`](../COORDINATION.md). Overlapping findings from the other sessions are cross-referenced below and not counted twice.

**Snapshot date:** 2026-11-14 UTC. **Scope:** the primary pages behind the repository's blocking claims and its site-level statements, plus the live site, the GitHub Pages API and the engine test suite.

This is an evidence log, not a model or a product review. A source passes here only when the sentence the repository relies on was read on the page and quoted below. Official sites change; each row records the read date.

## 1. Result

- **19 of 19** primary source pages cited for the blocking claims were re-opened and read. Every statement the repository relies on was found on the page.
- **Live site** `https://wingbangboozle1-lang.github.io/NBA4/` returned the published overview (read 2026-11-14 UTC). It still said "47 unit tests", which was stale (overlaps T-01 on the board; now corrected on `main`).
- **GitHub Pages API** (`api.github.com/repos/wingbangboozle1-lang/NBA4/pages`, read via the sandbox's GitHub access): `status: built`, `source: main /`, `https_enforced: true`, `public: true`. The latest build record was for commit `d51ed9f87614e580b9f41ec8d2a77d2a3dbb4536`, status `built`, duration 23,961 ms, error `null`.
- **Engine test suite** (`python3 -m unittest discover -s tests -t .`): `Ran 90 tests … OK` (`tests/test_engine.py` = 47, `tests/test_engine_models.py` = 43).
- **One new irregularity** logged as V-01 on the Flagged for Review page (open, counsel awareness). Three further findings overlap the other sessions' T-01, T-02 and T-03 and were confirmed here; they are not counted twice.
- **One observation** (not a flag): the 14 Nov 2026 04:15 a.m. ET injury PDF contains "NOT YET SUBMITTED" placeholders for several teams. Any report is incomplete until every team has submitted.

## 2. Source-by-source reading

| # | Source (official / primary) | Page read | Quoted or checked statement | Result |
| --- | --- | --- | --- | --- |
| 1 | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) | 2026-11-14, first of 2 fetched chunks | "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats" | Confirmed (NBA-01) |
| 2 | [NBA Terms of Use](https://www.nba.com/termsofuse) §1 | first of 10 fetched chunks | "No Basketball Content from the Services may be reproduced, republished, … without the written permission of the Operator." | Confirmed (NBA-02) |
| 3 | NBA Terms of Use §9 | fetched chunks 3–5 of 10 (zero-indexed 3, 4, 5) | §9(ii): NBA Statistics "may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes". §9(iv) and (v): "may not be used in connection with any gambling activity (including legal gambling activity)". §9(vii): "database (in any medium or format) of comprehensive, regularly updated statistics … without the Operator’s express prior consent." | Confirmed (NBA-02) [NBA Terms of Use](https://www.nba.com/termsofuse) |
| 4 | [2026–27 NBA Injury Report policy](https://official.nba.com/nba-injury-report-2026-27-season/) | 2026-11-14 | "By 5 p.m. local time the day before a game…"; "between 11 a.m. and 1 p.m. local time"; "Reports are updated on a continual basis throughout the day." | Confirmed (NBA-03) |
| 4a | Same page, report index | 2026-11-14 | Under "**November 14:**" the index lists reports from "12:00 a.m ET report" to "4:15 a.m ET report" | Confirms overlap with **T-02** (other session) [NBA injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 4b | [14 Nov 2026 04:15 a.m. ET injury PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_15AM.pdf) | first fetched chunk | Header "Injury Report: 11/14/26 04:15 AM". Several teams show "NOT YET SUBMITTED" rows (for example DEN@NOP, DAL@CLE and BKN@MEM). Player rows not copied. | Header confirmed; observation recorded in section 1. [NBA injury report PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_15AM.pdf) |
| 5 | [Injury PDF, 13 Nov 2026 07:30 p.m. ET](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-13_07_30PM.pdf) | first of 2 fetched chunks | Header "Injury Report: 11/13/26 07:30 PM". Columns: Game Date, Game Time, Matchup, Team, Player Name, Current Status, Reason | Confirmed (NBA-04). Player rows not republished. |
| 6 | [2026–27 regular-season schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | first of 13 fetched chunks | "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE" | Confirmed (NBA-05). Fixture rows not republished. |
| 7 | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) | fetched chunk index 5 of 10 (the P entries) | PACE: "The number of possessions per 48 minutes for a team or player." | Confirmed (NBA-06) |
| 8 | [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) | 2026-11-14 | "GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your online business … or providing commercial software as a service (SaaS)."; "soft limit of 10 builds per hour" | Confirmed (GH-03) |
| 9 | [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) | first of 2 fetched chunks | "It can take up to 10 minutes for changes to your site to publish after you push the changes to GitHub."; entry file "index.html, index.md, or README.md" | Confirmed (GH-02) |
| 10 | [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | 2026-11-14 | "GitHub Pages is a static site hosting service…"; under "Data collection": "When a GitHub Pages site is visited, the visitor's IP address is logged and stored for security purposes…" | Confirmed (GH-01). **Overlaps T-03 on the board; confirmed** |
| 11 | GitHub Pages API (`/repos/…/pages` and `/pages/builds`) | 2026-11-14 via GitHub access | `status: built`; `source: main /`; `https_enforced: true`; latest build `d51ed9f…` `built` | Confirmed (GH-04). The API is a point-in-time reading, not a guarantee. [GitHub Pages API for NBA4](https://api.github.com/repos/wingbangboozle1-lang/NBA4/pages) |
| 12 | [Ksa: Remote Gambling Act in force](https://kansspelautoriteit.nl/remote-gambling-act-force) | 2026-11-14 | "In order to do so, operators need a licence from the Netherlands Gambling Authority (Kansspelautoriteit, Ksa)." | Confirmed (KSA-01) |
| 13 | [Ksa: 10 tips for gambling safely](https://kansspelautoriteit.nl/10-tips-gambling-safely) | 2026-11-14 | Tip 4: "Keep in mind that, on average, you will end up losing more than you win." Tip 8: "Winning or losing is almost always determined by coincidence or chance, not by your insight or practice" | Confirmed (KSA-04) |
| 14 | [Ksa: belangrijkste regels voor kansspelreclame](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) (Dutch) | first of 2 fetched chunks | "heeft u geen vergunning … Dan mag u in het geheel geen reclame maken" (no licence, no advertising at all); "de tekst in wet- en regelgeving is leidend" (the legal text governs). The page also links bonus rules to `prod.kansspelautoriteit.hosted-temp.com` | Confirmed (KSA-02). **New: V-01** |
| 15 | [Ksa: affiliate websites](https://kansspelautoriteit.nl/ksa-attendeert-affiliatewebsites-op-regels-voor-reclame-kansspelen) (Dutch) | 2026-11-14 | "Als die vergunning er niet is, is niet alleen de illegale aanbieder, maar ook de affiliatewebsite in overtreding." (without a licence the affiliate site is also in breach) | Confirmed (KSA-03) |
| 16 | [scikit-learn: cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) §3.1.2.6 and §3.1.3 | fetched chunks 5–6 of 8 (zero-indexed; sections 3.1.2.6 and 3.1.3) | "it is very important to evaluate our model for time series data on the 'future' observations least like those that are used to train the model"; "will likely lead to a model that is overfit and an inflated validation score" | Confirmed (ML-01) |
| 17 | [scikit-learn: model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) | first fetched chunk of 23 | Footnote 1: "The Brier score is just a different name for the squared error in case of classification with one-hot encoded targets." | Confirmed (ML-02) |
| 18 | [scikit-learn: probability calibration](https://scikit-learn.org/stable/modules/calibration.html) | first fetched chunk of 3 | "A lower Brier loss, for instance, does not necessarily mean a better calibrated model" | Confirmed (ML-03). Also the source of VF-04's attribution. |
| 19 | [NIST glossary: correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) | fetched chunk index 3 of 16 (the C entries) | "Correlation is a measure of the strength of the (usually linear) relationship between two variables. The usual correlation coefficient, called the Pearson correlation coefficient, ranges from -1 to 1." | Confirmed (STAT-01) |
| 20 | [NIST: bootstrap plot](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) | 2026-11-14 | "The bootstrap … is used to estimate the uncertainty of a statistic"; subsamples "typically between 500 and 1000"; "The bootstrap is not appropriate for all distributions and statistics" | Confirmed (STAT-02) |

(Rows 1–20 cover 19 distinct primary pages; row 3 and row 4a are additional readings of pages 2 and 4.)

## 3. Irregularities and cross-references

| ID | Irregularity | Status | Cross-reference and action | Official source |
| --- | --- | --- | --- | --- |
| V-01 | The Ksa advertising-rules page links its bonus-rules text to `prod.kansspelautoriteit.hosted-temp.com`, which is not a `kansspelautoriteit.nl` host. | Open — counsel awareness | New in this pass; flagged on the Flagged for Review page. The repository does not cite that host. Owner or counsel to confirm if bonus rules become relevant. | [Ksa advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) |
| T-01 (overlap) | "47 unit tests" on the overview, automation page, README and docs. The suite runs 90 tests (47 + 43) and passes. | Corrected on `main` (PR #14 and this merge) | Re-confirmed in this pass: `Ran 90 tests … OK`. | [Test suite, repo](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine_models.py) |
| T-02 (overlap) | Injury snapshot one day behind the official index, which on 2026-11-14 UTC lists 14 Nov reports. | Open (recurring freshness) | Re-confirmed: the index lists 14 Nov reports to 4:15 a.m. ET; the 04:15 a.m. PDF header reads "Injury Report: 11/14/26 04:15 AM" (row 4b). Its "NOT YET SUBMITTED" rows are an additional completeness caveat. | [NBA injury report page](https://official.nba.com/nba-injury-report-2026-27-season/) |
| T-03 (overlap) | README "no data collection" overstated the hosting layer. | Corrected on `main` | Re-confirmed: GitHub's Pages documentation says visitors' IP addresses are logged and stored for security purposes. | [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection) |

Other findings on `main` (IR-T1 duplicate engine modules, IR-T4 picks versus NBA Terms §9) are not re-litigated here. They stay on the Flagged for Review page with their own owners.

## 4. What was not re-read in this pass

To keep the evidence honest, these were **not** read end to end in this pass:

- The remaining chunks of the NBA Stats FAQ (second chunk), NBA Terms of Use (chunks 2, 6–10), NBA Stats glossary (other 8 chunks), NIST glossary (other 15 chunks), scikit-learn pages (other chunks), Ksa pages (other text), the schedule PDF (chunks 2–13).
- The 13 Nov 7:45 p.m. and 8:00 p.m. ET injury PDFs and the 14 Nov reports. No player-level row from any injury report was read or copied.
- Any NBA statistic, schedule row, odds or market value. None is used in this pass or in the repository.

Earlier logs (`docs/source-verification.md`, `docs/verification-log.md`, `docs/verification-pass-2c06c7f9.md`) remain the record for the statements they checked. This log adds the reading above and does not replace them.

## 5. Method and limits

- Pages were read with the web-fetch tool. Bash in the sandbox cannot reach these hosts, except the GitHub API.
- "Confirmed" means the quoted sentence appears on the page on the read date. It does not mean the page's legal effect has been analysed. The NBA Terms and the Ksa rules need counsel for any legal conclusion, as the rest of the repository already says.
- Official pages change. Re-read them before relying on any row after the date above.
