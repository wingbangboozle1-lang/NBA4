# NBA4 line-origination and picks engine

**Three reference implementations live in `engine/` side by side.** This document covers the ratings/props/injuries/gameflow/picks subsystem (`engine/ratings.py`, `engine/player_props.py`, `engine/injuries.py`, `engine/gameflow.py`, `engine/picks.py`, `engine/corrstats.py`, `engine/gates.py`, `engine/ledger.py`, `engine/schema.py`, `engine/cli.py`). A second subsystem built by a parallel session (`engine/lineorigination.py`, `engine/parlay.py`, `engine/pipeline.py`, `engine/contracts.py`, `engine/sources.py`, `engine/correlation.py`, `engine/validation.py`, `engine/leaderboard.py`, `engine/distributions.py`) is documented in [`docs/line-origination.md`](line-origination.md), [`docs/automation.md`](automation.md) and [`docs/correlation-and-leaderboard.md`](correlation-and-leaderboard.md). Both test suites run together: `python3 -m unittest discover -s tests -t .`. Module names were disambiguated (`corrstats`, `gates`) during the parallel-session merge; no code was discarded.

**Status:** implemented and tested mechanics. **Trained/calibrated:** no. **Live output:** NO PICK — the repository has no authorized inputs and the G0 rights gate is open (see [`docs/decision-register.md`](decision-register.md) Q1/Q2 and [`docs/validation-plan.md`](validation-plan.md)). The engine exists so that the moment data rights and a licensed ledger are in place, lines, correlations and picks can be produced and validated without rewriting the pipeline — and so that nothing is ever invented to fill a gap.

## What the engine does

```
authorized inputs ledger (data/ledger/*.jsonl)
   ├─ TeamGame logs ──► engine.ratings ──► originated spread + total + margin distribution
   ├─ PlayerGame logs ► engine.player_props ► minutes x per-minute production (shrinkage)
   ├─ InjuryObservations ► engine.injuries ► availability scenario ─┐
   ├─ SlateGame feed ─► engine.picks (horizon ≤ 72h, UTC)           │
   └─ MarketQuote (optional, licensed) ── kept separate from model ─┤
                                                                    ▼
engine.gameflow (scenario distribution) ─► engine.gates checks G1–G12
engine.corrstats (pairwise, game-cluster bootstrap) ─► parlay/prop combos
                                                                    ▼
forecast ledger (JSONL): every record immutable, timestamped, NO PICK by default
```

Run it:

```sh
python3 -m engine.cli status        # what inputs exist (honest empty state today)
python3 -m engine.cli validate      # machine-checkable gate report G0–G12
python3 -m engine.cli generate --days 3 --out picks.jsonl
python3 -m engine.cli selftest      # SYNTHETIC fixture demo, stdout only
python3 -m unittest discover -s tests -v
```

## What the engine refuses to do

1. **Invent values.** Missing inputs produce `NO PICK` records with reason codes; blank means "not measured", never zero (enforced in `engine/schema.py`, `engine/picks.py`).
2. **Accept unprovenanced rows.** Every ledger record must carry an official `https://` source URL, a `source_time` and an `observed_at`; `engine/ledger.py` rejects anything else (gate G1).
3. **Leak synthetic data into production.** Fixture rows use the reserved host `synthetic.invalid`, which `load_ledger()` strips unless `allow_synthetic=True` (tests/selftest only).
4. **Use the future.** Ratings and props only consume games strictly before the forecast timestamp (`engine/ratings.py`, `engine/player_props.py`).
5. **Declare ELIGIBLE/winners.** `PickRecord.status` is `NO PICK` or `SHADOW` until every gate passes on frozen data; the current run can never emit `ELIGIBLE`.
6. **Assume parlay independence.** Same-game legs require a measured joint probability (`G8`); cross-game legs may multiply marginals only when the legs share no game (`engine/picks.py::parlay_record`).

## Module map and method

