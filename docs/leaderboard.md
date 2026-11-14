# Leaderboard competition and rewards framework

**Status: design proposal — no entries, no rankings, no rewards.** A leaderboard is a *result* of the validation gates in [`docs/validation-plan.md`](validation-plan.md), never a substitute for them. This document fixes the competition shape so that when (and only when) the G0 rights gate and G12 policy questions close, entries can compete under rules that were written **before** any result was seen. Every threshold not yet decided is left blank, by the project's no-invented-values rule.

## Competition concept

Strategy candidates (S1–S6 families from [`docs/strategy-framework.md`](strategy-framework.md)) enter as **version-locked entries**: one frozen code version + one preregistered parameter set + one declared market. Entries live in a shadow ledger first (G11), settle against official results, and only then appear on the board. "Top performing" means passing every gate and leading on the primary metric **with uncertainty** — not the largest raw backtest.

## Eligibility gates (all must pass; none optional)

| Gate | Requirement for an entry | Source / authority |
| --- | --- | --- |
| Rights & jurisdiction (G0) | Written data rights for training and outputs; legal review of the reward model in every target territory | [NBA.com Terms §9](https://www.nba.com/termsofuse#nba-statistics) · [Ksa gambling-advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) |
| Preregistration (G3) | Hypothesis, features, parameter register, baselines, primary metric and holdout frozen before the evaluation window opens | [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| Chronological evaluation (G4) | Walk-forward testing only; an untouched final holdout; feature timestamps audited for leakage | [scikit-learn time-series splits](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data) |
| Calibration & accuracy (G5) | Brier/log loss and reliability reported against baselines; a lower Brier loss alone does not prove calibration | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| Net value (G6) | Net result computed only from licensed, timestamped quotes under exact settlement rules | [NBA.com Terms §9](https://www.nba.com/termsofuse#nba-statistics) |
| Uncertainty / luck control (G7) | Game-cluster bootstrap interval on the primary metric; the interval's favourable bound must exclude zero; multiple-trials adjustment applied | [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| Combo dependence (G8) | Parlay/prop-combo entries must publish measured leg correlations (with sample counts) or declare and justify independence | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| Minimum sample (G12) | Entry must reach the preregistered settled-sample minimum. Proposed placeholder: 30 settled forecasts; **final number must come from a power/precision analysis, not from this document** | [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Integrity | No edited forecast records; all timestamps present; data rights flags valid | [NBA Injury Report policy (point-in-time discipline)](https://official.nba.com/nba-injury-report-2026-27-season/) |

## Scoring (proposed; blanks are deliberate)

| Element | Proposal | Value | Status |
| --- | --- | --- | --- |
| Primary metric | Mean proper-score improvement vs the preregistered baseline, on settled out-of-sample forecasts |  | Proposed — metric chosen per market at preregistration [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Secondary metrics | Calibration error, net result after costs (licensed quotes only), max drawdown |  | Proposed [NBA.com Terms §9](https://www.nba.com/termsofuse#nba-statistics) |
| Uncertainty display | Game-cluster bootstrap interval shown beside every score |  | Proposed [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| Trials adjustment | Bonferroni-style correction across all entries examined in a season |  | Proposed [NIST glossary](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| Ranking rule | Only gate-passing entries are ranked; ties broken by the narrower uncertainty interval, then by earlier preregistration timestamp |  | Proposed [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| Minimum sample |  |  | Blank — power analysis required (Q6) [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Confidence level |  |  | Blank — preregister before the holdout (Q6) [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| Drawdown limit |  |  | Blank — risk policy required (Q11) [Ksa safer-gambling guidance](https://kansspelautoriteit.nl/10-tips-gambling-safely) |

## Rewards (proposed tiers; nothing is offered today)

| Tier | Trigger | Reward | Status |
| --- | --- | --- | --- |
| Tier 0 — Research credit | Entry passes all gates on a frozen version | Named entry + verification badge on this board (non-monetary) | Proposed; safe default while G12 is blocked [Ksa safer-gambling guidance](https://kansspelautoriteit.nl/10-tips-gambling-safely) |
| Tier 1 — Season champion | Top primary metric among gate-passing entries at season review |  | Blank — legal review required before any inducement exists [Ksa advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) |
| Tier 2 — Improvement prize | Largest validated improvement over its own prior version |  | Blank — same blocker [Ksa affiliate guidance](https://kansspelautoriteit.nl/ksa-attendeert-affiliatewebsites-op-regels-voor-reclame-kansspelen) |

Monetary rewards, entries fees, or anything that could make this an operator/affiliate/advertising product are **blocked** until the product/jurisdiction classification (Q3/F-04) is resolved with qualified counsel. The Ksa pages are issue-spotting summaries; the underlying law controls.

## Anti-luck rules (why a hot streak cannot win)

1. Ranking requires the favourable bound of the game-cluster bootstrap interval to beat the baseline — a small-sample lucky streak's interval includes zero and cannot rank.
2. Every entry's score is reported with its sample size and window; short windows are visibly short.
3. The trials adjustment shrinks the significance bar as more entries are examined, so "try 100 strategies, publish the best" fails by construction.
4. Forecasts are locked before events; settlements use official results; corrections create new versions rather than edits ([NBA Injury Report point-in-time discipline](https://official.nba.com/nba-injury-report-2026-27-season/) is the same principle applied to injuries).
5. Past placement never guarantees future results; the board shows windows, not legends ([Ksa safer-gambling guidance](https://kansspelautoriteit.nl/10-tips-gambling-safely)).

## Current standings

Empty. No entry has passed any gate; the repository has no authorized data (G0/G1 blocked). The live table on [`leaderboard.html`](../leaderboard.html) shows the entry schema and an empty state rather than fabricated scores.

## Entry checklist (for when the blockers clear)

1. Resolve Q1 (rights) and Q3 (jurisdiction/product classification).
2. Freeze one market + one candidate strategy + the full parameter register.
3. Preregister baselines, primary metric, sample/power plan, holdout window and reward terms.
4. Run in the shadow ledger for the full preregistered window.
5. Publish only if every eligibility gate passes; otherwise keep the entry's board row blank with its failure reason.
