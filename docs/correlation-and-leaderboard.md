# Correlation measurement and leaderboard design

**Status: measurement tools are implemented and tested; no coefficient, no ranking and no reward exists.** Every numeric cell in this document is blank on purpose. A correlation value, a leaderboard row or a prize amount that cannot be checked against an official source and a licensed dataset stays empty and flagged.

Implementation: [`engine/correlation.py`](../engine/correlation.py), [`engine/parlay.py`](../engine/parlay.py) and [`engine/leaderboard.py`](../engine/leaderboard.py).

## What "correlation" has to mean before it can be measured

A correlation is not a property of a player. It is a property of a **defined pair of legs**, on a **defined market**, within a **defined conditioning set**, over a **defined window**, computed with a **defined estimator** and a **defined data policy**. Without all six, a number is decoration.

| Element of the definition | What must be fixed | Why it changes the number | Status | Method / source link |
| --- | --- | --- | --- | --- |
| Leg pair | For example "player A points over L" and "player B rebounds over L", in the same game | A different pair is a different quantity | To be declared per pair | [correlation definition](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| Market and threshold | The market type, the line and the settlement rule | A threshold changes which observations count | Blocked by Q5 | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Conditioning set | Whether the estimate is unconditional, or conditional on game context (rest, pace bucket, opponent) | Conditioning can flip the sign of an estimate | To be preregistered | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Window | Season, date range and the point-in-time policy used to build features | An estimate computed with later information is not the estimate used in production | Blocked by Q2 | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Estimator | Pearson for continuous residuals, direct joint frequencies for binary legs, plus a cluster interval | Different estimators answer different questions | Implemented | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) · [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| Uncertainty | A game-clustered bootstrap interval and the sample count | A point estimate without an interval invites over-reading | Implemented | [NIST bootstrap plot](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |

## Estimators implemented

| Estimator | Use it for | Implementation | Verification | Source link |
| --- | --- | --- | --- | --- |
| Pearson `r` | Continuous pregame residuals (for example two players' points residuals in one game) | [`pearson`](../engine/correlation.py) | Hand-checked value and a constant-series guard in the test suite | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) · [NIST definition](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| Spearman `rho` | Rank association when the relationship is monotone but not linear | [`spearman`](../engine/correlation.py) | Tie handling and the monotone case are tested | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| Phi and Yule's Q | Two binary legs (a prop crossing a threshold) | [`phi`](../engine/correlation.py), [`yule_q`](../engine/correlation.py) | Perfect-agreement case is tested | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| Cluster bootstrap interval | Any of the above, resampling whole games | [`cluster_bootstrap_ci`](../engine/correlation.py) | The interval is checked to bracket the estimate | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) · [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| Shrinkage toward a prior | Unstable small-sample pairs | [`shrink`](../engine/correlation.py) | The rule is explicit and the weight must be preregistered | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/correlation.py) |
| Joint probability via a Gaussian copula | Parlays and prop combos | [`joint_probability`](../engine/parlay.py) | The independence case and the positively correlated case are both tested | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) |

## The measurement table (intentionally empty)

| Pair / relationship | Estimator | Value | Interval | Sample / window | Status | Source link |
| --- | --- | --- | --- | --- | --- | --- |
| Two player-stat residuals in one game | Pearson on residuals |  |  |  | Unverified - no licensed event records | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| Two binary prop legs for one player | Direct joint frequency and phi |  |  |  | Unverified - no lines or settled legs | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| Game total and a player prop | Conditional joint distribution |  |  |  | Unverified - no point-in-time predictions | [NBA metric definitions](https://www.nba.com/stats/help/glossary) |
| Teammate minutes after an absence | Conditional pair effect with lineup controls |  |  |  | Unverified - no authorised lineup or minute history | [NBA injury report](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Both teams' totals in one game | Residual correlation of the margin model |  |  |  | Unverified - no model residuals yet | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |

Blank means *unknown*. It does not mean zero and it does not mean independent.

## Why the independence assumption is the most expensive shortcut

Multiplying marginals to price a parlay is fast, and it is wrong exactly where the money is: legs of the same game share pace, margin, team quality and rotation. The engine therefore computes the joint probability directly and reports the difference against the naive product, so the size of the shortcut is visible instead of hidden.

| Quantity | How it is computed | Reported with | Source link |
| --- | --- | --- | --- |
| Joint probability | Monte Carlo over a Gaussian copula with the supplied correlation matrix | Estimate, Monte Carlo standard error, draw count and seed | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) |
| Independent approximation | Product of the marginal probabilities | Shown next to the joint estimate as a comparison | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) |
| Dependence effect | Joint estimate minus the independent approximation | Reported per combo | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) |
| Leg marginals | Taken from the model's own calibrated probability for each leg | Reported with the joint estimate | [validation guide](https://scikit-learn.org/stable/modules/calibration.html) |

