# Site information architecture and publication specification

**Scope:** static, informational research dashboard. This document is the information-architecture specification; the eleven pages it describes are now built, plus `results.html` (task AN: official results with the printed-period settlement check, standings as printed, the derived aggregates and the per-player game logs), and the three model-surface pages of task AV/BH (`model.html`: the two estimators and the published disagreement; `availability.html`: the rotation-availability column and the minutes-share model; `ledger.html`: pre-registration and the seal/settlement stamps) — fifteen pages in all, whose sidebar navigation is the canonical list enforced by `scripts/check_site.py`. The final integration and Pages deployment are recorded in [`COORDINATION.md`](../COORDINATION.md). Publication rules below remain in force for every future change.

## User-facing promise

The landing page will state the truth immediately: the repository has no validated model or licensed point-in-time betting dataset, so no NBA picks, fair lines, probabilities, minutes, correlations, ROI, winners, or rewards are published. It will not present placeholders as predictions. Numeric model fields stay blank and receive an **Unverified / not computed** status. It will distinguish source facts from design recommendations and explain that source links are not licenses.

A prominent “not associated with the NBA” disclaimer will be included. The page will not copy NBA logos, team marks, schedule rows, injury rows, NBA statistics, odds, or player data. The [NBA.com Terms of Use](https://www.nba.com/termsofuse) restrict reuse and the use of NBA Statistics in gambling; an informational citation is not authorization. The official schedule PDF is dated “as of August 13, 2026” and “subject to change”; link to it rather than republishing the slate. Injury reporting is continually updated; link to the [NBA Official injury report](https://official.nba.com/nba-injury-report-2026-27-season/) rather than imply a static snapshot is current.

## Page categories

- **Overview (`index.html`)** — executive summary, data-rights blocker, no-picks state, what is verified vs not, and direct links to the decision register and flagged review.
- **Upcoming slate (`slate.html`)** — intended maximum-three-day horizon, but no fixtures or lines are copied while the data-rights and live-feed questions are unresolved. A source-linked empty-state explains that no slate/model output is available.
- **Injuries & game flow (`injuries.html`)** — separates official status source, expected availability, rotation minutes, production effect and game-flow scenarios. Only the first is an input fact; other columns remain blank until a validated authorized model exists.
- **Strategies & validation (`strategies.html`)** — singles, player props, parlays/combinations, injury scenarios and validation gates, each labeled as a hypothesis/not run and linked to its method/context source.
- **Questions (`questions.html`)** — a readable decision register: known fact, unknown, why it matters, suggested discovery, status and official source link.
- **Sources (`sources.html`)** — primary-source ledger with verified scope, publication/snapshot date and interpretation limits.
- **Flagged for Review (`review.html`)** — data-licensing, legal/jurisdiction, hosting, data-availability, stale-schedule, validation and reward blockers; each flag contains its official source and a specific next discovery step.
- **Line origination (`line-origination.html`)** — how a model-originated line is produced from a predictive distribution, how it is kept separate from a market quote, how a two-way price is de-vigged, and which inputs each formula needs. Every numeric cell stays blank until an authorised dataset exists.
- **Automation (`automation.html`)** — the daily, no-manual-input pipeline: the 72-hour horizon, the freshness and rights gates, the reason codes a run can emit, and the runbook that publishes the next slate.
- **Leaderboard (`leaderboard.html`)** — the gate-aware leaderboard design, the eligible-versus-ineligible rules, the declared scoring policy, and the current (empty) standings table.
- **Suggestions (`suggestions.html`)** — a dedicated review page carrying both proposal sets: the decision queue (four gating decisions and twelve prioritised proposals with options and trade-offs) and the review register (23 proposals with an empty **Decision** column for the reviewer), so the path is chosen before anything is implemented.
- **Model & estimators (`model.html`)** — the reference estimation stack: two independent estimators, the disagreement headline (the blend is arithmetic and never called confidence), the home-court value pinned to the measured home-win rate, the market-anchored prior weighted by measured out-of-sample log loss, parlay rho printed beside the naive product, and the totals model beside its naive baseline. Live model values stay blank until rights clear.
- **Availability & rotation (`availability.html`)** — the rotation-availability column the picks page must carry (blank means "not sourced", never "healthy"), the top-8 minutes-share redistribution model with caller-supplied replacement weights, and the injury → rotation → game-flow chain that stops at the first blank.
- **Ledger & seals (`ledger.html`)** — pre-registration freeze status (four sections, non-defaultable thresholds, frozen_at before the first bet), per-pick SHA-256 hashes in an append-only chain, the Merkle day seal published before tip, and the settlement stamp from verified finals. The production ledger is empty until rights clear; synthetic test fixtures are labelled as such and never stand in for a published pick.

The full written versions remain in [`docs/audit.md`](audit.md), [`docs/strategy-framework.md`](strategy-framework.md), [`docs/validation-plan.md`](validation-plan.md), [`docs/decision-register.md`](decision-register.md), [`docs/sources.md`](sources.md), [`docs/line-origination.md`](line-origination.md), [`docs/automation.md`](automation.md), [`docs/correlation-and-leaderboard.md`](correlation-and-leaderboard.md), [`docs/suggestions.md`](suggestions.md), [`docs/source-verification.md`](source-verification.md) and [`docs/verification-log.md`](verification-log.md). They are linked to the repository source view for review, not presented as live feed data.

## Table and status rules

Every data row in every site table has a final **Official source** cell linking directly to the NBA, GitHub, Ksa, NIST or project-maintainer source that supports the row. If a source only provides context, label it as context; do not imply it proves the recommendation or a model outcome. Values absent from an official/authorized source remain empty and receive a separate status/flag. Recommendations are labeled **Proposed**; empirical claims must be labeled **Verified** only after matching them to a primary source and a reproducible check.

No table may contain fabricated example picks, made-up correlations, toy odds, dummy player names, inferred injury impacts, simulated ROI, or an unsupported count. No page may turn an injury status into minutes or expected production without a separately validated method. A failure, stale feed, or unresolved injury should display **No pick / data not ready**, never a stale forecast.

## Technical and accessibility constraints

Use original, plain HTML/CSS and a small local script only if it improves accessibility or table usability; no third-party analytics, cookies, external fonts, images, user accounts, input forms, market scraping or API keys. Keep it responsive and keyboard navigable, semantic headings/tables, visible focus, adequate contrast and descriptive source-link text. Provide an accessible empty state and a no-script path.

The [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) describes Pages as static hosting without server-side code. The repo currently publishes from `main` root (confirmed by the [GitHub Pages API](https://api.github.com/repos/wingbangboozle1-lang/NBA4/pages)). Keep the site informational; if the product becomes commercial/live SaaS or facilitates transactions, [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) require a different hosting decision.

## Pre-publication checks

1. Verify each linked source URL, every table row’s official source cell, every local navigation/asset link and each page title/heading.
2. Run a local HTML/link/table check with no network-dependent build dependencies.
3. Confirm no NBA-derived schedule/stat/injury/odds values or credentials were copied into the site.
4. Publish only after all prerequisite tasks are marked done and record the PR, merge, Pages deployment status and live URL in `COORDINATION.md`.
