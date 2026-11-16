# The scheduled refresh job (task BH)

**Session:** `arena/cbc8e41a-nba4` · **Built:** 2026-11-16 · **Files:** [`scripts/scheduled_refresh.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/scheduled_refresh.py), [`.github/workflows/daily-refresh.yml`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/.github/workflows/daily-refresh.yml), [`tests/test_scheduled_refresh.py`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_scheduled_refresh.py)

**Brief item answered.** "Extend the scheduled job to refresh the official schedule, standings, team
statistics and injury report for each rolling slate, then rebuild only after freshness and provenance
gates pass." This also answers decision-register **Q10** ("scheduling the daily job — the trigger is not
chosen"): the 2026-11-16 brief instructs that there be no manual input, so the trigger chosen here is a
daily GitHub Actions schedule (`15 10 * * *` UTC), with a manual `workflow_dispatch` for verification.

## 1. What the job does, in order

| Phase | Step | Source | Gate name(s) | On failure |
| --- | --- | --- | --- | --- |
| fetch | Official 2026–27 schedule PDF: download, `%PDF` magic, sha256 | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | `schedule_pdf_fetch` | run fails; nothing rebuilt |
| fetch | Injury index: parse every report link, keep the newest listed revision | [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) | `injury_index_fetch` | run fails |
| fetch | Newest listed report PDF: download and check its printed header (`Injury Report: M/D/YY`) against the date in its own URL | newest [report PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) | `injury_report_newest_fetch`, `injury_report_header` | run fails (header check fails closed if `pypdf` is absent) |
| fetch | Standings: official stats feed behind the standings page, 30 rows expected | [standings](https://www.nba.com/standings) | `standings_fetch` | run fails |
| fetch | The three official team-stat pages (traditional/`Base`, advanced, opponent), 30 rows each | [traditional](https://www.nba.com/stats/teams/traditional/), [advanced](https://www.nba.com/stats/teams/advanced), [opponent](https://www.nba.com/stats/teams/opponent) | `teamstats_traditional_fetch`, `teamstats_advanced_fetch`, `teamstats_opponent_fetch` | run fails |
| freshness | Schedule PDF sha256 vs the committed baseline in `data/snapshots/raw/ci/schedule-sha-baseline.txt` | [raw archive directory](https://github.com/wingbangboozle1-lang/NBA4/tree/main/data/snapshots/raw) · [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | `schedule_pdf_drift` | run fails: a silently re-issued schedule invalidates the published slate rows |
| freshness | Published injury transcription age ≤ 24 h at run time (record also notes whether a newer report exists) | [newest pointer snapshot](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/snapshots/injuries-newest-pointer-2026-11-15.json) | `injury_transcription_age` | run fails: transcription must be refreshed at least daily |
| freshness | Published 72-hour slate window must contain "now" | [slate snapshot](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/snapshots/slate-2026-11-15.json) | `slate_window_current` | run fails: the rolling window has rolled past its data |
| provenance | Every `data/snapshots/*.json` must carry `source_url` + `fetched_at_utc` (or `derived_from` for derived files) | [repository snapshots](https://github.com/wingbangboozle1-lang/NBA4/tree/main/data/snapshots) | `provenance_chain` | run fails |
| build | `build_snapshots.py --check` and `check_site.py --with-tests` | [build script](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/build_snapshots.py) · [site checker](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) | `build_snapshots_check`, `site_check_with_tests` | run fails |
| rebuild | **Only when every gate above passed:** regenerate the site tables, commit if (and only if) the result differs | [build script](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/build_snapshots.py) | — | never reached on a failing gate |

Every gate result (pass/fail, detail, source URL, observation time) is written to a JSON run record,
uploaded as a workflow artifact (90-day retention) and printed in the job summary, so each run is
auditable after the fact.

## 2. Modes (why two)

* **`gates`** — cron default. Every gate asserted; exit 1 on any failure; rebuild licensed only on a
  fully green run. Fail-closed by construction: `rebuild_allowed` is a property of the record, not a
  step that can be skipped.
* **`probe`** — dispatchable. Fetch-phase gates asserted (reachability + parseability); freshness
  failures are reported in the record but do not fail the run, and a probe run can never license a
  rebuild. This separates "the source moved" (an alarm) from "the runner cannot reach the source"
  (a connectivity problem), which is what a verification session needs to tell apart.
* **`offline`** — no network at all (provenance + build gates); used by the unit tests and locally
  before any push.

## 3. What the job deliberately does not do

1. **It does not transcribe injury-report rows.** Row-level transcription of the PDF remains the
   human-verified snapshot cycle the repository already runs (`data/snapshots/raw/*.pipes` → JSON), because
   PDF text extraction outside the verified pipeline has never been byte-compared against the file of
   record. The job verifies the newest report's *printed header* instead, archives the run record, and
   lets the `injury_transcription_age` gate force the cadence. This limit is recorded as flag **BH-01**
   below, not hidden.
2. **It never touches the rights gate.** No line, probability, price or pick is generated; G0 / D-01 /
   IR-T4 stand. The job moves official publications into gate checks only.
3. **It commits nothing when a gate fails.** The workflow's commit step is conditioned on the script's
   exit code; a red run leaves `main` (or the dispatch ref) untouched. Pushes made by `GITHUB_TOKEN`
   do not trigger new workflow runs, so the job cannot loop on itself.

## 4. Verification performed

| Check | Result | When |
| --- | --- | --- |
| [tests/test_scheduled_refresh.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_scheduled_refresh.py) | 26 tests, OK — link ordering (dates + AM/PM), header-vs-URL match, 24 h freshness boundary, window containment, drift baseline (first run / match / change), provenance accept+reject paths, all-green gates run, standings-short fail-closed, stale-transcription rebuild block, probe semantics, offline no-network guarantee, missing-`pypdf` fail-closed, run-record shape | 2026-11-16 |
| [full suite via discover](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) | 323 OK (297 + 26, seven suites), command `python3 -m unittest discover -s tests -t .` | 2026-11-16 |
| [scripts/scheduled_refresh.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/scheduled_refresh.py) offline mode | exit 0; 3/3 gates pass (provenance 13 files, snapshot build check, site check with tests), command `--mode offline` | 2026-11-16T14:44Z |
| [scripts/check_site.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) | PASS: 12 pages, 470 HTML rows, 880 Markdown rows, engine tests OK, command `--with-tests` | 2026-11-16 |
| [Actions run 43890323162](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/43890323162) | First real run (push, gates). Reported success but the conclusion is **void**: the step ran `python3 … \| tee` under the default `bash -e` (no `pipefail`), so `tee` masked the script's exit code — a false green, caught in review the same day and fixed in PR #59 (explicit `shell: bash`) | 2026-11-16T14:52Z |
| [Actions run 43892474532](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/43892474532) | Gates run after the pipefail fix: **8/14 passed, rebuild blocked** (fail-closed as designed). Green: schedule PDF + drift baseline, injury index, newest report PDF, slate window, provenance (13 files), `build_snapshots --check`, `check_site --with-tests`. Failed: `injury_report_header` (pypdf layout miss), `standings_fetch` + all three `teamstats_*` (`stats.nba.com` read timeouts from GitHub-hosted runners), `injury_transcription_age` (27.4 h > 24 h) | 2026-11-16T15:05Z |
| [Actions run 43894487242](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/43894487242) | Gates run after the header fix: **9/14 passed, rebuild blocked**. `injury_report_header` now PASS (whitespace-tolerant match over all pages via pypdf/pdfminer). Remaining failures: the four `stats.nba.com` timeouts (second consecutive confirmation) and `injury_transcription_age` (27.75 h; newest listed report `2026-11-16 10:00 AM ET`). The run also **committed its own schedule-PDF baseline** (`9d77640`, sha256 `5e82e37e…`) through the licensed baseline step — the bot's first gated write to `main` | 2026-11-16T15:12Z |

## 5. Flags raised by this task

| Flag | Severity | Finding | Status |
| --- | --- | --- | --- |
| BH-01 | Medium | Full automation stops at the PDF: row transcription stays manual-verified, so "no manual input" is satisfied for fetch/freshness/provenance/rebuild but **not** for the transcription step itself. | Open — proposal: a byte-compared extraction service (fetch-page text vs `pdftotext`/`pypdf` output proven equal against historical [`.pipes` files](https://github.com/wingbangboozle1-lang/NBA4/tree/main/data/snapshots/raw)) before automating transcription. |
| BH-02 | Low | Standings and team-stat gates consume the official JSON feed behind the pages rather than the rendered HTML, because the rendered tables are client-side; the run record stores the row counts actually seen. | Open — reachability from GitHub-hosted runners is proven or disproven by the [dispatch runs](https://github.com/wingbangboozle1-lang/NBA4/actions/workflows/daily-refresh.yml) linked from the board. |
| BH-03 | Low | The 24-hour transcription-age threshold is a **proposed** parameter (matches the repository's daily observation cadence), not an NBA-published deadline. | Open — reviewer may tighten it; the NBA's own deadlines are on the [injury-report policy page](https://official.nba.com/nba-injury-report-2026-27-season/). |
| BH-04 | Info | The schedule baseline (`data/snapshots/raw/ci/schedule-sha-baseline.txt`) is created by the first successful fetch; until then the drift gate reports "baseline established" rather than comparing. | **Closed 2026-11-16:** run 43894487242 committed the baseline as `9d77640` (sha256 `5e82e37e…`) via the licensed baseline step ([raw archive directory](https://github.com/wingbangboozle1-lang/NBA4/tree/main/data/snapshots/raw)). |
| BH-05 | Medium | `stats.nba.com` (`leaguestandingsv3`, `leaguedashteamstats` ×3) **timed out from GitHub-hosted runners in two consecutive runs** (43892474532, 43894487242; 30 s ×3 retries each), so the [standings](https://www.nba.com/standings) and [team-stat](https://www.nba.com/stats/teams/advanced) refresh gates cannot pass in CI as configured. The job correctly blocks the rebuild. | Open — transport decision needed (a runner that the official feed serves, a licensed data vendor under G0, or accepting a documented standing failure); registered as a suggestion for the reviewer. |
| BH-06 | Medium | The first real run was a **false green**: `python3 … \| tee` under GitHub's default `bash -e` (no `pipefail`) masked the gates' exit code. | Closed — fixed in [PR #59](https://github.com/wingbangboozle1-lang/NBA4/pull/59) (explicit `shell: bash`); subsequent runs report the true conclusion (two red runs above). |
| BH-07 | Low | `workflow_dispatch` cannot be triggered by this session's token (`403 Resource not accessible by integration`, the same integration-permission limit earlier sessions recorded for Pages rebuild requests), so live verification went through the paths-limited `push` trigger and the daily cron instead ([workflow file](https://github.com/wingbangboozle1-lang/NBA4/blob/main/.github/workflows/daily-refresh.yml)). | Open — a token with Actions write (or a user dispatch) enables `mode=probe` runs; dispatch remains in the workflow for that purpose. |

## 6. Sources

| Source | Role in the job | Link |
| --- | --- | --- |
| 2026–27 schedule PDF (header: "AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE") | fetched; sha256 baseline; drift gate | [cdn.nba.com schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| NBA official injury-report index ("Reports are updated on a continual basis throughout the day.") | fetched; newest-revision discovery | [official.nba.com injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Newest injury-report PDF (printed header is the verification target) | fetched; header-vs-URL gate | [ak-static.cms.nba.com reports](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| NBA standings | fetched; 30-row gate | [nba.com/standings](https://www.nba.com/standings) |
| NBA team stats — traditional / advanced / opponent | fetched; 30-row gates each | [traditional](https://www.nba.com/stats/teams/traditional/) · [advanced](https://www.nba.com/stats/teams/advanced) · [opponent](https://www.nba.com/stats/teams/opponent) |
| GitHub Actions schedule documentation | cron trigger reference | [Events that trigger workflows](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule) |
