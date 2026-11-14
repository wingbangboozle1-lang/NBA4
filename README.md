# NBA4 — NBA line research dashboard

**Live site:** [https://wingbangboozle1-lang.github.io/NBA4/](https://wingbangboozle1-lang.github.io/NBA4/) (GitHub Pages is configured from `main` at the repository root; deployment is re-checked and recorded in [`COORDINATION.md`](COORDINATION.md) after every merge.)

## Current status

This repository provides an evidence-first research program, a static decision dashboard, and a **tested but uncalibrated line-origination/picks engine**. It does **not** contain trained strategies or an authorized point-in-time NBA/market data feed. No NBA game lines, player props, parlay probabilities, injury-minute projections, correlations, ROI, strategy rankings or rewards are generated. Unknown numerical fields are left blank and flagged, not guessed.

A material source/rights issue is documented: the NBA Stats FAQ says its statistics are for viewing and not available for download; NBA.com Terms restrict the use of NBA Statistics in gambling, including legal gambling. No NBA Stats scraping, player data, team data, odds or schedule rows have been added. Obtain appropriate written permission/data rights and legal review before a betting model or public picks are considered.

## Dashboard sections

- [Overview and executive summary](https://wingbangboozle1-lang.github.io/NBA4/)
- [Upcoming slate status](https://wingbangboozle1-lang.github.io/NBA4/slate.html)
- [Injuries, rotation and game flow](https://wingbangboozle1-lang.github.io/NBA4/injuries.html)
- [Strategies and validation gates](https://wingbangboozle1-lang.github.io/NBA4/strategies.html)
- [Leaderboard and rewards framework](https://wingbangboozle1-lang.github.io/NBA4/leaderboard.html)
- [Suggestions and decision queue](https://wingbangboozle1-lang.github.io/NBA4/suggestions.html)
- [Decision questions and missing information](https://wingbangboozle1-lang.github.io/NBA4/questions.html)
- [Verified source register](https://wingbangboozle1-lang.github.io/NBA4/sources.html)
- [Flagged for Review](https://wingbangboozle1-lang.github.io/NBA4/review.html)

## Engine (tested, unfitted, no live output)

`engine/` implements the documented pipeline — provenance-enforced inputs ledger → originated spread/total/player-prop distributions → injury and game-flow scenarios → correlation estimation with game-cluster bootstrap → validation gates G0–G12 → a pick generator with a hard ≤3-day horizon and NO PICK suppression. It never invents values and never emits an eligible pick while any gate is blocked. See [`docs/engine.md`](docs/engine.md) for the module map, the UNFITTED/PROPOSED parameter register and the authorized-ledger input spec.

```sh
python3 -m engine.cli status      # honest input/gate state (currently: NO AUTHORIZED INPUTS)
python3 -m engine.cli validate    # machine-checkable G0–G12 report
python3 -m engine.cli generate --days 3
python3 -m engine.cli selftest    # SYNTHETIC fixture demo, stdout only
python3 -m unittest discover -s tests   # 43 mechanics tests
```

## Research documents

- [`docs/audit.md`](docs/audit.md) — repository/evidence audit and hard blockers.
- [`docs/strategy-framework.md`](docs/strategy-framework.md) — proposed singles, props, parlay, injury and game-flow signals; correlation measurement plan.
- [`docs/validation-plan.md`](docs/validation-plan.md) — leakage-free testing, uncertainty and leaderboard gates.
- [`docs/engine.md`](docs/engine.md) — engine guide, formulas, parameter register and inputs spec.
- [`docs/leaderboard.md`](docs/leaderboard.md) — competition rules, scoring, anti-luck controls and proposed reward tiers.
- [`docs/suggestions.md`](docs/suggestions.md) — suggestion register with paths A/B/C, trade-offs and decision log.
- [`docs/decision-register.md`](docs/decision-register.md) — executive summary, open questions and discovery suggestions.
- [`docs/sources.md`](docs/sources.md) — official-source register and interpretation limits.
- [`docs/verification-log.md`](docs/verification-log.md) — independent line-by-line re-verification: exact quotes, results and logged irregularities.
- [`docs/site-spec.md`](docs/site-spec.md) — dashboard organization and integrity rules.
- [`COORDINATION.md`](COORDINATION.md) — task board, verification notes and publication record.

## Local verification

Run the static checks from the repository root:

```sh
python3 scripts/check_site.py
```

The checker verifies each page’s title/headings and local links/fragments, every HTML table row’s final source cell, and every Markdown table row in `docs/` for an HTTPS source on an approved official-source domain. It does not fetch external sites; each cited source must be reviewed directly (the current pass is recorded in [`docs/verification-log.md`](docs/verification-log.md)). The site uses static HTML/CSS only and no third-party scripts or data collection.

## Scope and disclaimer

The dashboard is informational and independent. It is not affiliated with or endorsed by the NBA, is not a betting service or financial advice, and does not promise that statistical testing can remove luck or guarantee results. If the product becomes a commercial/live picks or rewards service, re-evaluate data rights, jurisdiction, responsible-use requirements and hosting before launch; GitHub Pages is not intended for commercial SaaS or online-business hosting.
