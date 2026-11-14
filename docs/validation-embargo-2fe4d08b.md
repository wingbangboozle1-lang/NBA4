# Walk-forward embargo boundary audit

**Date:** 2026-11-14 UTC · **Task:** AH · **Session:** `arena/2fe4d08b-nba4`

**Scope:** `engine.validation.walk_forward_splits` and its synthetic regression tests. This change does not train or validate an NBA model and does not change the separate count-based helper in `engine.gates`.

## Finding

Before this change, the date-based splitter subtracted `embargo_days` from the training cutoff, started the test interval at the unadjusted cutoff, and added the embargo duration to the test-window end. That shortened the training interval and put the would-be embargo dates inside a test window that was wider than the declared `test_days`.

A synthetic reproduction with daily events, `train_days=3`, `test_days=2`, and `embargo_days=2` returned training days `[0]` and test days `[3, 4, 5, 6]`. That is not a two-day gap and not a two-day test window.

## Official methodology checked

The official scikit-learn source describes `TimeSeriesSplit.gap` as the number of samples excluded from the end of a training set before the test set. Its implementation sets `train_end = test_start - gap`, uses training indices strictly before `train_end`, and begins the test slice at `test_start`. The user guide also notes that comparable time-series folds assume equally spaced samples.

| Claim used in this audit | Official-source evidence | Manual-review link |
| --- | --- | --- |
| A gap is excluded after training and before testing, rather than added to the test window. | `TimeSeriesSplit` documents `gap` as samples excluded from the end of each train set before the test set (source lines 1140–1142); `_split` computes `train_end = test_start - gap` and returns a separate test slice (lines 1295–1305). | [Pinned official scikit-learn source](https://github.com/scikit-learn/scikit-learn/blob/ee56c8b5d809dc7b970a140ed501269b63c69cf8/sklearn/model_selection/_split.py#L1140-L1142) · [split implementation](https://github.com/scikit-learn/scikit-learn/blob/ee56c8b5d809dc7b970a140ed501269b63c69cf8/sklearn/model_selection/_split.py#L1292-L1305) |
| Comparable time-series test durations assume equally spaced samples. | The official user guide states that folds should represent the same duration and that this splitter is for samples observed at fixed time intervals. | [Pinned official scikit-learn user-guide source](https://github.com/scikit-learn/scikit-learn/blob/ee56c8b5d809dc7b970a140ed501269b63c69cf8/doc/modules/cross_validation.rst#L893-L905) · [published guide](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split) |

These citations establish the gap ordering only. The source was read from the official repository using GitHub's Contents API at commit `ee56c8b5d809dc7b970a140ed501269b63c69cf8`; the pinned links allow manual review. NBA events are not claimed to be equally spaced, and this project's implementation uses calendar-day durations rather than scikit-learn's sample-count `gap`; the number of events per window can therefore vary. This is a code-design reference, not evidence that any forecast has skill.

## Change made

`engine.validation.walk_forward_splits` now:

1. rejects a negative `embargo_days` value;
2. keeps training events strictly before `train_end`;
3. omits the interval `[train_end, test_start)` as the embargo; and
4. keeps each test interval exactly `test_days` wide, beginning at `test_start`.

The helper still emits only complete test windows. With the same synthetic example after the fix, the first fold trains on days `[0, 1, 2]`, omits embargo days `[3, 4]`, and tests on `[5, 6]`.

## Verification and limits

- Reproduced the pre-fix behavior using labelled synthetic `GameEvent` fixtures; no NBA or market data was used.
- `python3 -m unittest tests.test_engine.ValidationTests -v` — **5 tests passed**, including exact boundary, chronology and negative-embargo assertions.
- A post-fix synthetic smoke check returned training days `[0, 1, 2]` and test days `[5, 6]` for the two-day embargo example.
- `python3 -m unittest discover -s tests -t . -v` — **101 tests passed**; synthetic fixtures only.
- `python3 scripts/check_site.py --with-tests` — **PASS**: 11 pages and 323 HTML rows; Markdown source-link checks and embedded engine tests passed. Its source-link check validates HTTPS/approved hosts but does not fetch URLs.
- `python3 scripts/build_snapshots.py --check` — **PASS**: both published snapshots unchanged and in sync.
- `python3 -m engine.cli status` — zero authorized inputs; the expected ledger files are absent, so the engine reports no lines or picks. `python3 -m engine.cli validate` — G4 is not run because there is no dataset or predictions.
- Synthetic-only pipeline smoke run (`--now 2026-11-14T12:00:00Z`) — 2 fixture events inside the 72-hour horizon, rights not cleared, 0 forecasts, 0 bet picks and 0 no-bet picks. Its output was written under `/tmp`, not committed.
- During verification, the checker caught that adding two separately named test methods would change the repository's public test count from 101 to 103. To avoid editing another session's README or shared overview, the regression assertions were folded into the existing chronology test; the final suite remains at 101 and the count guard passes.
- The repository has no authorized NBA feature/outcome ledger. Production validation and picks remain blocked; this code change does not change that status.
