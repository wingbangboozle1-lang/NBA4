# Repository review and live-site re-check (session `arena/eb9d2e0b-nba4`, task T)

Date of checks: 2026-11-14 (UTC). Scope: re-run the repository's own checks, confirm the live GitHub Pages deployment, re-read two primary sources directly, and log irregularities. No shared page (`*.html`), data file, or engine code was changed in this task.

## 1. Checks re-run on `arena/eb9d2e0b-nba4` (branched from `d51ed9f`)

| Check | Command | Result |
| --- | --- | --- |
| Static site and table checker | `python3 scripts/check_site.py` | PASS: 11 pages, 203 HTML data rows and 341 Markdown data rows. Every row has an official HTTPS source link. |
| Unit and mechanics tests | `python3 -m unittest discover -s tests -t .` | OK. Output is labelled as synthetic fixtures and ends "Mechanics OK. Production runs with the real ledger remain NO PICK until rights (G0) and data (G1) are cleared." |
| GitHub Pages status | `gh api repos/wingbangboozle1-lang/NBA4/pages` | `status: built`, `source: main /`, `https_enforced: true`, public URL https://wingbangboozle1-lang.github.io/NBA4/ |
| Open pull requests | `gh pr list --state open` | None open at the time of the check. |
| Repo-internal links (GitHub `blob/main` and `tree/main` links in HTML and docs) | path existence check | All 22 distinct linked paths (blob/tree form) exist on `main`; none missing. |
| URL inventory | grep over `*.html`, `docs/*.md`, `README.md`, then host count | 62 distinct URL strings. Split by host: 25 external primary sources (NBA `www.nba.com` 5, `official.nba.com` 1, `ak-static.cms.nba.com` 2, `cdn.nba.com` 1, NIST 2, scikit-learn 5, Ksa 5, GitHub Docs 3, GitHub API 1); 23 links to this repository on github.com; 13 links to this project's own Pages site; 1 reserved fixture host (`synthetic.invalid`, see IR-T2). |

Limitation: the sandbox cannot make direct HTTP requests to `nba.com` or `docs.github.com` (`curl` returned no response, code 000). Those pages were therefore checked with the web-fetch tool, not `curl`. Results are in section 2.

## 2. Primary sources re-read in this task

| Source | Statement checked | Result | Link |
| --- | --- | --- | --- |
| NBA.com Terms of Use, §9 "NBA Statistics" (chunk 4 of 10) | NBA Statistics "may not be used in connection with any gambling activity (including legal gambling activity)"; may not be used for "a database ... of comprehensive, regularly updated statistics ... without the Operator's express prior consent." | Confirmed verbatim. | [NBA.com Terms of Use](https://www.nba.com/termsofuse) (anchor [§9](https://www.nba.com/termsofuse#nba-statistics)) |
| NBA.com Terms of Use, §1 "Ownership and Use Restrictions" (chunk 0 of 10) | Basketball Content, including statistics, may not be "reproduced, republished, ... reused ... without the written permission of the Operator." | Confirmed verbatim. | [NBA.com Terms of Use §1](https://www.nba.com/termsofuse#ownership-and-use-restrictions) |
| GitHub Docs, GitHub Pages limits | Pages "is not intended for or allowed to be used as a free web-hosting service to run your online business ... or providing commercial software as a service (SaaS)"; soft limit of 10 builds per hour; no user data collection for educational copies. | Confirmed verbatim. | [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| GitHub Pages API for this repo | `status: built`, `source main /` | Confirmed at check time (see section 1). | [Repository Pages API](https://api.github.com/repos/wingbangboozle1-lang/NBA4/pages) |

## 3. Irregularities flagged for review

These are logged for a reviewer and for the integration session. None of them was fixed here, because each sits in a shared page or in engine code owned by another session.

| ID | Finding | Evidence | Severity | Suggested owner action |
| --- | --- | --- | --- | --- |
| IR-T1 | **Duplicate engine modules after the parallel merge.** Both versions of each module are live and imported by different test suites. `engine/validation.py` (267 lines) and `engine/gates.py` (176 lines) both exist. `engine/correlation.py` (219 lines) and `engine/corrstats.py` (208 lines) both exist. `tests/test_engine.py` imports `validation` and `correlation`; `tests/test_engine_models.py` and `engine/cli.py` / `engine/selftest.py` use `gates` and `corrstats`. The board's merge log says these were renamed, which implies the old files should be gone. | `COORDINATION.md` "Parallel-merge log"; `grep` of `engine/` and `tests/` imports; `wc -l` of each file. | Medium. Two gate implementations and two correlation implementations could drift apart. | Decide on one canonical module per pair, then retire the other in a single change. Do not delete either without a test migration. |
| IR-T2 | **Non-official host in the fixture text.** `https://synthetic.invalid/fixture` appears in `docs/engine.md`. It is a reserved test host, not a source. | `docs/engine.md` lines 37 and 86; `README.md` line 53 names `synthetic.invalid`. | Low. It is labelled synthetic and filtered by `load_ledger()`. | Keep, but note in the source-check exemption list so the checker does not treat it as a missing source. |
| IR-T3 | **Board claims the sandbox can reach the official sites; in this run it could not with `curl`.** The "Final integration verification" section says verification used the web-fetch tool, which agrees with this run. | `COORDINATION.md` "Final integration verification". | Low. Process note only. | Keep the fetch-tool method stated in every verification record. |
| IR-T4 | **Requested scope exceeds the rights gate.** The task brief asks for picks for each upcoming slate. NBA Terms §9 (section 2 above) forbids using NBA Statistics "in connection with any gambling activity". The repository's own gates (G0 rights, G1 data) therefore block any production pick. | `docs/engine.md`; `docs/validation-plan.md`; section 2 above. | High, but a decision rather than a defect. | Owner decision needed: a licensed data source, a rights agreement, or a research-only scope. See the decision register. |

## 4. Counts and cross-checks

- HTML data rows: 203 across 11 pages. Markdown data rows in `docs/`: 341.
- The 2026-11-13 injury PDF is treated as a dated snapshot only. No player rows are copied into the site.
- No new values, probabilities, correlations, odds, or strategy results were added in this task. All such cells remain blank and flagged unverified.

## 5. Handoff

Requests for shared files (the Flagged for Review page and the site index/navigation) are logged in `COORDINATION.md` for the integration session, not edited here.
