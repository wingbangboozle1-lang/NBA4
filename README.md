# NBA4 — NBA line research dashboard

**Live site:** [https://wingbangboozle1-lang.github.io/NBA4/](https://wingbangboozle1-lang.github.io/NBA4/) (GitHub Pages is configured from `main` at the repository root; deployment must be rechecked after merge.)

## Current status

This repository now provides an evidence-first research plan and a static decision dashboard. It does **not** contain a trained model or an authorized point-in-time NBA/market data feed. No NBA game lines, player props, parlay probabilities, injury-minute projections, correlations, ROI, strategy rankings or rewards are generated. Unknown numerical fields are left blank and flagged, not guessed.

A material source/rights issue is documented: the NBA Stats FAQ says its statistics are for viewing and not available for download; NBA.com Terms restrict the use of NBA Statistics in gambling, including legal gambling. No NBA Stats scraping, player data, team data, odds or schedule rows have been added. Obtain appropriate written permission/data rights and legal review before a betting model or public picks are considered.

## Dashboard sections

- [Overview and executive summary](https://wingbangboozle1-lang.github.io/NBA4/)
- [Upcoming slate status](https://wingbangboozle1-lang.github.io/NBA4/slate.html)
- [Injuries, rotation and game flow](https://wingbangboozle1-lang.github.io/NBA4/injuries.html)
- [Strategies and validation gates](https://wingbangboozle1-lang.github.io/NBA4/strategies.html)
- [Decision questions and missing information](https://wingbangboozle1-lang.github.io/NBA4/questions.html)
- [Verified source register](https://wingbangboozle1-lang.github.io/NBA4/sources.html)
- [Flagged for Review](https://wingbangboozle1-lang.github.io/NBA4/review.html)

## Research documents

- [`docs/audit.md`](docs/audit.md) — repository/evidence audit and hard blockers.
- [`docs/strategy-framework.md`](docs/strategy-framework.md) — proposed singles, props, parlay, injury and game-flow signals; correlation measurement plan.
- [`docs/validation-plan.md`](docs/validation-plan.md) — leakage-free testing, uncertainty and leaderboard gates.
- [`docs/decision-register.md`](docs/decision-register.md) — executive summary, open questions and discovery suggestions.
- [`docs/sources.md`](docs/sources.md) — official-source register and interpretation limits.
- [`docs/site-spec.md`](docs/site-spec.md) — dashboard organization and integrity rules.
- [`COORDINATION.md`](COORDINATION.md) — task board, verification notes and publication record.

## Local verification

Run the static checks from the repository root:

```sh
python3 scripts/check_site.py
```

The checker verifies each page’s title/headings and local links/fragments, every HTML table row’s final source cell, and every Markdown table row in `docs/` for an HTTPS source on an approved official-source domain. It does not fetch external sites; each cited source must be reviewed directly. The site uses static HTML/CSS only and no third-party scripts or data collection.

## Scope and disclaimer

The dashboard is informational and independent. It is not affiliated with or endorsed by the NBA, is not a betting service or financial advice, and does not promise that statistical testing can remove luck or guarantee results. If the product becomes a commercial/live picks or rewards service, re-evaluate data rights, jurisdiction, responsible-use requirements and hosting before launch; GitHub Pages is not intended for commercial SaaS or online-business hosting.
