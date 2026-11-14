# Final acceptance verification — session `arena/ad4e7bf0-nba4`

**Date:** 2026-11-14 UTC. **Scope:** completion of task AA (final acceptance audit and release-readiness confirmation) after PR #28 merged and after the subsequent bookkeeping/snapshot PRs #29–#35. This is the post-merge acceptance check the release-audit document required before the release could be described as deployed/complete. It is a repository acceptance pass, not a fresh re-verification of every external source.

## What was re-checked (local, run this session)

| Check | Command | Result | Reference |
| --- | --- | --- | --- |
| Static site + engine tests | `python3 scripts/check_site.py --with-tests` | **PASS** — 11 pages, 323 HTML data rows, 536 Markdown data rows, engine unit tests OK | [`scripts/check_site.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |
| Unit tests | `python3 -m unittest discover -s tests -t .` | **OK** — 101 tests (47 + 43 + 11, three suites), synthetic fixtures only | [`tests/`](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |
| Engine status | `python3 -m engine.cli status` | 0 records loaded; **NO AUTHORIZED INPUTS → no lines, no picks** | [`engine/cli.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/cli.py) |
| Engine gates | `python3 -m engine.cli validate` | G0/G1/G2/G6/G9/G12 **blocked**; G3–G5/G7–G8/G10–G11 **not run**; G12 `declared_minimum_sample_size=UNSET` | [`engine/gates.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/gates.py)<br>[NBA Terms §9](https://www.nba.com/termsofuse) |
| Pipeline smoke | `python3 scripts/run_pipeline.py --inputs data/inbox-example --out /tmp/nba4-acc --now 2026-11-14T12:00:00Z` | 2 synthetic events, `rights cleared: False`, 0 forecasts, 0 bet picks, 0 no-bet picks, append-only ledger written | [`engine/pipeline.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| Snapshot sync | `python3 scripts/build_snapshots.py --check` (via checker) | slate/injury tables in sync with `data/snapshots/` provenance files | [`scripts/build_snapshots.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/build_snapshots.py)<br>[Official schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |

**No NBA-derived value was added, changed or inferred.** Every numeric model field (lines, probabilities, picks, minutes/production/game-flow impacts, correlations, ROI) remains blank and flagged unverified.

## Live-site and deployment confirmation (post-merge)

- **GitHub Pages API** (`api.github.com/repos/wingbangboozle1-lang/NBA4/pages`): `status: built`, source `main` at `/`, `public: true`, `https_enforced: true`.
- **Live landing page** (`https://wingbangboozle1-lang.github.io/NBA4/`): serves the executive-summary overview with the six "What matters before any pick" decision rows and the "What is built / what still blocks it" capability table; all source links intact.
- **Live slate page** (`…/slate.html`, cache-busted): serves the 22 official schedule rows (rows 231–252), each with its reason-coded NO PICK (`RIGHTS_NOT_CLEARED` / `NO_BENCHMARK_QUOTE` / `STALE_DATA`) and a schedule-PDF source link; line and probability cells empty.
- **Live injuries page** (`…/injuries.html`, cache-busted): serves the 49-row official 2026-11-14 04:30 AM ET injury report, each row with the report PDF link; the repaired date/time rows carry both the report and schedule sources; the one lost team cell (Traore, Nolan) is left blank and flagged unverified.

## External source spot-checks (this session)

The following primary claims were re-fetched and read this session. Quotations are recorded so a reader can check them without re-fetching.

| Source | Statement relied on | Verdict this session |
| --- | --- | --- |
| [NBA Stats FAQ](https://www.nba.com/stats/help/faq) | "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats" | **Confirmed verbatim** (read this session). |
| [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) | "GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your online business, e-commerce site, or any other website that is primarily directed at either facilitating commercial transactions or providing commercial software as a service (SaaS)." | **Confirmed verbatim** (read this session). |
| [NBA.com Terms of Use §9](https://www.nba.com/termsofuse#nba-statistics) | NBA Statistics "may not be used in connection with any gambling activity (including legal gambling activity)" (clause (iv)); "database … of comprehensive, regularly updated statistics … without the Operator's express prior consent" (clause (vii)) | **Could not be re-fetched this session** — the page returned a transient `502 Bad Gateway` on repeated attempts. The verbatim quotation is preserved from the prior quote-checked pass (clauses (i)–(vii) read in full): [`docs/verification-pass-644efa79.md`](verification-pass-644efa79.md). Recorded here so this is not misread as a new verification or a refutation; the 502 is a server-side transient, not evidence the clause changed. |

## Irregularities / observations this session

- **AA-01 (low, transient).** `https://www.nba.com/termsofuse` returned `502 Bad Gateway` on 2026-11-14 during this session's spot-check. The blocking §9 claim is not weakened: it is quoted verbatim in an earlier quote-checked pass and is unchanged in the site. No action needed beyond recording it; a future session should re-fetch the Terms page when NBA.com is reachable to refresh the quotation.
- **AA-02 (low, method).** The release-audit document (PR #28) stated the acceptance branch was not itself the deployed site and that the post-merge Pages/live-page confirmation had to be recorded before the release could be called complete. That confirmation is now performed and recorded here (and in the release-audit doc's deployment section), closing the open condition.
- **No fabricated data.** No pick, line, probability, correlation, injury-minute effect, ROI or leaderboard result was produced or published. Blank means unmeasured, not zero.

## Disposition

The informational research dashboard is **technically ready and deployed** (Pages `built`, live pages serving the published official observations and source-linked tables). Production forecasting, picks, leaderboard or rewards remain **not ready**: there is no rights-cleared input ledger, licensed feed, trained/calibrated model, settled holdout, or product/legal approval. The hard blocker remains data rights (NBA Stats FAQ + NBA Terms §9), not code.
