# Verification pass — session `arena/c38970c9-nba4` (2026-11-19)

Branch `arena/c38970c9-nba4`, based on `8e94c1f` (PR #80) and advanced through the merges
that landed while this session was working. Board tasks **DG–DS**; the claim is in
[`COORDINATION.md`](../COORDINATION.md) and was written before any work began.

This pass is deliberately narrow. It does not re-transcribe anything: the slate, injury,
results, standings and team-stat snapshots are other sessions' scopes and were refreshed
on 2026-11-17 and 2026-11-19 by `arena/5cca4190-nba4`, `arena/0fec89b5-nba4` and
`arena/639c095c-nba4`. What it does is check three things that were being **asserted**
rather than measured, and it records where a claim could not be checked at all.

Every finding below states which document was read, how it was read, and what the bytes
say. Where a value could not be confirmed, it is left blank and flagged — never inferred.

---

## 1. The schedule-PDF `" at "` claim does not reproduce (flag DS-01)

### What the repository says

Three documents state that the official 2026–27 schedule PDF prints no `at` token
between the two team cells on rows 215–259, and that this is why those rows needed
out-of-document corroboration for away/home order:

| Document | Text |
| --- | --- |
| [`scripts/build_snapshots.py`](../scripts/build_snapshots.py) line 111 | `The schedule PDF text prints no "at" token on rows 215-259` |
| [`data/snapshots/slate-2026-11-17.json`](../data/snapshots/slate-2026-11-17.json) → `basis.away_home_rule` | `The schedule PDF prints two team cells and, on rows 215-259, prints no 'at' or 'vs' token between them.` |
| [`review.html`](../review.html) (pass 7 / P7-02 wording) | `the schedule's away/home basis for rows 215–259` |

[`tests/test_snapshots.py`](../tests/test_snapshots.py) line 659 asserts the *rendered*
page never contains the phrase `prints no "at"`, so the site is consistent with itself;
the underlying claim was never re-measured against the PDF.

### What the PDF actually contains

The PDF is in this repository as captured evidence:
`data/official-pages/2026-11-17/schedule_pdf.pdf` — 541,060 bytes,
sha256 `5e82e37ef1b19e226dee57be69958b95b5694516280d3034aa7c1d64292b3570`,
captured by the `capture-official-pages` workflow on a GitHub-hosted runner
(record `schedule_pdf` in `data/official-pages/2026-11-17/manifest.json`, HTTP 200,
`application/pdf`). The same digest is the committed drift baseline
`data/snapshots/raw/ci/schedule-sha-baseline.txt`, so this is the exact document the
scheduled job compares against.

Three independent extractions were run on it:

| Extractor | Method | Window rows found | Rows with ` at ` |
| --- | --- | --- | --- |
| `pypdf` 5.1.0 | `page.extract_text()` default | 23 (rows 252–274) | 23 of 23 |
| `pypdf` 5.1.0 | `extract_text(extraction_mode="layout")` | 23 | 23 of 23 |
| `pdfminer.six` 20250506 | character stream grouped by `y0` baseline, sorted by `x0` | 23 | 23 of 23 |

Representative rows, verbatim (pypdf layout mode; page numbers are PDF pages):

```
252 p4 11/16/26 Phoenix        at       Denver           7:00 PM      9:00 PM
253 p4 11/17/26 New York       at       Toronto          7:30 PM      7:30 PM
257 p4 11/17/26 Utah           at       LA Clippers      8:00 PM     11:00 PM       NBC/PCK
260 p5 11/18/26 Milwaukee      at       Miami            7:00 PM      7:00 PM         ESPN
```

pdfminer's *default* `extract_text()` output is column-major (all row numbers, then all
dates, then all team cells), which is why a naive read of it shows no `at` next to a row
number — but that is an artefact of text ordering, not something the document prints.
Grouping pdfminer's characters by baseline restores the ` at ` on every row.

**Byte-level confirmation, no third-party library.** The committed PDF was also parsed with
the standard library alone: every Flate stream is inflated with `zlib` (287 streams) and the
literal string operands of the text operators are read in order. For row 253 the cells are:

```
253 | Tue. | 11/17/26 | New York | at | Toronto | 7:30 PM | 7:30 PM
```

