# Coordination board

Updated: 2026-11-14 (UTC). The starting repository contained only `README.md` and no coordination board or task claims. The session IDs below use the active Arena branch identifiers because no separate session ID is exposed in the repository.

**Concurrency note.** A second session (`arena/ddc81141-nba4`) ran in parallel with the final integration session. It found that task E was completed and merged via PR #2 while its own work was in progress. On rebasing, that session's `COORDINATION.md` claim was superseded by the integration record below rather than overwriting it. The remaining deltas from that session — the source re-verification, two corrections and the new suggestions section — are recorded as tasks F, G and H, and were merged by PR #3.

| Task | Status | Owner / session ID | Exact file scope | Verification / sources / notes |
| --- | --- | --- | --- | --- |
| A. Baseline repository, evidence and decision-gap audit | done | `arena/c5eef6bb-nba4` | `COORDINATION.md`, `docs/audit.md` | Verified the starting one-line README/no application data; checked NBA Stats FAQ, NBA Terms §§1/9, 2026–27 injury policy/PDF and schedule, NBA Stats glossary, GitHub Pages docs/API, and Ksa pages. Detailed snapshot, scope limits, and citations: [`docs/audit.md`](docs/audit.md). |
| B. Strategy design, validation gates, correlation and leaderboard specification | done | `arena/c5eef6bb-nba4` | `docs/strategy-framework.md`, `docs/validation-plan.md` | Proposed single, prop, injury, game-flow and joint/parlay hypotheses; defined chronological/holdout, calibration, uncertainty and leaderboard gates. Confirmed method references at NBA Stats/Terms, NBA Injury Report, scikit-learn time-split/calibration/Brier docs, NIST correlation/bootstrap pages. No strategy was trained; all metric/correlation/result cells remain blank. Markdown table-link and whitespace checks passed. |
| C. Executive summary, questions, missing-information register and source catalog | done | `arena/c5eef6bb-nba4` | `docs/decision-register.md`, `docs/sources.md` | Completed executive summary, 12 decision questions, discovery recommendations, known/missing inputs and official source catalog. Checked every Markdown data row for an official source link; the structural/link-presence check passed. |
| D. Site information architecture and content specification (no shared pages/data) | done | `arena/c5eef6bb-nba4` | `docs/site-spec.md` | Spec defines seven categories, source-linked-table rules, blank/unverified handling, rights safeguards, accessibility and local link checks; verified against NBA Terms, official schedule/injury pages, and GitHub Pages docs/API. Shared index/navigation/data remained untouched until integration. |
| E. Final site integration, full verification, build/link checks, PR and Pages deployment | done | `arena/eb3064e3-nba4` | `COORDINATION.md`, `index.html`, `slate.html`, `injuries.html`, `strategies.html`, `questions.html`, `sources.html`, `review.html`, `assets/**`, `scripts/check_site.py`, `.nojekyll`, `README.md` | Claim committed before work. Merged A–D content, ran the static checker, verified every live page and every distinct external source against its primary page, confirmed GitHub Pages build/deployment, then opened and merged the integration PR (see Publication record below). |

| F. Independent line-by-line source re-verification and correction log | done | `arena/ddc81141-nba4` | `docs/verification-log.md`, `docs/audit.md`, `docs/decision-register.md`, `docs/sources.md` | All 22 cited sources fetched again and compared with the claim text; exact quotations recorded. 22/22 exist and support the claim. Four irregularities logged (VF-01 … VF-04); two were factual errors and are corrected. Evidence: [`docs/verification-log.md`](docs/verification-log.md). |
| G. Suggestions review section | done | `arena/ddc81141-nba4` | `suggestions.html`, `docs/suggestions.md`, navigation on all pages | 12 proposals and 4 gating decisions, each with options, trade-off, effort, status and an official source, so a reviewer can choose a path before anything is built. Added to navigation on all eight pages and to the site checker. |
| H. Second integration pass, PR and deployment re-confirmation | done | `arena/ddc81141-nba4` | `COORDINATION.md`, `README.md`, `scripts/check_site.py` | Rebased onto the PR #2 merge; re-ran the checker (8 pages, 107 HTML rows, 104 Markdown rows). PR and deploy result recorded in the Publication record. |

## Second verification pass and corrections (session `arena/ddc81141-nba4`)