| Module | Method | Official method reference |
| --- | --- | --- |
| `engine/ratings.py` | Recency-decayed points-per-possession team strength; observed possessions × matchup PPP total (no pace imputation); predictive margin distribution; empirical pre-as-of home-win-rate anchor (no free home intercept); P(win)/P(cover) via normal approximation | [NBA Stats glossary (pace, possessions)](https://www.nba.com/stats/help/glossary) · [scikit-learn time-series evaluation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data) |
| `engine/player_props.py` | Minutes mean (clamped) × shrunk per-minute rate; empirical-Bayes shrinkage toward a population baseline; prop over/under probability | [NBA Stats glossary (MIN)](https://www.nba.com/stats/help/glossary) · [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| `engine/injuries.py` | Report status → availability scenario → minutes multiplier, three separate steps; unknown status ⇒ `UNRESOLVED` ⇒ pick suppression | [NBA Official Injury Report policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| `engine/gameflow.py` | Margin-threshold scenarios (competitive / moderate / separation) from the predictive distribution; scenario-averaged starter-minutes multiplier | [NBA Stats glossary (pace)](https://www.nba.com/stats/help/glossary) |
| `engine/corrstats.py` | Pearson correlation of pregame residuals; phi + direct joint rate for binary legs; game-cluster bootstrap intervals; shrink-toward-zero rule | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) · [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| `engine/gates.py` | Brier score, log loss, reliability bins, walk-forward folds, cluster-bootstrap skill comparison, Bonferroni trials adjustment, G0–G12 gate report | [scikit-learn Brier/calibration](https://scikit-learn.org/stable/modules/calibration.html) · [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| `engine/estimators.py` | Independent matchup-PPP and point-differential margin estimates; absolute disagreement is primary, arithmetic mean is secondary; research-only and unvalidated | [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) · [time-series validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| `engine/picks.py` | ≤3-day horizon filter (UTC), originated line + probability records, NO PICK suppression, parlay builder | [NBA schedule PDF (dated reference)](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) · [scikit-learn evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |

## Parameter register (all UNFITTED / PROPOSED)

These constants are engineering defaults so the code runs deterministically. They are **not** estimates about the NBA, none of them has been fitted or validated, and every one must be calibrated on authorized data and preregistered before a real forecast is issued.

| Parameter | Default | Where | Basis |
| --- | --- | --- | --- |
| Recency half-life | 30 days | `engine/ratings.py` | UNFITTED default; to be selected on development data only [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| Home advantage | Derived from observed pre-as-of home-win rate and UNFITTED margin SD using a normal quantile; no caller-supplied intercept | `engine/ratings.py` | Experimental transform, not a causal or validated NBA estimate; requires unique completed home results; extreme 0/1 rates suppress lines [model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Predictive margin sd | 12.0 points | `engine/ratings.py` | UNFITTED; replace with residual sd once authorized residuals exist [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| Minimum games per team/prop | 5 | `engine/ratings.py`, `engine/player_props.py` | PROPOSED, UNVALIDATED and not approved for production (IR-08); final minimum must come from a power/precision plan [scikit-learn evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Minimum settled forecasts (G12) |  | `engine/gates.py` | UNSET; only a preregistered power/precision policy may supply it; CLI output reports UNSET by default [scikit-learn evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| Shrinkage prior weight | 10 game clusters / 8 games | `engine/corrstats.py`, `engine/player_props.py` | PROPOSED fixed rule; must be preregistered [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| Injury status → availability/minutes | Out 0.0 / Doubtful 0.25 / Questionable 0.5 / Probable 0.9 / Available 1.0 (avail); 0 / 0.4 / 0.7 / 1.0 / 1.0 (minutes) | `engine/injuries.py` | PROPOSED, UNVALIDATED scenario mapping; the report status is an observation, not a minutes projection [NBA Injury Report](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Game-flow thresholds | competitive \|margin\| ≤ 5; separation \|margin\| ≥ 12 | `engine/gameflow.py` | PROPOSED scenario definitions; to be preregistered [NBA glossary](https://www.nba.com/stats/help/glossary) |
| Bootstrap repetitions / alpha | 1000 / 0.05 | `engine/corrstats.py`, `engine/gates.py` | Common default; report as an estimate, not a guarantee [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| Trials adjustment | Bonferroni | `engine/gates.py` | PROPOSED multiple-comparison control [scikit-learn evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |

## Inputs (the authorized ledger)

When (and only when) Q1/F-01 data rights are cleared, place JSONL files under `data/ledger/`:

| File | Record | Required provenance | Note |
| --- | --- | --- | --- |
| `games.jsonl` | TeamGame: game id/date, team, opponent, home flag, points, opp points, possessions | source_url, source_time, observed_at per row | Historical results from a licensed feed only [NBA.com Terms §9](https://www.nba.com/termsofuse#nba-statistics) |
| `players.jsonl` | PlayerGame: minutes, points, rebounds, assists | per row | Player-level history; never scraped from NBA Stats [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| `injuries.jsonl` | InjuryObservation: report_time, status, reason | per row | Point-in-time snapshots; later versions supersede but never overwrite [NBA Injury Report](https://official.nba.com/nba-injury-report-2026-27-season/) |
| `slate.jsonl` | SlateGame: tip_time, home, away | per row | Live authorized schedule, not the dated PDF [NBA schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| `quotes.jsonl` | MarketQuote: market, side, line, price, quoted_at, settlement_rule | per row | Licensed price feed only; kept separate from model output [NBA.com Terms §9](https://www.nba.com/termsofuse#nba-statistics) |

`python3 -m engine.cli status` prints exactly which files are missing — that list is the site's "Slate input status" table.

## Synthetic fixtures policy

`tests/` and `engine/selftest.py` fabricate two fictional teams (`SYNTH-H`/`SYNTH-A`) and one fictional player (`SYNTH-PLAYER`) to prove mechanics end-to-end. Every fixture row points at `https://synthetic.invalid/fixture`; `load_ledger()` filters that host out of production runs. No synthetic number is published on the site or written into `data/`. The selftest banner states this in full whenever it prints.

## The two brief-gap module sets, and which to read

On 2026-11-15 two sessions implemented the same enumerated requirement items from the
brief in the same `engine/` package, without coordinating (the board row collision itself is
logged in [`COORDINATION.md`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md)).
Neither was deleted, because each is the auditable record of one session's reading and each is
covered by its own suite. The correspondence, item by item:

| Requirement item | This branch (task AP, suite `tests/test_engine_brief_gaps.py`) | Parallel branch (task AS, PR #53, suite `tests/test_engine_requirements.py`) |
| --- | --- | --- |
| Result feed with quarter scores | [`engine/resultfeed.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/resultfeed.py) — `check_line` asserts the quarter-sum identity against the printed final | [`engine/officialresults.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/officialresults.py) — `verify_final`, `ResultStore`, `RefreshGate`, `settle_row` |
| Injury store + consecutive diff | [`engine/injurystore.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injurystore.py) — `diff_revisions`, `status_counts` | [`engine/injurydiff.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injurydiff.py) — `ReportArchive`, `diff_reports`, `diff_consecutive` |
| Pre-registration freeze file | [`engine/prereg.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/prereg.py) | [`engine/preregistration.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/preregistration.py) |
| Tamper-evident pick-hash ledger | not built here; blocked on the absence of any published ledger | [`engine/ledger.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/ledger.py) and [`engine/publishedledger.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/publishedledger.py) — `pick_hash`, `merkle_root`, `merkle_proof` |
| Two independent estimators + disagreement headline | [`engine/dualestimate.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/dualestimate.py) — bands model-**vs-market** disagreement, which the other module does not cover | [`engine/estimators.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/estimators.md) + [`engine/confidence.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/confidence.py) — model-vs-model `Disagreement`, `band_gap`, `home_court_pin_audit` |
| Pinned home-court from measured home-win rate | [`engine/homerate.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/homerate.py) — measures the rate from the standings page's printed HOME column, then **delegates** the conversion to `ratings.home_advantage_from_win_rate` (guarded by a test that fails if the conversion is re-implemented) | [`engine/ratings.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/ratings.py) `measured_home_win_rate` (from a ledger sample) + `home_advantage_from_win_rate` (the single conversion) |
| Per-team luck z-score with noise-band veto | [`engine/luckscore.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/luckscore.py) — one-possession records | [`engine/luck.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/luck.py) — `team_luck`, `binomial_variance`, `strategy_luck_gate` |
| Travel distance from arena coordinates | [`engine/travel.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/travel.py) — rest hours, back-to-back, disruption | [`engine/rest.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/rest.py) + [`engine/venues.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/venues.py) — `great_circle_miles`, `travel_leg`, `load_coordinate_table` |
| Top-8 minutes redistribution | [`engine/minutesshare.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/minutesshare.py) | [`engine/rotations.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/rotations.py) — `redistribution`, `availability_column` |
| Market-anchored prior weighted by log-loss | [`engine/marketprior.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/marketprior.py) — `no_vig_pair`, `prior_or_refusal` | [`engine/markets.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/markets.py) — `AnchorWeights`, `_check_log_loss`, `price_parlay` |
| Parlay priced with measured rho | [`engine/parlay.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) `rho_from_feed`, `resolve_ticket` | [`engine/markets.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/markets.py) `_equicorrelated`, `hold_adjusted` |
| Playoff tie-break / seeding layer | [`engine/seallayer.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/seallayer.py) — the L.2.a chain stopping at a missing criterion | **no counterpart** — unique to this branch |
| Projection/bet surface separation | site-level here (`scripts/check_site.py`, `engine/` untouched) | [`engine/surfaces.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/surfaces.py) — `project_view`, `bet_view`, `assert_not_mixed` |
| Shared refusal type | [`engine/inputs.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/inputs.py) `MissingInput`, used by every module above | per-module error classes (`LuckError`, `RestError`, `MarketError`, …) |

What each side adds that the other does not: this branch carries the **data** the requirement
items need — `data/snapshots/results-2026-11-14.json` (quarter scores for five completed
games), `standings-2026-11-15.json` (30 rows, HOME/ROAD/OT/LAST10/STREAK),
`aggregates-2026-11-15.json`, the two `.cells.json` extractions and their generated
`cross_check` — plus the `results.html` page and the revision-diff block on `injuries.html`.
The parallel branch carries the **ledger, totals, surfaces and pacing** implementations, which
this branch never built, and no page for them.

## Verification performed

- `python3 -m unittest tests.test_estimators` — 10 additional synthetic tests pass for empirical home-rate anchoring, future exclusion, duplicate rejection, suppressed extremes, and disagreement-first output.
- `python3 -m unittest tests.test_engine_models` — 43 tests, all passing (`python3 -m unittest discover -s tests -t .` runs all 310 across six suites: 47 in tests/test_engine.py, 43 in tests/test_engine_models.py, 30 in tests/test_snapshots.py, 10 in tests/test_estimators.py, 132 in tests/test_engine_requirements.py and 48 in tests/test_engine_brief_gaps.py) (schema rejection rules, ledger provenance enforcement, future-leak guard, min-sample gates, shrinkage direction, injury resolution, game-flow partition, Pearson/phi known values, bootstrap determinism, Brier/log-loss known values, chronological folds, horizon filter, NO PICK suppression, parlay dependence rule, selftest smoke).
- `python3 -m engine.cli status` on the real repository state reports `NO AUTHORIZED INPUTS -> no lines, no picks` — the honest output the site mirrors.
- Method statements in the module map were quote-checked against their official sources in [`docs/verification-log.md`](verification-log.md) (ML-01…ML-03, STAT-01…STAT-02, NBA-03…NBA-06).

## What is still required before a real pick

Exactly the same blockers the dashboard lists: Q1 data rights, Q2 a licensed provider, G2 market/settlement definitions, G3 preregistration of the parameter register above, G4–G11 evaluation on authorized data, and the G12 leaderboard/reward policy with legal review. Until then the engine is a tested instrument standing at zero, not a source of picks.

## Task-AN modules: brief-gap machinery that refuses without inputs (2026-11-15)

Twelve modules close the gaps the audit found between the brief and the engine. They
share one discipline (`engine/inputs.py`): a number is emitted only when the official
cells it is computed from are present; otherwise the module raises
`MissingInput` or returns a refusal record with the missing input named. Fixtures in
`tests/test_engine_brief_gaps.py` (48 tests) are synthetic except where a test reads
the dated official extractions in `data/snapshots/`.

| Module | What it computes | What it refuses | Official input it needs |
| --- | --- | --- | --- |
| [`engine/inputs.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/inputs.py) | `require`, `require_min`, `official_link`, the `[NO INPUT]` sentinel | any row that would publish without an https official link | — |
| [`engine/resultfeed.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/resultfeed.py) | quarter-sum vs printed-final check per team line; day settlement gate; retrieval lag | settling a day with an unchecked or disagreeing line; inventing a missing quarter or a game-end clock | `data/snapshots/results-<date>.json` (game-summary pages) |
| [`engine/injurystore.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injurystore.py) | revision store; consecutive-revision diff (status / reason / team / name-variance) | attributing a page-break row to a team; calling a name-spelling change a status change | the official injury-report PDFs |
| [`engine/prereg.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/prereg.py) | append-only code-hash registrations; `assert_covers` before a run | overwriting a registration; a run whose code hash or timestamp is not covered | the repository commit it records |
| [`engine/seallayer.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/seallayer.py) | the L.2.a / L.2.b tie-break walk in printed order | skipping a criterion whose input is absent; ordering by anything not in the rule | the standings page's tie-break procedures |
| [`engine/dualestimate.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/dualestimate.py) | model-vs-market bands (2/5/10 pt edges), per-variant counts, mean difference | a mean below 10 compared pairs; any pair with no market side | licensed quotes for the market side |
| [`engine/homerate.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/homerate.py) | measured home-win rate from the standings HOME column; pinned point value (12.0 x Phi⁻¹(rate)) | applying the pin before pre-registration **and** rights gate G0 clear it; any per-arena or altitude term | `data/snapshots/standings-<date>.json` |
| [`engine/luckscore.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/luckscore.py) | one-possession (2-pt) close-game record over the last 10 games; exact binomial 90% band | a baseline of .500 when no forecast history exists; padding a 4-game team to 10 | completed `TeamGame` lines, possessions when printed |
| [`engine/travel.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/travel.py) | tip-to-tip rest, back-to-back flag, games-in-nights count | a count from a slate that does not cover the whole window; any penalty value from a disruption notice | schedule extraction + a named official notice |
| [`engine/minutesshare.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/minutesshare.py) | top-8 minutes share, replacement-minutes share, availability-weighted rotation | a denominator synthesised from player rows; crediting minutes to a player whose row lost its team cell | official box-score MIN lines |
| [`engine/marketprior.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/marketprior.py) | price to probability, no-vig normalisation, preregistered shrinkage | a prior where G0 has not cleared the quote; a price that is not printed | licensed quotes with `allowed_use` |
| [`engine/parlay.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) | `resolve_ticket` push/void re-pricing; `rho_from_feed` leg-pair correlation | scoring a push as a win; pricing a ticket with an unsettled leg; a rho from fewer than 20 pairs | settlement states from official results |

`engine/ratings.py` is unchanged: `HOME_ADVANTAGE_POINTS` stays `0.0` and the module
docstring's "no default parameters" rule still holds — `homerate.for_ratings` is the
only path that could hand a calibrated value to a line, and it is gated twice.
