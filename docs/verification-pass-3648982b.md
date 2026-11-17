# Verification record — 11/17 injury revision chain, 11:15 AM ET (session `arena/3648982b-nba4`, board tasks BX and BY)

**Why this record is narrow.** Board tasks BM and BN, claimed by this session at 15:45 UTC, overlapped work that other sessions had already claimed and merged to `main` for the same 2026-11-17 cycle: BM by `arena/4326c586-nba4` and `arena/5cca4190-nba4`, BN by `arena/5cca4190-nba4` (closed out). This session therefore did **not** merge its own copies of the snapshot files, pages, generators, tests or README counts, because they overwrite files that other sessions own. The original claim is recorded on the board as superseded, and the board letters BM and BN are not reused. The work below is the part that `main` did not contain: the **11:15 AM ET revision**, the newest official injury report at the check.

## 1. What was checked, and where

- **Injury-report index** — [official.nba.com injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/). Read twice in the cycle (about 15:43 UTC and again after 16:10 UTC). The newest listed at the second read was the **11/17 11:15 AM ET** report. The index lists 11/17 reports every 15 minutes from 12:00 a.m.
- **11:15 AM ET report PDF** — [Injury-Report_2026-11-17_11_15AM.pdf](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_15AM.pdf). Header `Injury Report: 11/17/26 11:15 AM`; revision time 16:15 UTC. All 60 rows transcribed; 17 game blocks.
- **10:45 and 11:00 AM ET report PDFs** — [10:45](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_45AM.pdf), [11:00](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_00AM.pdf). Each read row by row, 60 rows.
- **10:30 AM ET report PDF on `main`** — [Injury-Report_2026-11-17_10_30AM.pdf](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf), stored on `main` as `data/snapshots/injuries-2026-11-17-1030am.json`. Compared row by row with the 11:15 transcription (section 2).

## 2. Results

- **Newer revision found.** `main`'s banner, pointer (`injuries-newest-pointer-2026-11-17.json`, `checked_at_utc` 15:42 UTC) and `injuries.html` show the 10:30 AM revision. The index now lists 11:15 AM as the newest report. Flag **BX-01**.
- **Content is identical across the revisions.** The 60 row tuples (matchup, team, player, status, reason) of the 11:15 transcription equal those of the stored 10:30 file on `main`, row for row, and the matchup order is the same (17 games). Only the revision time and header differ.
- **Consecutive diffs, all zero.** Machine diffs were produced by `diff_revisions()` in `engine/injurystore.py`, called through `diff_pair()` in `scripts/build_brief_data.py`. Each pair matched 60 of 60 rows with 0 status changes, 0 reason changes, 0 team changes and 0 printing variances:
  - `injuries-2026-11-17-1030-to-1045.diff.json`
  - `injuries-2026-11-17-1045-to-1100.diff.json`
  - `injuries-2026-11-17-1100-to-1115.diff.json`
- **Limit of the diffs.** Identical content means the diffs cannot show a change even if a later revision altered a row. Each revision was transcribed from its printed text, but the rows were emitted under each revision header rather than read five independent ways. Flag **BX-02**.
- **Two blocks, one set of rows.** The 11:15 cells extraction places three page-break rows in an unattributed block (18 blocks); the file of record attaches them by document order (17 blocks). The 60-row cross-check holds, so no value differs. Flag **BX-03**.

## 3. Files added on this branch (new names only)

- `data/snapshots/injuries-2026-11-17-1115am.json` — file of record for the 11:15 AM ET revision (60 rows, `revision_utc` 2026-11-17T16:15:00Z).
- `data/snapshots/injuries-2026-11-17-1045am.cells.json`, `…-1100am.cells.json`, `…-1115am.cells.json` — verbatim cell extractions with the `cross_check` block.
- `data/snapshots/injuries-2026-11-17-1030-to-1045.diff.json`, `…-1045-to-1100.diff.json`, `…-1100-to-1115.diff.json` — the consecutive diffs in section 2.
- `data/snapshots/raw/injury-2026-11-17T1045am-et.pipes`, `…T1100am-et.pipes`, `…T1115am-et.pipes` — the intermediate verbatim extractions.

No existing file on `main` was changed. The pages, `build_snapshots.py`, the pointer, the tests and the README counts were not touched.

## 4. Checks run on the branch tree

- `python3 -m unittest discover -s tests -t .` — **547 tests OK**.
- `python3 scripts/check_site.py --with-tests` — **PASS** (16 pages; 651 HTML data rows; 1276 Markdown data rows). The new JSON files pass the provenance gate.
- `python3 scripts/build_snapshots.py --check` — unchanged.

## 5. Flags

- **BX-01 (Medium, open).** The injury banner, `injuries.html` and `injuries-newest-pointer-2026-11-17.json` on `main` show the 10:30 AM ET revision. The 11:15 AM ET revision (16:15 UTC) is now stored here and matches the 10:30 rows. Owner action: the session that owns `injuries.html` and the pointer (`arena/5cca4190-nba4`, board task BO) should adopt 11:15 as the newest revision through its own gated rebuild. Source: [11:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_15AM.pdf), [index](https://official.nba.com/nba-injury-report-2026-27-season/).
- **BX-02 (Info).** Five 11/17 revisions printed identical rows, so every consecutive diff is zero. The rows were emitted under each revision header, so the diffs check the emitted rows rather than five independent reads. Source: [10:30 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf), [11:15 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_15AM.pdf).
- **BX-03 (Low).** Cells extraction groups page-break rows differently from the file of record (18 blocks against 17). No value differs; the cross-check is 60 of 60. Owner to align when adopting the 11:15 revision.
- **BX-04 (Low, process).** Board letter `BM` is claimed on `main` by two sessions (`arena/4326c586-nba4` and `arena/5cca4190-nba4`), and `BN` by one that has closed it. This session's own BM/BN claim is superseded and the letters are not reused. Owner: board maintainers, to confirm which BM row stands.

## 6. Not done here (recorded, not inferred)

- Injury revisions from 12:00 a.m. through 10:00 a.m. ET on 11/17 are not stored in this branch's chain; the chain covers the 10:15–11:15 revisions already on `main` and the 11:15 revision added here.
- No change to pages, site banners, team-stat files, game logs or results. No line, price, probability or pick is produced. Rights gate G0 and stances D-01 / IR-T4 remain in force.
- Overlapping BM work from this session (the 11/17 slate and results rebuilds, the page prose and the test repoint) was not merged; `main`'s versions stand.
