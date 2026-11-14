# Automation: the three-day slate pipeline and the daily runbook

**Status: the pipeline is implemented and tested; it has never been run against NBA data.** The inputs directory contains a synthetic example only. The runbook below is the procedure the project will follow once data rights are cleared; every step is automatic, so no manual entry is required from the project owner.

Implementation: [`engine/pipeline.py`](../engine/pipeline.py), [`engine/contracts.py`](../engine/contracts.py) and the command-line entry point [`scripts/run_pipeline.py`](../scripts/run_pipeline.py).

## The daily cycle

| Step | What happens | Automatic? | Failure behaviour | Where implemented | Source link |
| --- | --- | --- | --- | --- | --- |
| 1. Ingest | Adapters write schedule, injury, results and quote records into the run directory, each with provenance and a permission flag | Yes | A record without provenance or a timestamp aborts the run | [`engine/contracts.py`](../engine/contracts.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/contracts.py) |
| 2. Rights check | Every record is checked against its `allowed_use` flag | Yes | The run is suppressed with reason `RIGHTS_NOT_CLEARED`; no forecast, no pick | [`engine/pipeline.py`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| 3. Freshness check | Records older than the declared tolerance (default 90 minutes) are rejected | Yes | The run is suppressed with reason `STALE_DATA` | [`engine/pipeline.py`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| 4. Slate selection | Events with a tip-off inside the rolling horizon are selected; the horizon is capped at 72 hours | Yes | Events outside the horizon are never forecast | [`select_slate`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| 5. Forecasting | Each enabled strategy produces immutable forecasts bound to an input snapshot hash | Yes | A strategy that fails is recorded as suppressed | [`engine/contracts.py`](../engine/contracts.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/contracts.py) |
| 6. Pick decision | Every forecast becomes a `bet` or a `no_bet` with reason codes | Yes | Missing market specification or a missing benchmark quote force `no_bet` | [`_decide`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| 7. Ledger | The run report and every record are appended to an append-only ledger | Yes | A write failure stops the run rather than publishing a partial output | [`append_ledger`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| 8. Publication | A separate, explicit step copies approved records into the site data | Yes, but gated | Publication requires the rights and validation gates; the site never shows an unverified value | [`scripts/check_site.py`](../scripts/check_site.py) | [Pages is static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) |

## The three-day horizon, made precise

| Parameter | Value in the code | Why it is a hard limit | Status | Source link |
| --- | --- | --- | --- | --- |
| Maximum horizon | 72 hours (`HORIZON_HOURS`) | The project request caps the forecast horizon at three days; the constructor raises if a longer horizon is configured | Enforced | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) · [request recorded in the register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Timezone | Declared per run (`timezone_name`, default UTC) | The official schedule and injury reports are published on stated deadlines in local and ET times; a single declared zone avoids ambiguity | Parameterised, timezone not yet chosen | [NBA injury-report policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Boundary | `[now, now + horizon]` | A game that has started is never re-forecast; a game beyond the horizon is never forecast | Enforced | [engine source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| Stale tolerance | 90 minutes by default | Reports "are updated on a continual basis throughout the day", so a snapshot must be recent to be usable | Parameterised | [NBA injury-report policy](https://official.nba.com/nba-injury-report-2026-27-season/) |

## Reason codes a run can emit

| Code | Meaning | What the operator sees | Where implemented | Source link |
| --- | --- | --- | --- | --- |
| `RIGHTS_NOT_CLEARED` | A record is not cleared for the intended use | Run suppressed, no picks | [`REASON_CODES`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) · [NBA Terms](https://www.nba.com/termsofuse) |
| `STALE_DATA` | An input is older than the freshness tolerance | Run suppressed, no picks | [`REASON_CODES`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| `NO_MARKET_SPEC` | The market and settlement rule are not written down | That forecast becomes `no_bet` | [`REASON_CODES`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| `NO_BENCHMARK_QUOTE` | No licensed quote exists for that market | That forecast becomes `no_bet` | [`REASON_CODES`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| `UNRESOLVED_INJURY` | Availability of a relevant player is unresolved | That forecast becomes `no_bet` | [`REASON_CODES`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) · [injury policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| `GATE_FAILED` | A promotion gate did not pass | That forecast becomes `no_bet` | [`REASON_CODES`](../engine/pipeline.py) | [source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |

## Running it today

```sh
# Synthetic smoke test: the rights gate refuses to publish, by design.
python3 scripts/run_pipeline.py \
    --inputs data/inbox-example \
    --out data/out-example \
    --now 2026-11-14T12:00:00Z \
    --run-id example-run

# Unit tests for the whole engine.
python3 -m unittest discover -s tests -t .
```

Both commands are safe to run on any machine with Python 3.11+. The engine has no third-party dependencies and makes no network calls.

| Verification | Result | Where | Source link |
| --- | --- | --- | --- |
| Engine test suite | 46 tests pass | [`tests/test_engine.py`](../tests/test_engine.py) | [test source](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_engine.py) |
| Example run | 2 synthetic events inside the horizon, 0 forecasts, 0 picks, run suppressed by `RIGHTS_NOT_CLEARED` | [`data/inbox-example`](../data/inbox-example/README.md) | [example folder](https://github.com/wingbangboozle1-lang/NBA4/tree/main/data/inbox-example) |

## What still has to be decided before this runs on real data

| Open item | Effect on automation | Where it is tracked | Source link |
| --- | --- | --- | --- |
| Feed adapters for schedule, injuries, results and prices | The pipeline has no way to obtain data by itself; adapters must be written for the licensed provider | Decision register Q2 | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Scheduling the daily job (cron, CI schedule or a task service) | The run is a single command today; the trigger is not chosen | Decision register Q10 | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| Where the site data is published from | GitHub Pages publishes static files only, so a run must write a static file that a commit or workflow then publishes | Decision register Q4 | [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| Refresh interval for injury snapshots | Determines the freshness tolerance and how many versions are archived | Decision register Q8 | [injury policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
