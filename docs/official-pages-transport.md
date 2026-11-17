# Official-page transport: what the scheduled job can actually reach

**Task BU/BV · session `arena/af666c53-nba4` · 2026-11-17**

## 1. The question

The `daily-refresh` job has been red on `main` since PR #59. Its run record says only
`unreachable`, and the board carried that as **BH-05** ("the `stats.nba.com` fetch gates
fail"), later classified as **P11-01** ("a fetch-phase fail-closed alarm, not a broken site
build"). What nobody could say was *why* the host was unreachable, because every session
that looked had done so from a sandbox whose egress is restricted to GitHub, npm and PyPI —
recorded as **P11-03**. A sandbox that cannot reach a host proves nothing about that host.

So this pass ran the observation on the machine that matters: a GitHub-hosted
`ubuntu-latest` runner, the same environment the failing job runs in.

## 2. Method

`scripts/capture_official_pages.py` requests each URL the job depends on and records, per
URL: the HTTP status, the content type, the byte length, the SHA-256, the headers actually
sent, and whether the body parses as the declared shape. It is triggered by
`.github/workflows/capture-official-pages.yml` and commits what it retrieves to
`data/official-pages/<date>/`.

Three rules keep the observation honest:

1. **A URL that is not reached is recorded as not reached, with the failure text.** It is
   never recorded as an empty feed. A timeout is not a zero-row result.
2. **A 200 is not evidence of data.** Every body is then judged by
   `scripts/official_pages.py`, which searches the payload for the declared number of rows
   and reports the verdict.
3. **Retrieval is separated from interpretation.** The capture script extracts no values;
   the parsers run offline against the captured files, so every claim below is
   reproducible from a clone with no network access.

Three capture runs were made (`2026-11-17T15:53Z`, `15:57Z`, `16:00Z`). Each URL below was
requested at least twice, except the batch-2 and batch-3 candidates.

## 3. Reachability from a GitHub-hosted runner

Every row's evidence is the committed manifest record, listed in the last column.

| Endpoint | Host | Result | Detail | Evidence |
| --- | --- | --- | --- | --- |
| [2026-27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | cdn.nba.com | REACHED | HTTP 200, 541,060 bytes, `%PDF-` magic; also 200 with minimal headers | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [Injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) | official.nba.com | REACHED | HTTP 200, 41,606 bytes, server-rendered: 44 dated report links in the body | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [Standings](https://www.nba.com/standings) | www.nba.com | REACHED | HTTP 200, 254,098 bytes — **but no standings rows in the body** | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [Team stats: traditional](https://www.nba.com/stats/teams/traditional) | www.nba.com | REACHED | HTTP 200, 322,560 bytes — **no rows in the body** | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [Team stats: opponent](https://www.nba.com/stats/teams/opponent) | www.nba.com | REACHED | HTTP 200, 322,497 bytes — **no rows in the body** | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [Team stats: advanced](https://www.nba.com/stats/teams/advanced) | www.nba.com | REACHED | HTTP 200, 322,497 bytes — **no rows in the body** | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [League standings API](https://stats.nba.com/stats/leaguestandingsv3) | stats.nba.com | NOT REACHED | no HTTP response: `TimeoutError` at 45 s and again at 25 s | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [Team-stats API](https://stats.nba.com/stats/leaguedashteamstats) | stats.nba.com | NOT REACHED | no HTTP response: `TimeoutError` at 45 s and again at 25 s | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| [Scoreboard API](https://stats.nba.com/stats/scoreboardv3) | stats.nba.com | NOT REACHED | no HTTP response: `TimeoutError` — the whole host, not one path | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| cdn static JSON (`/static/json/liveData/…`) | cdn.nba.com | NOT REACHED | HTTP 403 for the browser-like header set, the minimal set **and** the no-`User-Agent` set | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| data.nba.net | data.nba.net | NOT REACHED | `CERTIFICATE_VERIFY_FAILED`: certificate is not valid for that hostname | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| www.nba.com/api/v1/standings | www.nba.com | NOT REACHED | HTTP 404 — probed so the guess is recorded, not assumed | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |

## 4. The body verdicts

Reached is not the same as usable. Each body captured above was judged against the row
count the feed is required to supply, by `scripts/official_pages.py`.

| Page | HTTP | Rows in the raw body | Verdict | Why | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Standings](https://www.nba.com/standings) | 200 | 0 of 30 | NO_DATA_IN_BODY | the Next.js payload parses, but no list of 30 rows exists anywhere in it | [payload](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/standings.next.json) |
| [Traditional](https://www.nba.com/stats/teams/traditional) | 200 | 0 of 30 | NO_DATA_IN_BODY | same: the page is a shell and the browser fetches the table afterwards | [payload](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/teamstats_traditional.next.json) |
| [Opponent](https://www.nba.com/stats/teams/opponent) | 200 | 0 of 30 | NO_DATA_IN_BODY | same | [payload](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/teamstats_opponent.next.json) |
| [Advanced](https://www.nba.com/stats/teams/advanced) | 200 | 0 of 30 | NO_DATA_IN_BODY | same | [payload](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/teamstats_advanced.next.json) |
| [Injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) | 200 | 44 dated report links | CARRIES_ROWS | WordPress page, server-rendered: the links are in the raw response | [body](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/injury_index.head.html) |
| [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | 200 | — | CARRIES_ROWS | the body begins with `%PDF-`; row counting is the schedule parser's job | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |

The search in `find_row_lists()` is a search, not a fixed pointer: it walks the whole
payload for *any* list of exactly 30 objects. It found none on all four pages, and it does
find one on a synthetic payload built for the test, so the negative result is a property of
the pages and not of the search.

## 5. What changed in the job

`scripts/scheduled_refresh.py` now tries two transports for each of the four statistics
feeds and judges the **body**, not the status code:

1. the `stats.nba.com` JSON API it has always used, passing when the body yields 30 rows;
2. the official page a reader opens, passing only when `classify_body()` reports that the
   body really carries 30 rows.

The gate's `source_url` is always the page a human can open, never the API host, so the
citation on the site stays the official document. The run record gained a `transport_used`
field and an `attempts` list, so a red gate can be diagnosed from the record alone.

**The four gates stay red.** That is the honest outcome: transport 1 returns no response
and transport 2 returns a rendered shell. What changed is the reason, from
`unreachable` to `NO_DATA_IN_BODY`, which is the true cause and is now visible in the run
record and in the gate annotation.

The dangerous fix — point the feed at the HTML URL and count the 200 as a pass — is exactly
the **BH-06** false-green the board already recorded once. `classify_body()` exists to make
that fix impossible: a 200 that carries no rows is a failure with a reason.

## 6. Irregularities

| ID | Finding | Status | Source |
| --- | --- | --- | --- |
| BU-01 | `stats.nba.com` returns no HTTP response at all from a GitHub-hosted runner — three different endpoints, two timeouts, three separate runs. The four red fetch gates are caused by transport, not by our code or by a bad request. Resolving it is an owner decision (a licensed vendor under G0, or a headless-browser transport with its own terms review); it is not a code fix. | Open — owner decision | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| BU-02 | `workflow_dispatch` could not be invoked from this session's GitHub credentials (HTTP 403, "Resource not accessible by integration"), so the capture is triggered by a push to the branch instead. A future session wanting to re-run the probe on demand needs a token with `actions: write`. | Open | [workflow](https://github.com/wingbangboozle1-lang/NBA4/blob/main/.github/workflows/capture-official-pages.yml) |
| BU-03 | The injury-report index prints the link label without a leading zero on the hour ("1:00 a.m ET report") while the PDF filename zero-pads it (`Injury-Report_2026-11-17_01_00AM.pdf`). Any matcher that compares the two as strings will drop or mis-order a report. | Recorded, handled in the parser | [index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| BU-04 | The four official statistics pages return HTTP 200 with no statistics in the body. Switching the feed to those URLs and counting the 200 as success would manufacture a green check out of an empty feed — the BH-06 failure repeated. `classify_body()` is the guard. | Guarded, not fixable here | [payload](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/standings.next.json) |
| BU-05 | `cdn.nba.com` serves `/manage/**.pdf` (200) but refuses `/static/json/**` (403) for the browser-like header set, a minimal set and a no-`User-Agent` set alike. The refusal is path-level, not request-level, so no header change will open it. | Recorded | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| BU-06 | `data.nba.net` fails TLS hostname verification: the certificate served is not valid for that hostname. Do not use it as a transport. | Recorded | [manifest](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) |
| BV-01 | After the change the four gates are still red, with a truer reason. The check is a fail-closed alarm about data availability, and the site build is unaffected. | Open — owner decision | [workflow](https://github.com/wingbangboozle1-lang/NBA4/blob/main/.github/workflows/daily-refresh.yml) |

## 7. Files

| File | Role |
| --- | --- |
| [scripts/capture_official_pages.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/capture_official_pages.py) | the runner-side probe; records status, headers, bytes and SHA-256 per URL |
| [scripts/official_pages.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/official_pages.py) | declared page contracts, payload extraction, the body classifier and the injury-index parser |
| [tests/test_official_pages.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/tests/test_official_pages.py) | 44 offline tests over the captured bodies and hand-built fixtures |
| [.github/workflows/capture-official-pages.yml](https://github.com/wingbangboozle1-lang/NBA4/blob/main/.github/workflows/capture-official-pages.yml) | runs the probe and commits the evidence |
| [data/official-pages/2026-11-17/manifest.json](https://github.com/wingbangboozle1-lang/NBA4/blob/main/data/official-pages/2026-11-17/manifest.json) | the recorded reachability evidence |

## 8. What is deliberately not done

No standings row, team-statistic, probability, line or pick is published anywhere in this
pass. The rights gate (G0, NBA Terms §9) and the D-01/IR-T4 owner decision on publishing
NBA-derived model output are unchanged. This pass answers a transport question only: it
establishes which official documents a scheduled job can retrieve, and it makes sure that
question can never again be answered with a bare status code.
