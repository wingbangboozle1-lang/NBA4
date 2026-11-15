# Independent estimators and disagreement-first reporting

## Status

**Research implementation only.** No authorized NBA game ledger is present, no estimator has been fitted or evaluated on real NBA data, and the code cannot authorize a pick. The NBA data-rights gate remains closed. Synthetic fixtures in `tests/test_estimators.py` demonstrate arithmetic and input controls only; their values are not NBA observations.

The modeling objective is to publish the absolute difference between two independently constructed margin forecasts as the **primary disagreement signal**. The arithmetic mean is reported only beneath it as a secondary summary. Disagreement is measured in points; it is not a probability, calibrated confidence score, or evidence of skill. Each method must be separately evaluated on chronological, untouched data before any production use. The official scikit-learn guidance says to choose a scoring function aligned with the prediction target and use it for both evaluation and model comparison ([model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html)); for temporal data, its documentation describes time-aware cross-validation ([cross-validation of time-series data](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data)).

## Two estimators

| Output | Definition | Current status / required evidence | Method reference |
| --- | --- | --- | --- |
| Estimator A | Existing recency-weighted points-per-possession matchup estimate, using the team's offense against the opponent's defense relative to league average. | UNFITTED; requires authorized possession and completed-game data, out-of-sample residual analysis, and rights clearance. | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) · [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Estimator B | Separate baseline: half the difference in each team's pre-as-of mean point differential, plus the same measured home-rate anchor. | UNFITTED and deliberately simple; validate independently against baseline A and a declared market benchmark on chronological folds. | [scikit-learn time-series cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data) |
| Primary headline | `abs(Estimator A - Estimator B)`, in points. | No NBA value is available. Lower disagreement means only that these two methods are closer on that event; it does not establish correctness or skill. | [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Possessions used for the total | Recency-weighted mean of recorded pre-as-of possessions; expected team points are possessions × matchup PPP. | Missing/nonpositive possessions are skipped; if either team or the league lacks enough eligible records, the line remains blank. No fixed 100-possession substitute is used. | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) · [NBA.com Terms](https://www.nba.com/termsofuse) |
| Secondary summary | Arithmetic mean of A and B, only when both exist. | Not promoted to a primary rating; do not call it confidence or use it for a pick until separately validated. | [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Home-rate anchor | Count unique completed home-team game rows dated strictly before forecast time; compute observed home wins / observed home games. Derive a point equivalent as `NormalDist().inv_cdf(rate) × margin_sd`, with no freely entered home-advantage coefficient. | UNFITTED mapping assumption; empirical rate, count, and margin SD must be exposed. A 0% or 100% rate yields no finite value and suppresses both margins; it is not clipped. Validate the normal-margin transformation on authorized data. | [NBA.com Terms](https://www.nba.com/termsofuse) (rights gate) · [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |

The current margin SD remains an explicitly **UNFITTED** engineering default. Thus the point-equivalent home anchor is still an experimental transform, not a measured causal points effect. It is an explicit limitation and must not be represented as a validated NBA estimate.

## Integrity rules

- Ignore every game at or after `as_of`; duplicate home-team records for one game are rejected.
- A missing estimator, insufficient sample, missing measured home rate, or an extreme empirical rate leaves the headline and blend blank. Do not silently substitute zero or clip rates.
- Do not compare models on the same training outcomes used to fit them. Lock the strategy/version, evaluate chronologically, report both estimators' losses and the disagreement distribution, and include uncertainty and sample counts.
- Keep market quotes separate. Any market-anchored prior must be preregistered and tested without future closing-line leakage.
- Rights and permitted use must be established before ingesting or publishing NBA-derived inputs. See [NBA Stats FAQ](https://www.nba.com/stats/help/faq) and [NBA.com Terms](https://www.nba.com/termsofuse).

## Files and checks

- Implementation: `engine/ratings.py`, `engine/estimators.py`.
- Synthetic unit tests: `tests/test_estimators.py`.
- Run `python3 -m unittest tests.test_estimators` and `python3 -m unittest discover -s tests -t .`.
- The site and existing snapshot tables remain unchanged; the estimator results are not published as NBA numbers.