which matches the page image a reader sees. A standalone `(at)` cell appears 1,197 times in
the document, and the row-253 (x=253.13, y=125.18) and row-255 (x=253.13, y=658.30) operands
both read `[(at)] TJ`. This is the same extraction path the new regression test uses, so the
test needs no PDF dependency and cannot skip.

**The test was proven to bite.** The PDF was temporarily patched so that row 253's cell read
`[(vs)] TJ` instead of `[(at)] TJ` (one stream recompressed, everything else untouched):

| Test | Result on the patched PDF | Result after restoring the original |
| --- | --- | --- |
| `test_every_window_row_has_away_at_home_cells` | **FAIL** — `row 253: no ' at ' cell` | pass |
| `test_published_window_rows_match_the_pdf_cells` | **FAIL** — `'vs' != 'at'` | pass |
| `test_pdf_is_the_document_the_drift_gate_compares` | **FAIL** — sha256 changed | pass |

The file was restored and its sha256 re-checked against the drift baseline
(`5e82e37e…b3570`) before anything was committed. A first version of the extractor stopped at
the first `endstream` byte sequence, which lands inside incompressible binary data in this
document; that bug was caught by the round-trip check, fixed to honour `/Length`, and the
finding above is the corrected run.

### Independent check of the published slate rows

To be sure the published table was not itself built on a misreading, all 21 published
window rows (`data/snapshots/slate-2026-11-17.json`, rows 253–273) were compared field by
field with the PDF text: away team, home team, date, and both printed time columns.

**Result: 21 rows compared, 0 field mismatches.** The published table is correct. It is the
*explanation* attached to it that is wrong, and with it three derived statements:

* rows 253–259 do print ` at `, so their away/home order is **directly readable** from the
  PDF and does not depend on the injury report or the games-page slug (those agree with the
  PDF on all 21 rows, so no published value changes);
* rows 260–273 print ` at ` as well, so the split at row 260 in `basis.away_home_rule` does
  not exist;
* `scripts/build_snapshots.py` line 111 and the `printed order only` note it renders rest on
  the wrong premise.

The same wrong premise appears in four earlier verification logs
(`docs/verification-pass-7dfeb9eb.md`, `-aea8c363.md`, `-b9938e48.md`, `-bcb4f9a7.md`).
They are historical records and are **not rewritten**; they are cross-referenced here and
listed on the Flagged for Review page.

**Why it happened — hypothesis, labelled as such:** the earlier passes read the PDF through
a markdown text extractor whose cell ordering interleaved row numbers with team cells
(`docs/verification-pass-0fec89b5.md` records `fetch_page (PDF text extraction, chunk 2)`),
and a column-major reading does lose the ` at `. The claim was then copied forward without a
second extractor. This repository has since captured the raw PDF, which is what makes the
check possible at all; the pass that made the claim did not have the bytes to check.

### Disposition

* Nothing is edited in another session's files. `scripts/build_snapshots.py`,
  `data/snapshots/slate-2026-11-17.json` and the existing `review.html` sections belong to
  other sessions; the correction request is logged in `COORDINATION.md` and on the
  Flagged for Review page (flag **DS-01**).
* A **regression test** now measures the PDF itself, so the wrong statement cannot be
  reintroduced silently: `tests/test_snapshots.py::SchedulePdfAtTokenTests` reads the
  committed PDF with both extractors and fails if any window row loses its ` at `.

---

## 2. Capture-workflow reachability (flag DS-02)

Measured, not assumed:

| Observation | Evidence |
| --- | --- |
| the workflow was triggered only by pushes to `arena/af666c53-nba4` | the file before this session's change, `on.push.branches` |
| that branch merged as PR #71 on 2026-11-17T16:17:36Z | `gh pr view 71` |
| after the merge the workflow could not be started by any push | no other branch was listed |
| on-demand start was refused to this session's token | `gh workflow run …` → `HTTP 403: Resource not accessible by integration` (reproduced 2026-11-19T07:07Z) |
| the repaired trigger works | run [44477290934](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/44477290934) started on this branch at 2026-11-19T07:08:15Z from a push that touched `scripts/capture_official_pages.py` |

