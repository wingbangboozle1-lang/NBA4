# Line origination: how a line is produced, and what it must not be

**Status: method specification and reference implementation. No line, price, probability or pick has been produced from NBA data.** The repository contains no authorised dataset, no market feed and no trained model, so every numeric field below is a formula or a blank cell, never an example value.

The implementation of this specification is [`engine/lineorigination.py`](../engine/lineorigination.py) and [`engine/parlay.py`](../engine/parlay.py); the tests that pin the arithmetic are in [`tests/test_engine.py`](../tests/test_engine.py).

## The one rule that shapes everything else

An **originated line** is the output of the project's own model, derived only from a predictive distribution that was estimated from an authorised dataset. It is never copied from a market, never anchored to a market price, and never rounded toward a market's price. A market quote is a separate object with its own timestamp, and any comparison between the two is a later, explicit step that also has to pass the rights and settlement gates.

This separation is what makes the output auditable. If the line were anchored to the market, "our line" would carry no independent information and the apparent edge would be an artefact of the anchoring.

## Objects in the pipeline

| Object | What it holds | Produced by | Never contains | Where implemented | Review link |
| --- | --- | --- | --- | --- | --- |
| Game score model | Expected home/away points, margin and total dispersion, model version | A team-strength model fitted on authorised history | Any market price | [`engine/lineorigination.py`](../engine/lineorigination.py) | [source on GitHub](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Player prop model | Minutes distribution, per-minute rate, their correlation, model version | A minutes x rate model fitted on authorised history | Injury status used directly as a minute adjustment | [`engine/lineorigination.py`](../engine/lineorigination.py) | [source on GitHub](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Market quote | Line, decimal price, provider, quote timestamp | A licensed price feed | Model output | [`engine/contracts.py`](../engine/contracts.py) | [source on GitHub](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/contracts.py) |
| Forecast | Model-originated line, probability, model version, input snapshot hash, emission time | The origination code | A later quote, a later injury update or the result | [`engine/contracts.py`](../engine/contracts.py) | [source on GitHub](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/contracts.py) |
| Pick | bet / no_bet decision, stake fraction, edge, reason codes | The pipeline, after the gates | An edit after settlement | [`engine/pipeline.py`](../engine/pipeline.py) | [source on GitHub](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |

## The maths, written out

For a game with expected home points `mu_h` and away points `mu_a`, and dispersion `sd_m` on the margin and `sd_t` on the total:

| Quantity | Formula | Notes | Status | Method / source link |
| --- | --- | --- | --- | --- |
| Fair spread | `mu_h - mu_a` | Home-minus-away points. Rounding to the market's published increment happens only at publication time. | Implemented, untested against NBA data | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) · [pace definition](https://www.nba.com/stats/help/glossary) |
| Fair total | `mu_h + mu_a` | The total is a separate distribution from the margin; the two are not independent in a real game. | Implemented, untested against NBA data | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) · [NBA metric definitions](https://www.nba.com/stats/help/glossary) |
| P(home covers `L`) | `1 - F_margin(-L)` | `F_margin` is the normal CDF of the model margin distribution. Away is the complement. | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| P(over `L`) | `1 - F_total(L)` | Uses the total distribution, not the margin. | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Fair decimal price | `1 / p` | No margin. This is the price at which the bet is fair, not a bookmaker quote. | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Net edge per unit staked | `p * price - 1` | Only meaningful against a licensed quote with a defined settlement rule. | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Prop line | quantile of the minutes x rate distribution (default: median) | A median line describes the centre of the predictive distribution, not the most likely single value. | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Prop probability | `1 - F_total(line)` for the over side | Uses the same distribution that produced the line. | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Joint (parlay) probability | Monte Carlo over a Gaussian copula with an estimated correlation matrix | Multiplying marginals assumes independence, which is exactly the assumption that fails for legs of one game. | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) · [NIST correlation definition](https://www.itl.nist.gov/div898/handbook/glossary.htm) |

### Why the de-vig step is declared, not assumed

A two-way quote contains the bookmaker's margin. Removing it requires choosing a method, and the method changes the comparison:

| Method | What it assumes | Implementation | Status | Method / source link |
| --- | --- | --- | --- | --- |
| Proportional (multiplicative) | The margin is spread in proportion to the implied probabilities | [`devig_two_way`](../engine/lineorigination.py) | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Additive | The margin is split evenly between the two sides | [`devig_two_way`](../engine/lineorigination.py) | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Shin | The favourite-longshot bias is present; the favourite is protected | [`_shin_devig`](../engine/lineorigination.py) | Implemented | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| Chosen method for this project | Must be written into the market specification before any comparison | Not chosen | Blocked - depends on Q5 | [market-definition question](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |

### The publish rules

1. A line is published with its probability, its model version, the input snapshot hash and the emission time. A forecast is immutable: a correction is a new version.
2. A pick is published only when the market is specified, a licensed benchmark quote exists, and every promotion gate passed. Otherwise the record is a `no_bet` with a reason code.
3. The stake fraction is a separate, declared policy. The engine returns `0.0` by design; it does not size positions on its own.
4. Nothing derived from a league statistics page is used as a model input without the written permission described in [`docs/source-verification.md`](source-verification.md) and the [NBA.com Terms of Use](https://www.nba.com/termsofuse).

## Worked example (arithmetic only, no NBA values)

The test suite pins the behaviour of the code without introducing any NBA number:

| Check | Expected behaviour | Where it is verified | Status | Source link |
| --- | --- | --- | --- | --- |
| Fair price round trip | `fair_decimal_price(0.25) == 4.0` and `net_edge(0.25, 4.0) == 0.0` | [`tests/test_engine.py`](../tests/test_engine.py) | Passing | [test source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine.py) |
| Complementarity | `P(home covers) + P(away covers) == 1` for the same line | [`tests/test_engine.py`](../tests/test_engine.py) | Passing | [test source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine.py) |
| De-vig | A 1.91/1.91 pair de-vigs to 0.50/0.50 and a positive margin | [`tests/test_engine.py`](../tests/test_engine.py) | Passing | [test source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine.py) |
| Dependence | A positively correlated pair has a joint probability above the product of marginals | [`tests/test_engine.py`](../tests/test_engine.py) | Passing | [test source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine.py) |
| Property check | A correlation matrix that is not symmetric or not positive definite fails loudly | [`tests/test_engine.py`](../tests/test_engine.py) | Passing | [test source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine.py) |

## What still blocks real lines

| Blocker | Why it stops origination | What would unblock it | Status | Source link |
| --- | --- | --- | --- | --- |
| Data rights | NBA Statistics may not be used in connection with gambling, including legal gambling, and a comprehensive regularly updated statistics database needs the Operator's express prior consent | Written permission or a licensed contract covering betting use, derivatives, storage, automation and public display | Open - P0 | [NBA.com Terms of Use](https://www.nba.com/termsofuse) · [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| Authorised history | No point-in-time game, player, lineup or injury history exists in the repository | A licensed feed with historical depth, update timestamps and correction history | Open - P0 | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Market specification | No quote source, settlement rule, push/void treatment or fee schedule is defined | One written contract per market type | Open - P1 | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Model validation | No walk-forward test, calibration check or untouched holdout exists | The procedure in [`docs/validation-plan.md`](validation-plan.md) on authorised data | Open - P1 | [scikit-learn time-series validation](https://scikit-learn.org/stable/modules/cross_validation.html) |

Until all four are closed, the origination code returns *no pick*. That is a designed outcome, not a failure of the code.
