# Verification pass 6b — session `arena/c4d167da-nba4`

**Date:** 2026-11-14 (UTC). **Branch:** `arena/c4d167da-nba4`, branched from `a52a4d60` (PR #35 merge).
**Board tasks:** AJ (external-source quote-check), AK (requirements-coverage map and fixes), AL (final integration, PR, deployment).

**Method.** Every source below was re-fetched from its primary URL during this session and the sentence the
repository relies on was compared with the text actually returned. Where a quotation is given it is verbatim.
Nothing was accepted from memory, and nothing that could not be read is asserted as verified. GitHub blob/tree
links were not individually re-fetched (they are repository-internal and are link-checked by
[`scripts/check_site.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py)).

---

## 1. Non-overlapping scope (parallel sessions)

Two sessions merged into `main` while this session was working: `arena/ad4e7bf0-nba4` (task AF, PR #36,
10:26:48Z) and `arena/b9938e48-nba4` (task AG, PR #37, 10:29:18Z). `arena/b9938e48-nba4` had already
compared all 22 published schedule rows and all 49 published injury rows field by field and answered Q21 from
the PDF's `LOCAL | ET` header. **This session does not repeat that comparison as a new claim.** It re-derived it
independently as a cross-check (section 4 — the two agree) and directed its quote-checking at the sources that
session did **not** re-read, which is this session's distinct contribution:

- session `arena/b9938e48-nba4` re-read: the schedule PDF rows, the 04:30 AM injury PDF, the NBA Stats FAQ and
  the GitHub Pages limits page, and attempted the NBA Terms page (502);
- **this session** re-read: the NBA injury-report policy page, scikit-learn × 4 (v1.9.1), NIST × 2,
  GitHub Pages × 2 further pages, and Ksa × 4 — all of which were last quote-checked in earlier passes only.

This session's original task letters AF–AI collided with theirs and were re-lettered to AJ–AL at 10:31Z.
Both of their board rows are preserved in full; nothing of either session's work was discarded.

---

## 2. Sources quote-checked this session

| # | Source | Sentence the repository relies on | Text returned this session | Result |
| --- | --- | --- | --- | --- |
| 1 | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) | Statistics are not downloadable | "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats" (chunk 0 of 2) | Confirmed |
| 2 | [NBA Official Injury Report 2026-27](https://official.nba.com/nba-injury-report-2026-27-season/) | Reporting deadlines; continual updates | "By 5 p.m. local time the day before a game (other than the second day of a back-to-back) …"; "For the second game of a back-to-back, teams must report the above information by 1 p.m. local time on the day of the game."; "In addition, teams are required to submit a game-day injury report between 11 a.m. and 1 p.m. local time (and between 8 and 10 a.m. for tip-offs 5 p.m. or earlier)"; "Reports are updated on a continual basis throughout the day." | Confirmed verbatim |
| 3 | [Same page, dated report list](https://official.nba.com/nba-injury-report-2026-27-season/) | The published 04:30 AM snapshot is the newest report listed for 14 Nov | The November 14 list runs 12:00 a.m. … 4:30 a.m. ET and stops at the [4:30 a.m. PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf) (read ~10:26 UTC) | Confirmed — the published snapshot was the newest listed at fetch time |
| 4 | [Injury Report PDF 2026-11-14 04:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf) | Document identity and row count | Header "Injury Report: 11/14/26 04:30 AM"; 49 rows across three page-tables (17 + 17 + 15) | Confirmed |
| 5 | [2026-27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | Header and window rows | "2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE"; rows 231–252 read in chunks 1 and 2 | Confirmed |
| 6 | [Same PDF, column header](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | `LOCAL` / `ET` columns | Header row: "GAME \| DAY \| DATE \| TEAM 1 \| TEAM 2 \| LOCAL \| ET \| NAT TV \| R \| #" (chunk 0) | Confirmed — the header *is* printed |
| 7 | [Same PDF, out-of-window rows](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | Rows 253–257 excluded | "253 \| Tue. \| 11/17/26 \| New York \| Toronto \| 7:30 PM \| 7:30 PM" … "257 \| Tue. \| 11/17/26 \| Utah \| LA Clippers \| 8:00 PM \| 11:00 PM" (chunk 2) | Confirmed, but see flag **AJ-02** |
| 8 | [scikit-learn — probability calibration](https://scikit-learn.org/stable/modules/calibration.html) | A lower Brier loss does not necessarily mean better calibration | "A lower Brier loss, for instance, does not necessarily mean a better calibrated model, it could also mean a worse calibrated model with much more discriminatory power"; and "assess calibration (reliability) and discriminative power (resolution) of a model, as well as the randomness of the data (uncertainty) at the same time" | Confirmed verbatim |
| 9 | [scikit-learn — cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) §3.1.2.6 | Evaluate on future observations | "it is very important to evaluate our model for time series data on the “future” observations least like those that are used to train the model."; §3.1.3: "shuffling the data will likely lead to a model that is overfit and an inflated validation score" (chunk 6 of 8) | Confirmed verbatim |
| 10 | [scikit-learn — model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) §3.4.1 | Brier is a strictly consistent scoring function for the mean | "For classification **strictly proper scoring rules** … coincide with strictly consistent scoring functions"; table row "mean \| Brier score \| multi-class \| `predict_proba`"; footnote "The Brier score is just a different name for the squared error in case of classification with one-hot encoded targets." (chunk 0 of 23) | Confirmed verbatim |
| 11 | [scikit-learn — brier_score_loss](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html) | Brier is a strictly proper scoring rule | "The Brier score is a strictly proper scoring rule." | Confirmed verbatim |
| 12 | [NIST — glossary](https://www.itl.nist.gov/div898/handbook/glossary.htm) | Correlation definition and range | "Correlation is a measure of the strength of the (usually linear) relationship between two variables. The usual correlation coefficient, called the Pearson correlation coefficient, ranges from -1 to 1." (chunk 3 of 16) | Confirmed verbatim |
| 13 | [NIST — bootstrap plot](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) | Bootstrap estimates uncertainty; caveats | "The bootstrap … plot is used to estimate the uncertainty of a statistic."; subsamples "typically between 500 and 1000"; "The bootstrap is not appropriate for all distributions and statistics" | Confirmed verbatim |
| 14 | [GitHub Pages — limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) | No commercial SaaS/online business; build rate | "GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your online business, e-commerce site, or any other website that is primarily directed at either facilitating commercial transactions or providing commercial software as a service (SaaS)."; "GitHub Pages sites have a _soft_ limit of 10 builds per hour." | Confirmed verbatim |
| 15 | [GitHub Pages — what is](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | Visitor IP addresses are logged (flag T-03) | "When a GitHub Pages site is visited, the visitor's IP address is logged and stored for security purposes, regardless of whether the visitor has signed into GitHub or not." | Confirmed verbatim |
| 16 | [GitHub Pages — creating a site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) | Static-only hosting; entry file (flags IR-01/V4-01) | Note: "GitHub Pages does not support server-side languages such as PHP, Ruby, or Python."; "GitHub Pages will look for an `index.html`, `index.md`, or `README.md` file as the entry file for your site."; "It can take up to 10 minutes for changes to your site to publish after you push the changes to GitHub." | Confirmed verbatim (IR-01/V4-01 stands as a false positive: the sentence is on this page exactly as cited) |
| 17 | [Ksa — Remote Gambling Act](https://kansspelautoriteit.nl/remote-gambling-act-force) | Licence required for online gambling in NL | "In order to do so, operators need a licence from the Netherlands Gambling Authority (Kansspelautoriteit, Ksa)." | Confirmed verbatim |
| 18 | [Ksa — 10 tips](https://kansspelautoriteit.nl/10-tips-gambling-safely) | Variance/chance cannot be removed | Tip 4: "Keep in mind that, on average, you will end up losing more than you win."; Tip 8: "Winning or losing is almost always determined by coincidence or chance, not by your insight or practice, and certainly not by superstition" | Confirmed verbatim |
| 19 | [Ksa — advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) | No licence, no advertising; page is a summary | "heeft u geen vergunning van de Kansspelautoriteit … Dan mag u in het geheel geen reclame maken"; "Deze informatie is een samenvatting van de geldende regelgeving"; "de tekst in wet- en regelgeving is leidend" | Confirmed verbatim (Dutch) |
| 20 | [Same page, external host](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) | The official page links to a non-`kansspelautoriteit.nl` host (flags V-01 / V4-07) | The page links bonus rules to `https://prod.kansspelautoriteit.hosted-temp.com/eisen-bonussen` | Confirmed present — the flag stands; the repository does not cite that host |
| 21 | [Ksa — affiliate websites](https://kansspelautoriteit.nl/ksa-attendeert-affiliatewebsites-op-regels-voor-reclame-kansspelen) | Affiliates are also in breach without a licence | "er alleen reclame mag worden gemaakt voor gokbedrijven met een vergunning"; "Als die vergunning er niet is, is niet alleen de illegale aanbieder, maar ook de affiliatewebsite in overtreding." | Confirmed verbatim (Dutch) |

**Not re-verified — recorded honestly.** [NBA.com Terms of Use](https://www.nba.com/termsofuse) returned
**HTTP 502 Bad Gateway on five attempts** during this session (10:24, 10:25, 10:26, 10:31 and 10:33 UTC), so
§1 and §9 were **not** re-read. This session does **not** assert them as newly verified. The verbatim clause
quotations already in the repository were quote-checked by earlier passes and are preserved as history
(see flags AA-01 and P6-03). The rights gate (G0) that blocks every pick therefore rests on those earlier
readings, not on this session's. See flag **AJ-03**.

---

## 3. Engine and repository checks re-run

- `python3 scripts/check_site.py --with-tests` — **PASS**: 11 pages, 332 HTML data rows, 586 Markdown data rows, engine unit tests OK. Script: [`check_site.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py).
- `python3 -m unittest discover -s tests -t .` — **OK**, 101 tests (47 in [`test_engine.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine.py) + 43 in [`test_engine_models.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine_models.py) + 11 in [`test_snapshots.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_snapshots.py)).
- `python3 scripts/build_snapshots.py --check` — slate.html and injuries.html unchanged after this session's edit to the JSON note ([`build_snapshots.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/build_snapshots.py)).
- `python3 scripts/run_pipeline.py --inputs data/inbox-example --out … --now 2026-11-14T12:00:00Z` — 2 synthetic events, `rights cleared: False`, 0 forecasts, 0 picks, append-only ledger written ([`pipeline.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py)).
- Structural audit (this session): every page has exactly one `<h1>`; every HTML table data row carries a source link — 0 missing across 332 rows.
- Published-value audit (this session): originated-line, fair-probability and impact-estimate cells are empty on both observation tables; no numeric NBA or model value is published.

---

## 4. Independent re-derivation of the published official rows

Re-read from the primary PDFs during this session and compared field by field with `data/snapshots/`. This is a
cross-check of session `arena/b9938e48-nba4`'s comparison, not a new claim.

- **Schedule, 22/22 rows agree.** Rows 231–252 of the official [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) match `slate-2026-11-14.json` on date, weekday, both printed tip columns and team order.
- **Injury report, 49/49 rows agree.** All 49 rows of the [04:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf) match `injuries-2026-11-14-0430am.json` on team, player, status and reason, including the `NOT YET SUBMITTED` reporting states and the single lost team cell (`Traore, Nolan`), which remains blank and flagged.
- **Cross-source corroboration.** The injury PDF labels its own tip column `(ET)`. For all 14 matchups present in both documents, the report's `(ET)` time equals the schedule PDF's second column exactly (DEN@NOP 07:00 / 7:00 PM, DAL@CLE 07:30 / 7:30 PM, … OKC@SAC 09:00 / 9:00 PM). Two independent official documents therefore agree that the second printed column is Eastern time.
- **Q21 recomputed independently with IANA time zones** (not taken from the other session's result): for each of the 22 rows the printed local time was converted to ET under (a) the home venue's zone and (b) the away team's zone, then compared with the printed ET value.

| Reading | Rows consistent | Result | Official source |
| --- | --- | --- | --- |
| Home-venue local time → ET | 22 / 22 | Confirms the `LOCAL` column is the home-venue local tip time | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Away-team local time → ET | 7 / 22 | Confirms the away reading does **not** hold; the 7 rows are those where both teams share a zone (e.g. Detroit at Miami, Chicago at Minnesota, Phoenix at Denver) | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |

This reproduces session `arena/b9938e48-nba4`'s figures (22/22 and 7/22) exactly. No change required — flag
**AJ-01**, informational corroboration only.

---

## 5. Engine-math spot-check (independent of the test suite)

The repository's own 101 tests were supplemented with 19 hand-computed values this session, exercising the
functions as a caller would rather than through their own assertions. **19/19 agree.**

| Function | Hand-computed check | Result | Source |
| --- | --- | --- | --- |
| `correlation.pearson` | perfect +1 / −1; `x=[1,2,3], y=[2,4,7]` → 0.9933992677987827 | Pass | [engine/correlation.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| `correlation.spearman` | reversed ranks → −1 | Pass | [engine/correlation.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| `correlation.phi` | balanced 2×2 → 0; `[[2,0],[1,1]]` → 2/√12 | Pass | [engine/correlation.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| `correlation.shrink` | w=0 → estimate; w=1 → prior; w=0.5 → midpoint | Pass | [engine/correlation.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| `lineorigination.fair_decimal_price` | p=0.5 → 2.00; p=0.8 → 1.25 | Pass | [engine/lineorigination.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| `lineorigination.net_edge` | p=0.5 at 2.10 → 0.05 | Pass | [engine/lineorigination.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| `lineorigination.margin_of_two_way` | 1.90/1.90 → 0.052631578947368 | Pass | [engine/lineorigination.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| `lineorigination.devig_two_way` | 1.90/1.90 → 0.5/0.5; 1.50/2.50 → 0.625/0.375; both sum to 1 | Pass | [engine/lineorigination.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| `validation.brier_score` | perfect → 0; inverted → 1; `[0.6,0.4]` on `[1,0]` → 0.16 | Pass | [engine/validation.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/validation.py) |

Note on scale: the engine's `brier_score` averages `(p − y)²` over binary outcomes, so it ranges 0–1. That is the
binary form scikit-learn describes as "usually divided by two" (`scale_by_half="auto"`, added in 1.7), i.e. it
matches `brier_score_loss` with its default rescaling. Recorded so a future reader does not mistake it for the
0–2 multiclass form (**AJ-05**, informational). Source: [brier_score_loss](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html).

---

## 6. Requirements-coverage map (task AK)

Each requirement in the project brief, mapped to what ships today and to what blocks it.

| # | Requirement from the brief | Ships as | Status | Blocker / note | Source |
| --- | --- | --- | --- | --- | --- |
| 1 | Collect, organise and analyze against a full requirement list | `docs/audit.md`, `docs/decision-register.md`, `questions.html` | Delivered | — | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| 2 | Originate our own NBA lines | `docs/line-origination.md`, `engine/lineorigination.py` (fair spread/total/prop, de-vig, edge) | Mechanism delivered; no line published | Needs authorised history + a market specification. Math verified (section 5) | [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| 3 | Research and develop signal-generating strategies | `docs/strategy-framework.md`, `strategies.html` | Hypotheses only | Every numeric result cell is blank and flagged; no strategy is validated | [strategy framework](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/strategy-framework.md) |
| 4 | Leaderboard competition with rewards | `leaderboard.html`, `docs/leaderboard.md`, `engine/leaderboard.py` (gate-aware, version-locked) | Design + code delivered | Rewards blocked on product classification and legal review | [Ksa advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) |
| 5 | Single bets, parlays, player-prop combos | `engine/parlay.py` (Gaussian copula, independence shortcut shown beside it), `engine/player_props.py` | Mechanism delivered | Needs licensed paired outcomes for the correlation matrix | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| 6 | Correlation values | `engine/correlation.py`, `engine/corrstats.py`, `docs/correlation-and-leaderboard.md` | Estimators delivered; all coefficients blank | No licensed sample exists | [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| 7 | Each strategy must pass validation gates | `engine/gates.py` (G0–G12), `engine/validation.py`, `docs/validation-plan.md` | Delivered | G0 (rights) and G1 (data) block by design; G12 threshold intentionally UNSET | [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| 8 | Remove luck; build selectively skill-based strategies | `docs/validation-plan.md` (walk-forward, holdout, calibration, multiple-testing control), `engine/leaderboard.py` | Framed and enforced, not achieved | "Luck-free" is not supportable — Ksa tip 8 is cited on the site | [Ksa: 10 tips](https://kansspelautoriteit.nl/10-tips-gambling-safely) |
| 9 | Generate picks for every slate up to 3 days ahead | `engine/pipeline.py` (hard 72-hour cap, freshness + rights gates, reason codes, append-only ledger), `engine/picks.py` | Pipeline delivered and tested | **Picks are blocked, not produced.** NBA Terms §9 bars NBA Statistics in connection with gambling (IR-T4 / AJ-03); every game shows reason-coded NO PICK | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| 10 | Injuries → rotation minutes and production | `engine/injuries.py`, `engine/gameflow.py`, `injuries.html` (49 verbatim rows) | Mechanism + dated official rows delivered | Minutes/production impacts blank and flagged; status is not a minutes forecast | [NBA injury policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 11 | Game-flow analysis | `engine/gameflow.py`, game-flow rows on `injuries.html` | Mechanism delivered | No calibrated pace/margin model; no historical game flow | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) |
| 12 | Executive summary | `index.html`, "Executive summary · evidence first" | Delivered | Counts audited this session (section 7) | [index.html](https://github.com/wingbangboozle1-lang/NBA4/blob/main/index.html) |
| 13 | Site-improvement suggestions + a dedicated review section | `suggestions.html`, `docs/suggestions.md`, `docs/suggestions-2c06c7f9.md`, `docs/suggestions-634f12d9.md` | Delivered | 4 gating decisions, 12 decision-queue proposals, 23 review-register proposals, 12 decision paths; the Decision column is left empty for the reviewer | [suggestions register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/suggestions.md) |
| 14 | Questions / information / answers needed before deciding; how to discover missing information | `questions.html`, `docs/decision-register.md` (Q1–Q22) | Delivered | Each question carries the known, the missing, the discovery action and an official source | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| 15 | No manual input | `scripts/run_pipeline.py`, `docs/automation.md` | Delivered | One command per cycle; the smoke run confirms 0 manual steps | [automation](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/automation.md) |
| 16 | Repo review, line by line, with links and flagged irregularities | `docs/verification-*.md` (six passes), `review.html` | Delivered | This document is pass 6b | [review page](https://github.com/wingbangboozle1-lang/NBA4/blob/main/review.html) |
| 17 | Live GitHub Pages site; clean landing page + subpages by category; dashboard UI | 11 pages, `assets/site.css`, sidebar navigation with `aria-current` | Delivered | Verified live (section 8) | [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) |
| 18 | Every table row sourced; unverifiable values blank and flagged | `scripts/check_site.py` (row-level source cell, snapshot sync, nesting audit, nav-duplication guard, test-count guard) | Delivered and enforced | 332 HTML + 586 Markdown rows checked; 0 rows missing a source | [check_site.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| 19 | Parallel-session coordination | `COORDINATION.md` | Delivered | Two collisions this session handled without discarding work (section 1) | [COORDINATION.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md) |
| 20 | PR and merge; Pages deployment | Publication record in `COORDINATION.md` | Delivered this session | See section 8 | [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |

---

## 7. Count audit of the executive summary

Numeric claims on `index.html` and `suggestions.html` were counted against the content they describe this
session: 4 gating decisions (D-1…D-4) ✓; 12 decision-queue proposals (P-01…P-12) ✓; 23 review-register
proposals (S-01…S-23) ✓; 12 decision paths (D5-14…D5-25) ✓; 101 unit tests (47 + 43 + 11) ✓; 22 games and
49 injury rows ✓. No stale count found.

---

## 8. Findings and flags

| Flag | Severity | Finding | Disposition | Source |
| --- | --- | --- | --- | --- |
| **AJ-01** | Informational | Q21 (schedule column semantics) recomputed independently with IANA time zones: home-venue reading holds 22/22, away-team reading 7/22. Reproduces `arena/b9938e48-nba4`'s figures exactly. | No change. Recorded as independent corroboration. | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| **AJ-02** | Low — documentation precision | `data/snapshots/slate-2026-11-14.json` and `slate.html` said rows 253–257 "tip off **after** 2026-11-18T00:30:00Z". Row 253 (New York / Toronto, 7:30 PM ET on 11/17) tips off *exactly* at that instant, so "after" excludes the first of them; the file's own `window.rule` field correctly says "on or after". | **Fixed** in both files this session: now "at or after 2026-11-18T00:30:00Z, past the window end of 2026-11-17T09:40:00Z", with the row-253 example given. | [schedule PDF rows 253–257](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| **AJ-03** | Medium — open | [NBA.com Terms of Use](https://www.nba.com/termsofuse) returned HTTP 502 on five attempts this session; §1/§9 could not be re-read. The rights gate rests on earlier quote-checked readings (AA-01, P6-03). | Open for the owner/counsel. Not asserted as verified by this session. | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| **AJ-04** | Informational | scikit-learn stable documentation is version **1.9.1**; all four scikit-learn quotations above were read from that build. | Matches flag P5-06; no change. | [scikit-learn 1.9.1](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| **AJ-05** | Informational | The engine's `brier_score` returns the 0–1 binary form (mean of `(p−y)²`), which is the form scikit-learn calls "usually divided by two", not the 0–2 multiclass form. | Recorded to prevent a future misreading; no code change. | [brier_score_loss](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html) |

**No NBA-derived value was added, changed or inferred by this session.** Every numeric model, correlation,
injury-impact and performance cell remains blank and flagged.

---

## 9. Deployment

Recorded in the Publication record of [`COORDINATION.md`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md).
Pages state observed during this session: 11 builds were started in the preceding hour against GitHub's
documented soft limit of 10 builds per hour, and two builds (`603e737`, and the first attempt at `ad416c4`) were
rejected with `duration: 0` — the rate-limit signature already documented on the board. Recovery followed the
recorded procedure (an empty rebuild commit), not a content change. Source: [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
