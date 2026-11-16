# The scheduled-job refresh gate

Brief item: *"Extend the scheduled job to refresh the official schedule,
standings, team statistics and injury report for each rolling slate, then
rebuild only after freshness and provenance gates pass."*

Module: [`engine/refresh.py`](../engine/refresh.py) ·
hook: [`engine/pipeline.py`](../engine/pipeline.py) `refresh_gate` ·
CLI: `python3 -m engine.cli refresh`

## Why the order is the whole point

Refresh first, rebuild second. A rebuild run on a stale injury report produces a
number that looks current and is not, which is worse than producing nothing:
nothing is visibly nothing, while a stale number has to be caught by someone who
already knows it is wrong.

The gate is therefore a separate, binary decision taken **before** any modelling
happens, and it is recorded so a later reader can see why a slate was or was not
rebuilt.

## What a feed declaration is

A [`FeedSpec`](../engine/refresh.py) is a declaration, not a result. It says
which official document the job must refresh, how old that document may be,
whether the document must print its own revision time, and how many rows and
chunks a complete read has.

| Feed | Official document | Freshness tolerance | Document stamp required | Completeness rule | Source |
| --- | --- | --- | --- | --- | --- |
| schedule | [2026-27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | 24 h | no (it prints an "as of" date, not a revision clock) | - | [schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| standings | [NBA.com standings](https://www.nba.com/standings) | 12 h | no | 30 rows | [standings](https://www.nba.com/standings) |
| team_stats_traditional | [Teams Traditional](https://www.nba.com/stats/teams/traditional) | 12 h | no | 30 rows | [traditional](https://www.nba.com/stats/teams/traditional) |
| team_stats_opponent | [Teams Opponent](https://www.nba.com/stats/teams/opponent) | 12 h | no | 30 rows | [opponent](https://www.nba.com/stats/teams/opponent) |
| team_stats_advanced | [Teams Advanced](https://www.nba.com/stats/teams/advanced) | 12 h | no | 30 rows | [advanced](https://www.nba.com/stats/teams/advanced) |
| injuries | [NBA injury report](https://official.nba.com/nba-injury-report-2026-27-season/) | 90 min | **yes** | - | [injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| results | [NBA games](https://www.nba.com/games) | 6 h, optional pre-tip | no | - | [games](https://www.nba.com/games) |

The tolerances are **operating choices, not measured truths.** They are stated
in one place (`default_feed_specs`) so a reviewer can disagree with them without
reading code. The injury-report tolerance is the tightest because the report is
revised through the day; the team-stat tolerances are the widest because those
pages change once per game day.

## How freshness is measured

Age is measured from the **document's own timestamp** when the document prints
one, because that is when the information became true. The injury-report PDF
prints its revision (for example `Injury Report: 11/15/26 06:15 AM`), so a
revision published five hours ago is five hours old no matter when we fetched
it.

Retrieval time is the fallback for documents that print no stamp — which is the
case for the standings and the three team-stat pages. The fallback is recorded
as the weaker basis in every verdict (`age_basis`) and never silently upgraded
to "fresh".

A retrieval recorded *before* the document's own timestamp is refused rather
than repaired: an impossible provenance chain means something upstream is
wrong, and the gate's job is to surface that, not to smooth it over.

## States, and which ones block

Every state below blocks a **required** feed except `PASS`.

* **`PASS`** — within tolerance, complete, and cleared.
* **`NOT_RETRIEVED`** — no observation was recorded. A missing feed is not an
  empty feed.
* **`STALE_DOCUMENT`** — the document's own timestamp is older than the
  tolerance.
* **`STALE_RETRIEVAL`** — no document stamp, and the retrieval time is older
  than the tolerance.
* **`NO_DOCUMENT_TIMESTAMP`** — the declaration requires a stamp and none was
  recorded.
* **`INCOMPLETE_ROWS`** — fewer rows read than declared, or the count was not
  reported at all.
* **`INCOMPLETE_CHUNKS`** — fewer chunks read than the document has.
* **`RIGHTS_NOT_CLEARED`** — the permission flag is not set, which is rights
  gate G0 under [NBA Terms of Use](https://www.nba.com/termsofuse) sections 1
  and 9.
* **`RETRIEVED_BEFORE_PUBLISHED`** — the provenance chain is impossible.
* **`URL_MISMATCH`** — observed from a different document than the one declared.

Optional feeds that fail are reported as warnings and do not block. The results
feed is optional pre-tip because the slate has not been played yet; settlement
is gated separately by
[`engine/officialresults.py`](../engine/officialresults.py).

## Using it

```sh
# With no observations recorded the answer is a refusal, not a neutral state.
python3 -m engine.cli refresh --now 2026-11-16T12:00:00Z
# exit 1, "NO REBUILD - the slate is not rebuilt on a failed refresh"

# With a manifest, each feed is gated and the reason is printed.
python3 -m engine.cli refresh --now 2026-11-16T12:00:00Z --observations feeds.json
```

The manifest schema (`feeds.json`):

```json
{
  "observations": [
    {
      "feed_id": "injuries",
      "url": "https://official.nba.com/nba-injury-report-2026-27-season/",
      "retrieved_at": "2026-11-16T11:58:00Z",
      "document_timestamp": "2026-11-16T11:15:00Z",
      "rows_read": 101,
      "chunks_read": 4,
      "allowed_use": false,
      "note": "newest revision listed at 11:15 ET"
    }
  ]
}
```

`allowed_use` defaults to `false`. Until the operator sets it after clearing the
data rights, every feed fails with `RIGHTS_NOT_CLEARED` and the rebuild never
runs — which is the correct behaviour for this repository today.

## What this module does not do

* It does not fetch. It is the decision layer a fetcher reports into, so a run
  can be replayed and audited from its observation record alone.
* It does not retry, back off or schedule. Those belong to the job runner
  described in [docs/automation.md](automation.md).
* It does not hold NBA data. The URLs are declarations; nothing in the module
  asserts what those documents currently contain.
