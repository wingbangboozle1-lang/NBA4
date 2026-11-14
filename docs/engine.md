# NBA4 line-origination and picks engine

**Two reference implementations live in `engine/` side by side.** This document covers the ratings/props/injuries/gameflow/picks subsystem (`engine/ratings.py`, `engine/player_props.py`, `engine/injuries.py`, `engine/gameflow.py`, `engine/picks.py`, `engine/corrstats.py`, `engine/gates.py`, `engine/ledger.py`, `engine/schema.py`, `engine/cli.py`). A second subsystem built by a parallel session (`engine/lineorigination.py`, `engine/parlay.py`, `engine/pipeline.py`, `engine/contracts.py`, `engine/sources.py`, `engine/correlation.py`, `engine/validation.py`, `engine/leaderboard.py`, `engine/distributions.py`) is documented in [`docs/line-origination.md`](line-origination.md), [`docs/automation.md`](automation.md) and [`docs/correlation-and-leaderboard.md`](correlation-and-leaderboard.md). Both test suites run together: `python3 -m unittest discover -s tests -t .`. Module names were disambiguated (`corrstats`, `gates`) during the parallel-session merge; no code was discarded.

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
| `engine/ratings.py` | Recency-decayed points-per-possession team strength; predictive margin distribution (mean, sd); fair spread = expected margin; P(win)/P(cover) via normal approximation | [NBA Stats glossary (pace, possessions)](https://www.nba.com/stats/help/glossary) · [scikit-learn time-series evaluation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data) |
| `engine/player_props.py` | Minutes mean (clamped) × shrunk per-minute rate; empirical-Bayes shrinkage toward a population baseline; prop over/under probability | [NBA Stats glossary (MIN)](https://www.nba.com/stats/help/glossary) · [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| `engine/injuries.py` | Report status → availability scenario → minutes multiplier, three separate steps; unknown status ⇒ `UNRESOLVED` ⇒ pick suppression | [NBA Official Injury Report policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| `engine/gameflow.py` | Margin-threshold scenarios (competitive / moderate / separation) from the predictive distribution; scenario-averaged starter-minutes multiplier | [NBA Stats glossary (pace)](https://www.nba.com/stats/help/glossary) |
| `engine/corrstats.py` | Pearson correlation of pregame residuals; phi + direct joint rate for binary legs; game-cluster bootstrap intervals; shrink-toward-zero rule | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) · [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| `engine/gates.py` | Brier score, log loss, reliability bins, walk-forward folds, cluster-bootstrap skill comparison, Bonferroni trials adjustment, G0–G12 gate report | [scikit-learn Brier/calibration](https://scikit-learn.org/stable/modules/calibration.html) · [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| `engine/picks.py` | ≤3-day horizon filter (UTC), originated line + probability records, NO PICK suppression, parlay builder | [NBA schedule PDF (dated reference)](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) · [scikit-learn evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) |

## Parameter register (all UNFITTED / PROPOSED)

These constants are engineering defaults so the code runs deterministically. They are **not** estimates about the NBA, none of them has been fitted or validated, and every one must be calibrated on authorized data and preregistered before a real forecast is issued.

| Parameter | Default | Where | Basis |
| --- | --- | --- | --- |
| Recency half-life | 30 days | `engine/ratings.py` | UNFITTED default; to be selected on development data only [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| Home advantage | 0.0 points | `engine/ratings.py` | UNFITTED; deliberately neutral until calibrated [NBA glossary](https://www.nba.com/stats/help/glossary) |
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

## Verification performed

- `python3 -m unittest tests.test_engine_models` — 43 tests, all passing (`python3 -m unittest discover -s tests -t .` runs all 90) (schema rejection rules, ledger provenance enforcement, future-leak guard, min-sample gates, shrinkage direction, injury resolution, game-flow partition, Pearson/phi known values, bootstrap determinism, Brier/log-loss known values, chronological folds, horizon filter, NO PICK suppression, parlay dependence rule, selftest smoke).
- `python3 -m engine.cli status` on the real repository state reports `NO AUTHORIZED INPUTS -> no lines, no picks` — the honest output the site mirrors.
- Method statements in the module map were quote-checked against their official sources in [`docs/verification-log.md`](verification-log.md) (ML-01…ML-03, STAT-01…STAT-02, NBA-03…NBA-06).

## What is still required before a real pick

Exactly the same blockers the dashboard lists: Q1 data rights, Q2 a licensed provider, G2 market/settlement definitions, G3 preregistration of the parameter register above, G4–G11 evaluation on authorized data, and the G12 leaderboard/reward policy with legal review. Until then the engine is a tested instrument standing at zero, not a source of picks.
