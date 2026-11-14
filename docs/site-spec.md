# Site information architecture and publication specification

**Scope:** static, informational research dashboard. This is a design specification only; shared navigation, index, content tables, and Pages deployment are reserved for final integration after the audit, research framework, decision register, and this spec are complete.

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
- **Suggestions (`suggestions.html`)** — a dedicated review page for proposed site improvements. Each proposal states the decision-making benefit, effort, dependency and evidence, and carries an empty **Decision** column for the reviewer, so the path is chosen before anything is implemented.

The full written versions remain in [`docs/audit.md`](audit.md), [`docs/strategy-framework.md`](strategy-framework.md), [`docs/validation-plan.md`](validation-plan.md), [`docs/decision-register.md`](decision-register.md), [`docs/sources.md`](sources.md), [`docs/line-origination.md`](line-origination.md), [`docs/automation.md`](automation.md), [`docs/correlation-and-leaderboard.md`](correlation-and-leaderboard.md), [`docs/suggestions.md`](suggestions.md) and [`docs/source-verification.md`](source-verification.md). They are linked to the repository source view for review, not presented as live feed data.

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