So the "transport evidence" path in the repository was dead for two days, and the
`daily-refresh` job's four red statistics gates were being explained by a capture that could
only be reproduced by editing the workflow file itself. The repair keeps `main` in the
trigger list and adds `arena/**`, checks out `${{ github.ref }}` and pushes back to the
branch the run started from, so a capture can never land on `main` by accident.

The 403 is a property of the credential, not of the file: `workflow_dispatch` needs
`actions: write` on the token that starts the run. The push path needs no extra permission
and is therefore the path the repository relies on. Both are recorded.

---

## 3. What could not be verified in this sandbox (flag DS-03)

The sandbox this pass ran in has outbound access to GitHub, npm and PyPI only. Measured
2026-11-19T06:56Z with `curl -sS -o /dev/null -w "%{http_code}"`:

| Host | Result |
| --- | --- |
| `github.com` | 200 |
| `www.nba.com` | no response (exit 000) |
| `stats.nba.com` | no response |
| `cdn.nba.com` | no response |
| `official.nba.com` | no response |
| `ak-static.cms.nba.com` | no response |

Consequences, stated plainly:

* **No NBA page was fetched by this session.** Every NBA statement in this pass is read
  from a document already committed to the repository (the captured PDF, and snapshots
  other sessions captured on GitHub-hosted runners or with their own fetch tooling).
* The 2026-11-19 01:45 AM ET injury report was **not** re-read from
  `ak-static.cms.nba.com`; its transcription is checked only for internal consistency (§4)
  and its external re-read stays open.
* The schedule PDF in this repository is the **August 13, 2026** issue
  (`source_document_header`: `2026-27 NBA REGULAR SEASON SCHEDULE AS OF AUGUST 13, 2026 |
  SUBJECT TO CHANGE`). A schedule re-issued after that date would not be visible here unless
  the capture workflow runs again; the drift gate is exactly that alarm.

---

## 4. Internal consistency checks on the 11/19 injury snapshot

Read from `data/snapshots/injuries-2026-11-19-0145am.json` (another session's file, not
edited here):

| Check | Result |
| --- | --- |
| `row_count` vs rows inside `games` + `unattributed_rows` | 44 vs 42 + 2 = 44 ✅ |
| `games_counted` vs `len(games)` | 13 vs 13 ✅ |
| matchup codes vs the official schedule row cited per block | 13 of 13 match the `schedule_row` recorded in each block ✅ |
| printed tip vs schedule tip where both exist | 12 blocks agree (`08:00 (ET)` vs `8:00 PM`); POR@MIL prints no tip cell and records `tip_et_from_report: ""` ✅ (blank kept blank) |
| statuses | 21 NOT YET SUBMITTED rows keep a blank status and the printed reason text; 17 Out, 2 Available, 2 Questionable ✅ |
| orphan rows | 2 (Kuminga, Pullin) carry no date/time/matchup/team and are stored unassigned with an unverified flag ✅ |
| NYK@MIN block | 4 Minnesota rows, 0 New York rows — the absence is recorded and not interpreted ✅ |

**Not checkable here:** whether every printed cell matches the PDF. The PDF is not in the
repository and the host is unreachable from this sandbox. That check stays open and is
listed as such on the review page.

---

## 5. Numbers this pass re-measured

| Measurement | Command | Result |
| --- | --- | --- |
| unit tests | `python3 -m unittest discover -s tests -t .` | 547 before this session's additions (§6) |
| site check | `python3 scripts/check_site.py --with-tests` | PASS, 16 pages, 652 HTML data rows, 1310 Markdown data rows |
| snapshot regeneration | `python3 scripts/build_snapshots.py --check` | exit 0, `unchanged team-stats.html` |
| refresh gates, offline | `python3 scripts/scheduled_refresh.py --mode offline` | 3/3 PASS, `rebuild_allowed=False` |
| refresh gates, probe | `… --mode probe --now 2026-11-19T07:00:00Z` | 5/12 PASS, exit 1 — every NBA host fails from this sandbox with `TLS/SSL connection has been closed` |
| nightly CI on `main`, 2026-11-18 | Checks API annotations for run 44293154114 | `gates 10/14 passed; failed=standings_fetch,teamstats_traditional_fetch,teamstats_advanced_fetch,teamstats_opponent_fetch` |

