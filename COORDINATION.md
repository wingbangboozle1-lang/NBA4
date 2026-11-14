# Coordination board

Updated: 2026-11-14 (UTC). The starting repository contained only `README.md` and no coordination board or task claims. No concurrent claims were visible at kickoff. The session ID below uses the active Arena branch identifier because no separate session ID is exposed in the repository.

| Task | Status | Owner / session ID | Exact file scope | Verification / sources / notes |
| --- | --- | --- | --- | --- |
| A. Baseline repository, evidence and decision-gap audit | done | `arena/c5eef6bb-nba4` | `COORDINATION.md`, `docs/audit.md` | Verified the starting one-line README/no application data; checked NBA Stats FAQ, NBA Terms §§1/9, 2026–27 injury policy/PDF and schedule, NBA Stats glossary, GitHub Pages docs/API, and Ksa pages. Detailed snapshot, scope limits, and citations: [`docs/audit.md`](docs/audit.md). |
| B. Strategy design, validation gates, correlation and leaderboard specification | done | `arena/c5eef6bb-nba4` | `docs/strategy-framework.md`, `docs/validation-plan.md` | Proposed single, prop, injury, game-flow and joint/parlay hypotheses; defined chronological/holdout, calibration, uncertainty and leaderboard gates. Confirmed method references at NBA Stats/Terms, NBA Injury Report, scikit-learn time-split/calibration/Brier docs, NIST correlation/bootstrap pages. No strategy was trained; all metric/correlation/result cells remain blank. Markdown table-link and whitespace checks passed. |
| C. Executive summary, questions, missing-information register and source catalog | in progress | `arena/c5eef6bb-nba4` | `docs/decision-register.md`, `docs/sources.md` | Claim committed before work. Each decision row will include an official primary-source link and a discovery action; unresolved values remain blank/flagged. |
| D. Static site, source-linked data tables, navigation, review flags and GitHub Pages workflow | unclaimed | — | `site/**`, `.github/workflows/pages.yml`, `README.md` | Shared site data, index and navigation are reserved for final integration after A–C. |
| E. Final integration, full verification, build/link checks, PR and Pages deployment | unclaimed | — | `COORDINATION.md`, `site/**`, `.github/workflows/pages.yml`, `README.md` | Perform only after all prerequisite tasks are done; record the PR and deploy result here. |

## Handoff and integrity rules

- Keep file scopes non-overlapping and update this board before starting work. If a needed file is owned by another session, log a request here rather than editing it.
- Every factual data value must have an official primary source, a source timestamp, and a verification status. Leave unknown values blank and flag them; do not manufacture picks, probabilities, correlations, or performance.
- Strategy claims are hypotheses until a pre-registered, leakage-free, out-of-sample validation supports them. This board records status and evidence; it is not itself evidence.
- GitHub Pages publication is conditional on verified inputs, a passing site build/link check, and repository Pages configuration. No deployment has been attempted at kickoff.