**Why a second pass.** The integration session verified that every claim matched its source. This pass additionally recorded the literal quoted passage for each source so a reader can check the claim without re-fetching everything, and reviewed the site for internal consistency rather than only link integrity. Full evidence: [`docs/verification-log.md`](docs/verification-log.md).

**Result.** 22 of 22 cited sources exist and support the statement made about them. No fabricated source, dead link or misquote was found. No data value changed, because no NBA-derived data value exists anywhere in the repository.

| Flag | Irregularity found | Severity | Resolution |
| --- | --- | --- | --- |
| VF-01 | The 2026-11-13 7:30 p.m. ET injury PDF was described as the **latest checked** report. The official page for that date also lists 7:45 p.m. and 8:00 p.m. ET reports. | Medium — freshness claim stronger than the evidence | Wording corrected in `docs/audit.md`, `docs/decision-register.md`, `docs/sources.md`, `injuries.html` and `sources.html`. Now stated as one snapshot, with the later reports acknowledged. Published on the Flagged for Review page. |
| VF-02 | `docs/decision-register.md` Q3 placed the owner in Amsterdam; session context says Naaldwijk, South Holland, NL. | Low — context only | Corrected and still labelled session context, not a product jurisdiction. |
| VF-03 | KSA-02 and KSA-03 are Dutch-language pages described in English. | Low — presentational | Flagged for review with the note to read the Dutch text with counsel. |
| VF-04 | The Brier-decomposition sentence is on scikit-learn's calibration page, not its metrics page. | Low — attribution | Correct attribution recorded; both links retained. |

**Site consistency checks run in this pass.** No `<script>`, analytics, form, iframe or cookie usage on any page; every page's HTML tags are balanced; every external host is on the approved list (NBA, GitHub, Ksa, NIST, scikit-learn, and this project's own published site); every table row ends in an official source; every local link and fragment resolves.

## Final integration verification (session `arena/eb3064e3-nba4`, 2026-11-14 UTC)

**Method.** The final integration session took ownership of task E, re-ran the repository's own static checker, then re-verified each fact and each link against the primary source (not a summary or snippet). The sandbox could not reach arbitrary hosts over plain `curl`; verification was performed with the web-fetch tool, which resolved every cited URL to the live primary page. Local build/link/table integrity was checked with `python3 scripts/check_site.py`.