The CI reading matters for the strategy work: **on a GitHub-hosted runner the schedule and
injury feeds already succeed.** Only the four statistics transports are red, and they are red
for a measured reason — `stats.nba.com` returns no response, and the `www.nba.com` pages
return HTTP 200 with a rendered shell that carries no rows.

---

## 6. This session's own additions (each with its test)

| Addition | Test | What is asserted |
| --- | --- | --- |
| `SchedulePdfAtTokenTests` (`tests/test_snapshots.py`) | 4 tests | the committed official PDF prints ` at ` on every window row under two extractors; the 21 published rows match the PDF field for field |
| `CaptureWorkflowContractTests` (`tests/test_official_pages.py`) | 4 tests | the capture workflow has an on-demand trigger, no single-branch pin, checks out and pushes to the run branch, and every probe target declares a kind and an https URL |
| `CapturedManifestReproducibilityTests` (`tests/test_official_pages.py`) | 2 tests | every stored body hashes to its manifest value (or is a declared truncated head); the stored schedule PDF equals the drift baseline |

---

## 7. Sources

| Claim in this pass | Source | How it was read |
| --- | --- | --- |
| every window row prints ` at ` | [official 2026–27 schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) | the captured copy in this repository, three extractors (§1) |
| the PDF is the August 13, 2026 issue | same PDF, extracted header text; `source_document_header` in `data/snapshots/slate-2026-11-17.json` | extracted text |
| the drift baseline is the same document | `data/snapshots/raw/ci/schedule-sha-baseline.txt` vs the stored PDF's sha256 | recomputed |
| the workflow was unreachable | PR #71 merge record; the pre-change workflow file | `gh pr view 71`; file history |
| on-demand start is refused to this token | `gh workflow run …` response | reproduced twice |
| nightly CI gate counts | run 44293154114 annotations via the Checks API | API read only (the raw log host returns `EOF` from this sandbox) |
| the 11/19 injury transcription's internal consistency | `data/snapshots/injuries-2026-11-19-0145am.json` | computed (§4) |

**Not read from an official source in this pass:** any live NBA page. That limit is flag
DS-03 and applies to this whole document.

---

## 8. Transport re-measured on 2026-11-19 (flag DS-04) — the reason is now exact