## Leaderboard design

The leaderboard is a gate, not a prize for the largest backtest. Only entries that pass every declared gate are ranked, and when nothing passes, the leaderboard is empty.

| Element | Rule | Where implemented | Status | Source link |
| --- | --- | --- | --- | --- |
| Eligibility | Every required gate must have passed on a frozen strategy version; a gate the candidate does not report counts as **failed** | [`evaluate_gates`](../engine/leaderboard.py) | Implemented and tested | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/leaderboard.py) |
| Minimum sample | The policy must supply a minimum sample size; below it, an entry is not ranked | [`LeaderboardPolicy`](../engine/leaderboard.py) | Implemented; the number itself is blank | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/leaderboard.py) |
| Scoring | A weighted composite over declared metrics; the weights come from the policy and are never chosen by looking at the holdout | [`_score`](../engine/leaderboard.py) | Implemented; weights are blank | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/leaderboard.py) |
| Ranking output | Rank, strategy id, frozen model version, market, sample size, window, scores, uncertainty context, baseline comparison, correlation check | [`rank`](../engine/leaderboard.py) | Implemented | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/leaderboard.py) |
| Calibration discipline | A proper scoring rule must be read together with a reliability table, because a lower Brier loss does not by itself mean better calibration | [`reliability_table`](../engine/validation.py) | Implemented | [calibration guide](https://scikit-learn.org/stable/modules/calibration.html) |
| Multiple testing | The number of candidate variants examined must be reported; a shortlist chosen after the holdout is a failure | Process control in [`docs/validation-plan.md`](validation-plan.md) | Not run | [time-series validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| Rewards | Amount, funding, eligibility, tie handling, payment schedule and tax treatment | Not defined | Blocked - needs a risk policy and legal review | [Ksa advertising rules](https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame) · [Ksa consumer guidance](https://kansspelautoriteit.nl/10-tips-gambling-safely) |

### Leaderboard table (no entries)

| Rank | Strategy | Model version | Market | Sample | Window | Calibration | Net result | Uncertainty | Status | Source link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  | No eligible candidate - no strategy has passed a gate | [validation plan](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/validation-plan.md) |

## Luck versus skill: what can actually be claimed

| Claim | Verdict | Evidence standard | Source link |
| --- | --- | --- | --- |
| "This strategy is luck-free" | Not supportable | Random game outcomes remain; no method removes variance | [Ksa: 10 tips for gambling safely](https://kansspelautoriteit.nl/10-tips-gambling-safely) |
| "This strategy beats the market" | Not supportable yet | Requires a licensed, timestamped benchmark, a walk-forward test and an untouched holdout | [scikit-learn time-series validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| "This strategy is calibrated" | Not supportable yet | Requires a reliability table and a proper score on out-of-sample data | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| "These two props are correlated" | Not supportable yet | Requires a defined pair, a licensed sample, a cluster interval and a holdout check | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| "This forecast had no leakage" | Testable and mechanically checked | The engine compares every input's observation time with the forecast time | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/validation.py) |
| "This run used fresh data" | Testable and mechanically checked | The engine rejects inputs older than the declared tolerance | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