**Static check (re-run, passed).** `python3 scripts/check_site.py` → `PASS: 7 pages, 82 HTML data rows and 72 Markdown data rows passed.` (After the PR #3 additions the same check reports `PASS: 8 pages, 107 HTML data rows and 104 Markdown data rows passed.`) Every HTML table data row ends in an official HTTPS source cell; every Markdown table data row in `docs/` contains an official HTTPS source link; every page has exactly one non-empty `<h1>`; all local links and fragments resolve.

**Source re-verification (each URL fetched and matched to the statement in its row).**

| Source | Verified statement | Link |
| --- | --- | --- |
| NBA Stats FAQ | "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats." | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| NBA.com Terms of Use §1, §9 | §1 restricts reproduction/publication/reuse of Basketball Content without written permission; §9 states NBA Statistics "may not be used in connection with any gambling activity (including legal gambling activity)" and may not be used for a comprehensive, regularly updated statistics database without the Operator's express prior consent. | [NBA.com Terms](https://www.nba.com/termsofuse) |
| NBA Official 2026–27 Injury Report | Teams must report participation status/reason by set deadlines; "Reports are updated on a continual basis throughout the day." | [NBA injury policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| NBA injury report PDF snapshot | File timestamped "Injury Report: 11/13/26 07:30 PM" with game/player status and reason rows for that snapshot only. | [Official report PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-13_07_30PM.pdf) |
| NBA 2026–27 regular-season schedule | Header reads "AS OF AUGUST 13, 2026 | SUBJECT TO CHANGE." | [Official schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| NBA Stats glossary | Defines metric labels including minutes and pace/offensive rating (definitions only). | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) |
| GitHub Pages limits | "GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your online business, e-commerce site, or any other website that is primarily directed at either facilitating commercial transactions or providing commercial software as a service (SaaS)." | [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| GitHub Pages creation docs | Pages publishes static files and does not support server-side languages. | [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) |
| GitHub Pages API (this repo) | `status: built`, `public: true`, source `main` at `/`, `https_enforced: true`. | [Repository Pages API](https://api.github.com/repos/wingbangboozle1-lang/NBA4/pages) |
| Ksa — Remote Gambling Act in force | Operators need a Ksa licence to offer gambling via the internet in the Netherlands. | [Ksa licensing](https://kansspelautoriteit.nl/remote-gambling-act-force) |
| Ksa — key advertising rules | Page states it is a summary of the rules and that unlicensed operators may not advertise. | [Ksa advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) |
| Ksa — affiliate guidance | Ksa addresses affiliate websites that direct users to gambling operators and the applicable advertising rules. | [Ksa affiliate guidance](https://kansspelautoriteit.nl/ksa-attendeert-affiliatewebsites-op-regels-voor-reclame-kansspelen) |
| Ksa — 10 tips for gambling safely | Tip 8: winning/losing "is almost always determined by coincidence or chance, not by your insight or practice." | [Ksa safe-gambling tips](https://kansspelautoriteit.nl/10-tips-gambling-safely) |
| scikit-learn — cross-validation | Documents future-after-past evaluation and the leakage risk of training on future/evaluating the past. | [Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| scikit-learn — model evaluation | Brier score is a proper probability score; a lower Brier alone does not prove better calibration. | [Model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| scikit-learn — calibration | Reliability/calibration curves; Brier/log loss combine reliability, resolution and uncertainty. | [Probability calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| NIST — correlation glossary | Correlation is a measure of (usually linear) association; Pearson coefficient ranges −1 to +1. | [NIST glossary](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| NIST — bootstrap plot | Bootstrap resampling estimates statistic uncertainty and is not appropriate for every statistic/distribution. | [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |

**Live site verification.** All seven pages were fetched from the deployed URL and returned their full content with every table and source link intact: `index.html`, `slate.html`, `injuries.html`, `strategies.html`, `questions.html`, `sources.html`, `review.html`. GitHub Pages API reported `status: built`; the live URL is [https://wingbangboozle1-lang.github.io/NBA4/](https://wingbangboozle1-lang.github.io/NBA4/).

**Irregularities and observations.**

- **No fabricated data.** No NBA game rows, player rows, odds, probabilities, correlations, injury-minute effects, ROI, or strategy results were added. All numeric model fields remain blank and flagged unverified. The injury PDF was verified only as a dated snapshot; no player rows from it were copied into the site.
- **Alternate Ksa URL resolves.** `docs/audit.md` cites `https://kansspelautoriteit.nl/voor-zakelijke-aanbieders/beperken-reclame/belangrijkste-regels-kansspelreclame-per/`; fetching it resolves to the same canonical "Belangrijkste regels voor kansspelreclame" page used elsewhere in the site. No change needed; noted for the record.
- **Pre-existing merge.** The A–D content and the site files were already merged into `main` via PR #1 before this session; task E's remaining work was final verification, board completion, and the integration PR. The prior board entry left E "in progress"; this entry closes it.
- **No external-source changes required.** Every claim in the site matched the primary source at verification time. Time-sensitive NBA schedule/injury pages were checked against their dated snapshots; they are explicitly labelled as dated/changeable rather than live feeds.

## Publication record

| Item | Result |
| --- | --- |
| PR #2 (integration) | Created from `arena/eb3064e3-nba4` to `main`; merged. |
| PR #3 (suggestions, verification and corrections) | Created from `arena/ddc81141-nba4` to `main` after rebasing onto the PR #2 merge; merge result appended below by that session. |
| GitHub Pages | `status: built`; published from `main` at `/`; HTTPS enforced; public. |
| Live URL | [https://wingbangboozle1-lang.github.io/NBA4/](https://wingbangboozle1-lang.github.io/NBA4/) |
| Post-merge check | Site re-fetched after merge; all seven pages served with intact tables and source links. |

## Handoff and integrity rules

- Keep file scopes non-overlapping and update this board before starting work. If a needed file is owned by another session, log a request here rather than editing it.
- Every factual data value must have an official primary source, a source timestamp, and a verification status. Leave unknown values blank and flag them; do not manufacture picks, probabilities, correlations, or performance.
- Strategy claims are hypotheses until a pre-registered, leakage-free, out-of-sample validation supports them. This board records status and evidence; it is not itself evidence.
- GitHub Pages publication is conditional on verified inputs, a passing site build/link check, and repository Pages configuration. Deployment was confirmed successful in the Publication record above.