The `capture-official-pages` workflow was repaired (§2) and run on a GitHub-hosted runner
at 2026-11-19T07:08Z. The manifest is `data/official-pages/2026-11-19/manifest.json`
(run [44477290934](https://github.com/wingbangboozle1-lang/NBA4/actions/runs/44477290934),
`conclusion: success`). Twenty-one targets were probed. The result, with the numbers read
from that manifest and the stored bodies:

| Surface | 2026-11-17 | 2026-11-19 | What the body holds |
| --- | --- | --- | --- |
| official schedule PDF | 200, 541,060 B, sha `5e82e37e…` | 200, 541,060 B, **sha `5e82e37e…` (identical)** | the `SUBJECT TO CHANGE` August 13 issue, unchanged for two days |
| injury-report index | 200, 41,606 B | 200, 36,940 B | server-rendered and it does carry its data: 44 distinct dated report links on 11/17 (newest listed 10:45 AM) vs 9 on 11/19 (newest listed **02:00 AM**) |
| `www.nba.com/standings` | 200, 254,098 B | 200, 225,385 B | **no** statistics payload |
| `www.nba.com/stats/teams/{traditional,opponent,advanced}` | 200, ~322 KB | 200, ~293 KB | **no** statistics payload |
| `stats.nba.com` origin | *not probed* | **200, 371,561 B** | a Next.js shell for `/stats/players/traditional`; still no statistics payload |
| `stats.nba.com` JSON endpoints (3) | no response (timeout 45 s) | no response (timeout 25 s) | — |
| `cdn.nba.com/static/json/**` (5 paths) | 403 | 403 (all five) | path-level refusal, not header-level |
| `data.nba.net` | certificate mismatch | certificate mismatch | — |
| `www.nba.com/api/v1/standings` | 404 | 404 | — |

**The important correction to the earlier reading.** A first version of this session's
auditor counted team names in the body and reported "carries statistics" for all four
statistics pages. That was wrong, and the reason is instructive: every one of those pages
ships a navigation/footer blob that names all 30 teams. Two further markers were tried and
also failed — `<option value="W">Wins</option>` in the page's own filter dropdown matched a
"W column", and 426 one-decimal numbers in the inline **SVG path data** matched "rendered
numbers". The marker that survives all three traps is a structural row key of the feed
itself. Measured on both dates: `teamName` appears 10 times (navigation), while `rowSet`,
`headers`, `teamId`, `teamTricode` and `gamesPlayed` appear **0** times in every capture.

So the verdict is unchanged — **the four statistics surfaces return HTTP 200 and carry no
statistics** — but it is now measured three ways and guarded by tests
(`CaptureAuditMarkerTests`), instead of resting on the phrase "0 of 30 rows".

**Why this matters beyond the gate colour:** the source of the four statistics feeds is not
merely *unreachable*. It is reachable and empty, which means a licensing/transport decision
cannot be "retry harder"; it needs a data source the NBA actually publishes as data
(the Stats FAQ's own wording is quoted on the Sources page) or written permission. That is
decision **DP-01** in §9.

**`stats.nba.com` answers.** The 2026-11-17 manifest recorded timeouts for the JSON
endpoints; the 2026-11-19 capture shows the *origin document* returning 200 in 371 KB. Both
are true: the host answers plain page requests and times out on its stats API paths from a
runner. This is recorded rather than resolved, because settling it needs a request the
runner does not make (a browser session with the site's own headers), and that is an owner
decision, not a measurement this session can complete.

---

## 9. Finding DS-05: the newest official injury report is not in any snapshot

The 2026-11-19 capture's index lists a 2026-11-19 **02:00 AM ET** report as the newest
entry (the 11/19 index carries 9 distinct dated links, newest `02_00AM`). The published
transcription in this tree is `injuries-2026-11-19-0145am.json` — the **01:45 AM** report,
captured at 06:58Z by another session before the 02:00 revision was listed.

Consequences, stated exactly:

* the 01:45 transcription is not wrong; it was correct when it was made;
* the 02:00 revision supersedes it, and nothing in the tree records the difference. The
  consecutive-report diff for that pair does not exist;
* the freshness gate (`injury_transcription_age`) passes today only because the 01:45 file
  is 0.03 h old at the moment it was written. It will fail again 24 h later, and it will
  have passed *while the newest report was not the published one*.

This is the same class of defect as the 11/19 CA-01 flag another session opened, one
revision later. It is recorded as **DS-05** with the exact links, so the next refresh cycle
transcribes 02:00 AM (or newer) and diffs against 01:45 rather than starting fresh.
The index link list is the authority here; the PDF itself was not fetched by this session
(§3), so the 02:00 report's rows are **not** transcribed and no value from it is published.

### Decision DP-01 — which is the real blocker, and what would clear it

The measurements in §8 reduce the open transport question to a decision that only the
owner can take. Options, with what each would require and what it would cost:

| Option | What it needs | Evidence it would produce | Cost / risk |
| --- | --- | --- | --- |
| A. Licensed statistics feed | a contract with the NBA (or an authorised distributor) that permits the intended use | the four feeds become authorised inputs; G0 can clear | money, time; the Terms §9 gambling clause still governs any betting use |
| B. Written permission for this specific use | a written reply from the NBA permitting it | the same, for a non-commercial reading | the Terms FAQ says statistics are not available for download for personal or academic use, so a refusal is the likely answer |
| C. A public non-NBA data source, re-verified to the same standard | a source that publishes its own data under a licence that permits this use, plus a row-level provenance chain for every value | rows that are *not* NBA-published values, clearly labelled | the site can no longer call them "official NBA statistics"; the current verification standard would have to change |
| D. Stay observation-only | nothing further | the schedule PDF, the injury report and the game pages — all reachable, all quoted | the model never gets its statistical inputs; every pick stays NO PICK |

**Recommendation (not a decision):** D now, A when there is a budget, with B as a
low-cost attempt in parallel. C is the only option that would let the model run without a
contract, and it changes the site's central claim (official values) — so it needs the owner's
explicit choice, which is why it is a decision and not a suggestion.

**What this session did not do:** it did not transcribe the 02:00 AM report, did not change
any snapshot, and did not publish any value derived from a document it could not fetch.
