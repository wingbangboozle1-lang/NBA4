# NBA4 — NBA line research dashboard

**Live site:** [https://wingbangboozle1-lang.github.io/NBA4/](https://wingbangboozle1-lang.github.io/NBA4/) (GitHub Pages publishes from `main` at the repository root; the deployment is re-checked after every merge.)

## Current status

This repository contains an evidence-first research plan **and a working reference engine** for it: data contracts with a hard rights gate, model-originated fair lines and prices, de-vigging, parlay/prop-combo joint probabilities, correlation estimators with game-cluster bootstrap intervals, validation metrics, a gate-aware leaderboard, and a three-day slate pipeline with an append-only ledger. The engine ships with synthetic fixtures and 90 passing unit tests (47 + 43, both suites); it contains **no NBA or market data**, no trained model and no published pick.

The blocking issue is still data rights, not code. NBA's Stats FAQ states its statistics are "not available for download for either academic or personal use", and NBA.com's Terms of Use restrict NBA Statistics to "legitimate news reporting or private, non-commercial purposes" and state they "may not be used in connection with any gambling activity (including legal gambling activity)", nor with a "database ... of comprehensive, regularly updated statistics" without the Operator's express prior consent. No NBA statistics, player data, team data, odds or schedule rows have been added, and the engine refuses any record whose permission flag is not set. Obtain written permission or a licensed contract, plus legal review of the product and rewards, before a betting model or public picks are considered.

## Dashboard sections

- [Overview and executive summary](https://wingbangboozle1-lang.github.io/NBA4/)
- [Upcoming slate status](https://wingbangboozle1-lang.github.io/NBA4/slate.html)
- [Injuries, rotation and game flow](https://wingbangboozle1-lang.github.io/NBA4/injuries.html)
- [Line origination](https://wingbangboozle1-lang.github.io/NBA4/line-origination.html)
- [Automation and the three-day pipeline](https://wingbangboozle1-lang.github.io/NBA4/automation.html)
- [Strategies and validation gates](https://wingbangboozle1-lang.github.io/NBA4/strategies.html)
- [Leaderboard and correlation values](https://wingbangboozle1-lang.github.io/NBA4/leaderboard.html)
- [Decision questions and missing information](https://wingbangboozle1-lang.github.io/NBA4/questions.html)
- [Suggestions and decision queue](https://wingbangboozle1-lang.github.io/NBA4/suggestions.html)
- [Verified source register](https://wingbangboozle1-lang.github.io/NBA4/sources.html)
- [Flagged for Review](https://wingbangboozle1-lang.github.io/NBA4/review.html)

## Reference engine

| Module | Responsibility |
| --- | --- |
| [`engine/contracts.py`](engine/contracts.py) | Data contracts, provenance, the rights gate and the leakage check |
| [`engine/lineorigination.py`](engine/lineorigination.py) | Fair spread/total/prop lines, fair prices, de-vigging and edge |
| [`engine/parlay.py`](engine/parlay.py) | Joint probability for parlays and prop combos (Gaussian copula) |
| [`engine/correlation.py`](engine/correlation.py) | Pearson/Spearman/phi estimators, game-cluster bootstrap interval, shrinkage |
| [`engine/validation.py`](engine/validation.py) | Brier, log loss, reliability bins, walk-forward splits, coverage, net return |
| [`engine/leaderboard.py`](engine/leaderboard.py) | Gate evaluation and ranking of eligible, version-locked candidates |
| [`engine/pipeline.py`](engine/pipeline.py) | Three-day horizon, freshness/rights gates, pick decisions, append-only ledger |
| [`engine/sources.py`](engine/sources.py) | The verified source registry used by the documents and the site |
| [`scripts/run_pipeline.py`](scripts/run_pipeline.py) | Command-line entry point for one pipeline cycle |
| [`tests/test_engine.py`](tests/test_engine.py) | 47 unit tests over synthetic fixtures (pipeline, contracts, leakage and gates) |

A second model-side subsystem from session `arena/2c06c7f9-nba4` lives alongside it (module names disambiguated during the parallel-merge; nothing discarded). Full guide: [`docs/engine.md`](docs/engine.md).

| Module | Responsibility |
| --- | --- |
| [`engine/ratings.py`](engine/ratings.py) | Recency-weighted team strength; originated spread/total distributions; win/cover probabilities |
| [`engine/player_props.py`](engine/player_props.py) | Minutes × shrunk per-minute production prop distributions |
| [`engine/injuries.py`](engine/injuries.py) | Status → availability scenario → minutes multiplier (separate, unvalidated steps) |
| [`engine/gameflow.py`](engine/gameflow.py) | Margin-threshold game-flow scenarios and minutes conditioning |
| [`engine/picks.py`](engine/picks.py) | ≤72-hour pick generator with NO PICK suppression and parlay rules |
| [`engine/corrstats.py`](engine/corrstats.py) | Pearson/phi/joint-rate estimators with game-cluster bootstrap and shrinkage |
| [`engine/gates.py`](engine/gates.py) | G0–G12 gate report, Brier/log loss/reliability, walk-forward folds, trials control |
| [`engine/ledger.py`](engine/ledger.py) · [`engine/schema.py`](engine/schema.py) | Provenance-enforced inputs ledger (rows without official https source + timestamps are rejected) |
| [`engine/cli.py`](engine/cli.py) | `python3 -m engine.cli status\|validate\|generate\|selftest` |
| [`tests/test_engine_models.py`](tests/test_engine_models.py) | 43 unit tests over labelled synthetic fixtures (`synthetic.invalid`) |

## Research documents

- [`docs/audit.md`](docs/audit.md) — repository/evidence audit and hard blockers.
- [`docs/strategy-framework.md`](docs/strategy-framework.md) — proposed singles, props, parlay, injury and game-flow signals.
- [`docs/validation-plan.md`](docs/validation-plan.md) — leakage-free testing, uncertainty and leaderboard gates.
- [`docs/decision-register.md`](docs/decision-register.md) — executive summary, 16 open questions and discovery suggestions.
- [`docs/line-origination.md`](docs/line-origination.md) — how an originated line is produced and kept separate from the market.
- [`docs/automation.md`](docs/automation.md) — the daily, no-manual-input runbook for the three-day slate.
- [`docs/correlation-and-leaderboard.md`](docs/correlation-and-leaderboard.md) — correlation measurement plan and leaderboard design.
- [`docs/suggestions.md`](docs/suggestions.md) — four gating decisions, 12 decision-queue proposals and 23 site-improvement proposals for reviewer action.
- [`docs/source-verification.md`](docs/source-verification.md) — per-source verification log and the irregularities that were found.
- [`docs/sources.md`](docs/sources.md) — official-source register and interpretation limits.
- [`docs/site-spec.md`](docs/site-spec.md) — dashboard organization and integrity rules.
- [`docs/verification-log.md`](docs/verification-log.md) — line-by-line re-verification of all 22 cited sources and the corrections made.
- [`docs/release-audit-607c89a8.md`](docs/release-audit-607c89a8.md) — final acceptance map, verification results, open flags and production-data blockers.
- [`docs/engine.md`](docs/engine.md) — model-side engine guide: ratings/props/injury/game-flow methods, UNFITTED parameter register, inputs spec.
- [`docs/leaderboard.md`](docs/leaderboard.md) — leaderboard competition rules, anti-luck scoring and proposed reward tiers (supplementary design record).
- [`docs/verification-pass-c6ae3e43.md`](docs/verification-pass-c6ae3e43.md) — fourth verification pass (task V, PR #17): 19 primary pages re-read and quoted, live-site and Pages API check, flag V-01.
- [`docs/verification-pass-88673f07.md`](docs/verification-pass-88673f07.md) — fourth live re-check of the primary sources, with the test-count, injury-snapshot and privacy-wording corrections (T-01…T-03) and observations O-1…O-3.
- [`docs/verification-pass-644efa79.md`](docs/verification-pass-644efa79.md) — fourth independent verification pass by the final-integration session (19 sources quote-checked, requirements checklist; VI-01/VI-02 cross-referenced to T-01/V4-03 and V4-05 on the review page).
- [`docs/verification-pass-2c06c7f9.md`](docs/verification-pass-2c06c7f9.md) — third independent verification pass (18 sources quote-checked; 5 irregularities I-1…I-5).
- [`docs/suggestions-2c06c7f9.md`](docs/suggestions-2c06c7f9.md) — supplementary suggestion register (paths A/B/C and decision log) from the same session.
- [`COORDINATION.md`](COORDINATION.md) — task board, verification notes and publication record.

## Local verification

```sh
python3 scripts/check_site.py --with-tests   # page, link, table and source-link checks + engine tests
python3 -m unittest discover -s tests -t .    # engine unit tests only
python3 scripts/run_pipeline.py \
    --inputs data/inbox-example \
    --out data/out-example \
    --now 2026-11-14T12:00:00Z                # synthetic smoke test
```

The checker verifies each page's title and single heading, every local link and fragment, every HTML table row's final source cell, every Markdown table row in `docs/` for an HTTPS source on an approved official-source domain, and that no page on disk is missing from the checked set. It does not fetch external sites; each cited source must be reviewed directly (the review log is in `docs/source-verification.md`). The site's own code uses static HTML/CSS only, with no third-party scripts or cookies and no form or data collection. GitHub Pages is different: GitHub states that "when a GitHub Pages site is visited, the visitor's IP address is logged and stored for security purposes" ([GitHub Docs, What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)). This was flagged as T-03 on the Flagged for Review page.

## Publication record

- **PR #10** (`arena/248bb9ab-nba4` → `main`, merged `2026-11-14`) brought the reference engine, the 11-page dashboard and the integration of all parallel sessions' work into `main`. GitHub Pages built the merge commit `f9c63d2` successfully (`status: built`, 29.3s) and every page was re-fetched from the live URL with intact tables, merged suggestion registers and source links.
- PRs #1–#9 (initial dashboard, integrations, independent verification and the one Pages build-rate-limit incident) are recorded in [`COORDINATION.md`](COORDINATION.md).

## Scope and disclaimer

The dashboard is informational and independent. It is not affiliated with or endorsed by the NBA, is not a betting service or financial advice, and does not promise that statistical testing can remove luck or guarantee results. If the product becomes a commercial or live picks/rewards service, re-evaluate data rights, jurisdiction, responsible-use requirements and hosting before launch; GitHub Pages is not intended for commercial SaaS or online-business hosting.
