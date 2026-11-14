# Verification pass 4 — session `arena/98c57da8-nba4` (14 Nov 2026)

**Scope.** Task T on the coordination board. A fresh, line-by-line re-read of every cited primary web URL (21 URLs covering 20 distinct pages; one URL is a redirect alias of a page already listed) and the GitHub Pages API, followed by repository integrity checks (GitHub blob links, relative links, counts, navigation). Each row records the exact wording checked today, so a reviewer can compare it with the live page without re-running the pass.

**Method.** Each document was opened with the web-fetch tool on 14 Nov 2026 and the sentence the repository relies on was compared with the text on the page. Where a claim depends on a specific section (for example NBA Terms §9), the chunk containing that section was read. Quotations below are verbatim from the fetched text. Translations of Dutch text are marked as translations.

**Result.** All 21 cited primary web URLs exist and support the statement made about them. Four documents needed a correction or a flag (see the irregularity table). No data value changed, because the repository contains no NBA-derived values.

## 1. Source re-verification

| # | Source (primary) | Repository claim | Wording checked on 14 Nov 2026 | Result |
| --- | --- | --- | --- | --- |
| 1 | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) | Statistics are not for download | "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats" | Confirmed |
| 2 | [NBA Terms of Use §1](https://www.nba.com/termsofuse) | Basketball content may not be reproduced or reused without written permission | "...without the written permission of the Operator." | Confirmed |
| 3 | [NBA Terms §9(ii)](https://www.nba.com/termsofuse#nba-statistics) | Use is for legitimate news reporting or private, non-commercial purposes | "the NBA Statistics may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes" | Confirmed |
| 4 | [NBA Terms §9(v)](https://www.nba.com/termsofuse#nba-statistics) | No gambling use | "may not be used in connection with any gambling activity (including legal gambling activity)" | Confirmed |
| 5 | [NBA Terms §9(vii)](https://www.nba.com/termsofuse#nba-statistics) | No comprehensive statistics database without consent | "...features a database ... of comprehensive, regularly updated statistics ... without the Operator's express prior consent." | Confirmed |
| 6 | [NBA injury-report policy 2026–27](https://official.nba.com/nba-injury-report-2026-27-season/) | Reports are updated through the day | "Reports are updated on a continual basis throughout the day." The page also lists 14 Nov 2026 reports from 12:00 a.m. to 4:15 a.m. ET. | Confirmed; see V4-08 |
| 7 | [Injury report PDF, 13 Nov 2026 07:30 PM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-13_07_30PM.pdf) | Dated snapshot with status/reason rows | Header "Injury Report: 11/13/26 07:30 PM"; rows with Game Date, Matchup, Team, Player, Current Status, Reason | Confirmed |
| 8 | [Injury report PDF, 13 Nov 2026 08:00 PM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-13_08_00PM.pdf) | Later snapshot on the same day | Header "Injury Report: 11/13/26 08:00 PM" | Confirmed (cited in the 2c06c7f9 log) |
| 9 | [NBA 2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | Schedule is "as of" 13 Aug 2026 and subject to change | "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE" | Confirmed |
| 10 | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) | Defines metric labels such as PACE | PACE appears in the glossary index (entry 214, anchor `#pace`). The definition text was not re-read in this pass. | Confirmed for the label; definition not re-read |
| 11 | [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) | Not for commercial SaaS or online-business hosting | "GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your online business, e-commerce site, or any other website that is primarily directed at either facilitating commercial transactions or providing commercial software as a service (SaaS)." Soft limit of 10 builds per hour. | Confirmed |
| 12 | [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) | Pages publishes static files; no server-side languages | Note: "GitHub Pages does not support server-side languages such as PHP, Ruby, or Python." The page also says `.nojekyll` disables the Jekyll build. | Confirmed (this corrects IR-01; see V4-01) |
| 13 | [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | Static hosting of HTML, CSS and JavaScript | "GitHub Pages is a static site hosting service that takes HTML, CSS, and JavaScript files straight from a repository on GitHub" | Confirmed |
| 14 | [Ksa — 10 tips for gambling safely](https://kansspelautoriteit.nl/10-tips-gambling-safely) | Tip 8: outcome is chance, not skill | "Winning or losing is almost always determined by coincidence or chance, not by your insight or practice, and certainly not by superstition" | Confirmed |
| 15 | [Ksa — Remote Gambling Act in force](https://kansspelautoriteit.nl/remote-gambling-act-force) | Operators need a Ksa licence for online gambling in the Netherlands | "operators need a licence from the Netherlands Gambling Authority (Kansspelautoriteit, Ksa)" (English page) | Confirmed |
| 16 | [Ksa — key advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) | Summary only; no advertising without a licence | Dutch: "Deze informatie is een samenvatting van de geldende regelgeving" and "heeft u geen vergunning ... Dan mag u in het geheel geen reclame maken." (Translation: the page is a summary; without a licence you may not advertise at all.) | Confirmed. Page also links to a non-Ksa host; see V4-07 |
| 17 | [Ksa — affiliate websites](https://kansspelautoriteit.nl/ksa-attendeert-affiliatewebsites-op-regels-voor-reclame-kansspelen) | Ksa addresses affiliate sites | Dutch: "er alleen reclame mag worden gemaakt voor gokbedrijven met een vergunning" (Translation: advertising is permitted only for licensed operators) | Confirmed |
| 18 | [Ksa advertising-rules alias](https://kansspelautoriteit.nl/voor-zakelijke-aanbieders/beperken-reclame/belangrijkste-regels-kansspelreclame-per/) | Same page as #16 | Returned the same title and text under the canonical URL | Confirmed, but the alias is a redirect; citations moved to the canonical URL (V4-06) |
| 19 | [scikit-learn — cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) | Evaluate on future observations; leakage | "it is very important to evaluate our model for time series data on the 'future' observations least like those that are used to train the model." | Confirmed |
| 20 | [scikit-learn — probability calibration](https://scikit-learn.org/stable/modules/calibration.html) | Lower Brier loss does not necessarily mean better calibration | "A lower Brier loss, for instance, does not necessarily mean a better calibrated model" | Confirmed; attribution is this page (V4-02) |
| 21 | [scikit-learn — brier_score_loss](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html) | Brier is a strictly proper scoring rule | "The Brier score is a strictly proper scoring rule." | Confirmed |
| 22 | [scikit-learn — model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) | Brier is a strictly consistent scoring function for the mean of classification probabilities | The table lists the Brier score as a strictly consistent scoring function for the mean. The calibration sentence is not on this page. | Confirmed for the scoring-rule statement only (V4-02) |
| 23 | [NIST — bootstrap plot](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) | Bootstrap estimates uncertainty; cautions apply | "The bootstrap ... is used to estimate the uncertainty of a statistic." Caution: "The bootstrap is not appropriate for all distributions and statistics." | Confirmed |
| 24 | [NIST — glossary, correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) | Correlation measures usually linear association; Pearson −1 to 1 | "Correlation is a measure of the strength of the (usually linear) relationship between two variables. The usual correlation coefficient, called the Pearson correlation coefficient, ranges from -1 to 1." | Confirmed |
| 25 | [GitHub Pages API for this repository](https://api.github.com/repos/wingbangboozle1-lang/NBA4/pages) | Pages settings | `status: built`, `public: true`, source `main` at `/`, `https_enforced: true`, legacy build | Confirmed on 14 Nov 2026 |
| 26 | [Latest Pages build](https://api.github.com/repos/wingbangboozle1-lang/NBA4/pages/builds/latest) | Build status | `status: built`, commit `d51ed9f87614e580b9f41ec8d2a77d2a3dbb4536`, duration 23,961 ms, error message `null` | Confirmed |

The table has 26 rows: 21 cited primary web URLs (20 distinct pages; several rows check different sections of the same page, such as NBA Terms §1 and §9) plus the two GitHub Pages API rows. Every cited page was re-read; the NBA glossary definition text is the only item not read in full.

## 2. Repository integrity checks (14 Nov 2026)

| Check | Result | Source |
| --- | --- | --- |
| GitHub blob and tree links to `wingbangboozle1-lang/NBA4` on `main` (187 links in pages, docs, README and board) | All targets exist; 0 missing | [all linked files](https://github.com/wingbangboozle1-lang/NBA4/tree/main) |
| Relative Markdown links in `docs/*.md` and `README.md` | All targets exist; 0 missing | [docs folder](https://github.com/wingbangboozle1-lang/NBA4/tree/main/docs) |
| Engine unit tests (`python3 -m unittest discover -s tests -t .`) | 90 pass (47 in `test_engine.py`, 43 in `test_engine_models.py`) | [tests folder](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| Models module alone (`python3 -m unittest tests.test_engine_models`) | 43 pass | [test_engine_models.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine_models.py) |
| Decision questions (`Q1`–`Q16`) in the register and on the questions page | 16 and 16 | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Suggestion IDs in `docs/suggestions.md` | 39 (D-1…D-4, P-01…P-12, S-01…S-23), matching the 4 + 12 + 23 described on the overview | [suggestions register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/suggestions.md) |
| Duplicate primary-navigation links | Found on six pages before this pass; fixed; the checker now fails on it | [checker](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| Test-count statements on README and landing page | Found stale (47); fixed; the checker now fails on a stale count | [README](https://github.com/wingbangboozle1-lang/NBA4/blob/main/README.md) |

## 3. Irregularities for review

| ID | Severity | Irregularity | Action | Source |
| --- | --- | --- | --- | --- |
| V4-01 | Low | IR-01 was a false positive. The creation page carries the server-side-language sentence as a Note. | Withdrawn on the review page; the original claim stands. | [Creating a site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) |
| V4-02 | Low | The coordination-board row still attributed the calibration sentence to the model-evaluation page. | Row split. | [Probability calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| V4-03 | Low | README and landing page stated 47 engine unit tests; the suite has 90. | Corrected; checker guard added. | [tests folder](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| V4-04 | Low | `docs/engine.md` attributed the 43-test count to the discover command. | Corrected to `tests.test_engine_models`. | [engine guide](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/engine.md) |
| V4-05 | Low | Duplicate "Suggestions" sidebar link on six pages. | Removed; checker guard added. | [review page](https://github.com/wingbangboozle1-lang/NBA4/blob/main/review.html) |
| V4-06 | Low | A Ksa citation path is a redirect to the canonical Ksa page. | Citations moved to the canonical URL in `docs/audit.md` and `docs/validation-plan.md`. | [Ksa canonical page](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) |
| V4-07 | Medium | The official Ksa advertising page links to `prod.kansspelautoriteit.hosted-temp.com`, a host not on kansspelautoriteit.nl. | Open for counsel. Not cited by the repository. | [Ksa advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) |
| V4-08 | Medium | The cited injury PDF is one dated snapshot. The official page lists later 14 Nov 2026 reports. | Open (IR-04). No player rows are republished. | [NBA injury report](https://official.nba.com/nba-injury-report-2026-27-season/) |
| V4-09 | Low | The board asks for session branches, while the session branch rule names one branch for this session. | Recorded on the board; no file scope overlaps with another session. | [coordination board](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md) |

## 4. Not re-verified in this pass

- The Dutch text of the Ksa pages is summarised as a translation for the reader. Counsel should read the Dutch text (VF-03 remains open).
- The NBA glossary definition text for PACE is not re-read (only its index entry).
- No NBA statistics, injury rows or schedule rows were copied into the repository. The NBA Terms restrict reproduction (§1) and the NBA Stats FAQ states that the statistics are not available for download, so this pass did not republish them.
