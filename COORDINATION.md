# Coordination board

Updated: 2026-11-14 (UTC). The starting repository contained only `README.md` and no coordination board or task claims. No concurrent claims were visible at kickoff. The session ID below uses the active Arena branch identifier because no separate session ID is exposed in the repository.

| Task | Status | Owner / session ID | Exact file scope | Verification / sources / notes |
| --- | --- | --- | --- | --- |
| A. Baseline repository, evidence and decision-gap audit | done | `arena/c5eef6bb-nba4` | `COORDINATION.md`, `docs/audit.md` | Verified the starting one-line README/no application data; checked NBA Stats FAQ, NBA Terms §§1/9, 2026–27 injury policy/PDF and schedule, NBA Stats glossary, GitHub Pages docs/API, and Ksa pages. Detailed snapshot, scope limits, and citations: [`docs/audit.md`](docs/audit.md). |
| B. Strategy design, validation gates, correlation and leaderboard specification | done | `arena/c5eef6bb-nba4` | `docs/strategy-framework.md`, `docs/validation-plan.md` | Proposed single, prop, injury, game-flow and joint/parlay hypotheses; defined chronological/holdout, calibration, uncertainty and leaderboard gates. Confirmed method references at NBA Stats/Terms, NBA Injury Report, scikit-learn time-split/calibration/Brier docs, NIST correlation/bootstrap pages. No strategy was trained; all metric/correlation/result cells remain blank. Markdown table-link and whitespace checks passed. |
| C. Executive summary, questions, missing-information register and source catalog | done | `arena/c5eef6bb-nba4` | `docs/decision-register.md`, `docs/sources.md` | Completed executive summary, 12 decision questions, discovery recommendations, known/missing inputs and official source catalog. Checked every Markdown data row for an official source link; the structural/link-presence check passed. |
| D. Site information architecture and content specification (no shared pages/data) | in progress | `arena/c5eef6bb-nba4` | `docs/site-spec.md` | Claim committed before work. The actual site index, navigation and source-linked tables remain reserved for final integration. |
| E. Final site integration, full verification, build/link checks, PR and Pages deployment | unclaimed | — | `COORDINATION.md`, `index.html`, `slate.html`, `injuries.html`, `strategies.html`, `questions.html`, `sources.html`, `review.html`, `assets/**`, `.nojekyll`, `README.md` | Perform only after A–D are done; use the existing `main`/root Pages source and record the PR and deploy result here. |

## Handoff and integrity rules

- Keep file scopes non-overlapping and update this board before starting work. If a needed file is owned by another session, log a request here rather than editing it.
- Every factual data value must have an official primary source, a source timestamp, and a verification status. Leave unknown values blank and flag them; do not manufacture picks, probabilities, correlations, or performance.
- Strategy claims are hypotheses until a pre-registered, leakage-free, out-of-sample validation supports them. This board records status and evidence; it is not itself evidence.
- GitHub Pages publication is conditional on verified inputs, a passing site build/link check, and repository Pages configuration. No deployment has been attempted at kickoff.
