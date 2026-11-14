# Official-observation snapshots

These files are verbatim, dated extractions of **official NBA publications**, kept so every row published on the site can be traced back to a document, a row and a fetch time. They are not a feed, not a dataset for modelling, and not evidence of any model output.

| File | What it holds | Official source | Source document timestamp | Fetched (UTC) |
| --- | --- | --- | --- | --- |
| `slate-2026-11-14.json` | Rows 231–252 of the official 2026–27 schedule PDF: the 22 games that tip off inside the requested three-day window from the observation time. | [2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | header: "AS OF AUGUST 13, 2026 \| SUBJECT TO CHANGE" | 2026-11-14T09:46:00Z |
| `injuries-2026-11-14-0430am.json` | Every row of the 2026-11-14 04:30 AM ET official injury report, including `NOT YET SUBMITTED` teams and cells lost at PDF page breaks. | [Injury report PDF, 2026-11-14 04:30 AM](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf) | header: "Injury Report: 11/14/26 04:30 AM" | 2026-11-14T10:20:00Z |
| `injuries-newest-pointer-2026-11-14.json` | Metadata only: the 11/14 05:00 PM ET report was the newest listed on the official index at 22:09 UTC. Its rows are not transcribed. | [Injury report index](https://official.nba.com/nba-injury-report-2026-27-season/) and [5:00 PM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_05_00PM.pdf) | header: "Injury Report: 11/14/26 05:00 PM" | 2026-11-14T22:09:00Z |

## Rules these files follow

1. **Provenance first.** Each file records `source_url`, the document's own header timestamp, `source_index_url`, `fetched_at_utc`, the extraction tool and per-cell extraction notes. A row without that chain is not publishable.
2. **No inference.** Values come from the document. Where the extraction lost a cell, the cell is empty and carries `unverified: true` plus a note. Nothing is back-filled from memory or from another report.
3. **Schedule-assisted repair, limited scope.** Date and tip time lost at a PDF page break may be filled from the independent official schedule PDF, and the published row then cites **both** documents. A lost **team** cell is never repaired this way for a player row.
4. **`NOT YET SUBMITTED` is a reporting state.** It is not "no injuries" and never becomes a status, probability or pick.
5. **Snapshots supersede.** A newer report invalidates an older one; each file keeps its own timestamp and is never relabelled "latest".
6. **No model output.** No originated line, probability, price, pick, minute estimate or production impact is stored here. Those stay blank and flagged until the rights and validation gates pass.

## Reading and re-checking

```bash
python3 -c "import json;d=json.load(open('data/snapshots/slate-2026-11-14.json'));print(len(d['games']),'games')"
python3 -c "import json;d=json.load(open('data/snapshots/injuries-2026-11-14-0430am.json'));print(sum(len(g['rows']) for g in d['games']),'injury rows')"
```

To re-check a value, open the `source_url`, find the row by game/matchup and player, and compare with the value on [Upcoming slate](../slate.html) or [Injuries & flow](../injuries.html). If the document has moved on (a newer report exists), the older snapshot is stale by definition — see [Flagged for review](../review.html).
