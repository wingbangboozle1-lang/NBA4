# Verification pass 7ce5c0cc — 2026-11-16 daily refresh + close-outs

Session `arena/7ce5c0cc-nba4`, branch `arena/7ce5c0cc-nba4`, tasks BB–BE.
This log records every fetch of this pass, what was decided from it, and every
correction made during the pass. Snapshot writers
(`scripts/_gen_7ce5c0cc.py`, `scripts/_gen_7ce5c0cc_b.py`,
`scripts/_gen_7ce5c0cc_c.py`, `scripts/_gen_7ce5c0cc_site.py`) name this file as
their provenance record. Post-refresh count on this branch: **300 unit tests OK**
(47+43+17+10+135+48); after the parallel session's scheduled-refresh suite merged
into the integration branch the total is **327 across seven suites**, site check
PASS (16 pages, 517 HTML data rows, 831 Markdown data rows).

## 1. Fetches performed (2026-11-16, UTC times as recorded)

| What | URL | Time (UTC) | Outcome | Official source |
| --- | --- | --- | --- | --- |
| Injury-report index | https://official.nba.com/nba-injury-report-2026-27-season/ | 14:31 | newest listed report = 09:15 a.m. ET; reports every 15 min; later reports may appear | [Index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Injury PDF 09:15 AM | https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf | 14:31 | 72 player rows / 13 matchup blocks transcribed verbatim | [PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| Injury PDF 09:00 AM | https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_00AM.pdf | 14:31 | 72 rows; consecutive-revision diff computed | [PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_00AM.pdf) |
| Schedule PDF (August release) | https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf | 14:33 | window rows 245–269 transcribed; header "AS OF AUGUST 13, 2026 / SUBJECT TO CHANGE" | [PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| Games page 2026-11-16 | https://www.nba.com/games?date=2026-11-16 | 14:34 | 8 game cards; card records matched the standings transcription | [Page](https://www.nba.com/games?date=2026-11-16) |
| Games page 2026-11-15 | https://www.nba.com/games?date=2026-11-15 | 14:34 | 9 finals; cards carry no quarter scores (flag P9-05) | [Page](https://www.nba.com/games?date=2026-11-15) |
| Games page 2026-11-17 | https://www.nba.com/games?date=2026-11-17 | 14:35 | 5 cards, rows 253–257; tips confirm AN-02; records matched | [Page](https://www.nba.com/games?date=2026-11-17) |
| Games page 2026-11-18 | https://www.nba.com/games?date=2026-11-18 | 14:35 | 12 cards, rows 258–269; new tip conflict P9-04 on rows 266/267 | [Page](https://www.nba.com/games?date=2026-11-18) |
| Standings | https://www.nba.com/standings | 14:36 (chunks 0+1) | 30 rows + tie-break text; internal checks computed (below) | [Page](https://www.nba.com/standings) |
| Team stats — advanced | https://www.nba.com/stats/teams/advanced | 14:41–14:44 | 30 rows × 20 cells (RANK dropped); Dallas row split at chunk seam, rejoined | [Page](https://www.nba.com/stats/teams/advanced) |
| Team stats — opponent | https://www.nba.com/stats/teams/opponent | 14:44–14:48 | 30 rows × 26 cells (RANK dropped); Detroit row split at chunk seam, rejoined | [Page](https://www.nba.com/stats/teams/opponent) |
| Team stats — traditional | https://www.nba.com/stats/teams/traditional | 14:52 | this session's chunk-0 fetch served filter controls only; NOT transcribed here (flag P9-06). A parallel pass (docs/team-stats-recheck-cbc8e41a.md) read all five chunks and verified 30 of 30 rows; read gap closed by that evidence, publication stays an owner decision | [Page](https://www.nba.com/stats/teams/traditional) |
| Standings re-read (spot check) | https://www.nba.com/standings | 15:0x | LAL 12-2, SAS 12-2, BOS 11-2 as printed; transcription confirmed cell-for-cell on all rows of the East table and the visible West rows | [Page](https://www.nba.com/standings) |

## 2. Checks computed in this pass (not asserted)

| Check | Result | How | Official source |
| --- | --- | --- | --- |
| Standings internal: HOME+ROAD+NEUTRAL = GP per row | 30/30 | `scripts/_gen_7ce5c0cc_b.py` write log | [Standings](https://www.nba.com/standings) |
| League W = league L, home+road+neutral = 394 team-game lines | 197 = 197; 196+196+2 | same | [Standings](https://www.nba.com/standings) |
| GP/W/L agree: standings vs advanced vs opponent | 30/30 | computed after writing all three files | [Advanced](https://www.nba.com/stats/teams/advanced) |
| OffRtg − DefRtg = NetRtg within rounding | 30/30 | computed | [Advanced](https://www.nba.com/stats/teams/advanced) |
| DefRtg vs Opp PTS best-five sets | same five teams (BOS, MIN, NYK, SAS, OKC), order differs | computed; exact equality NOT claimed (per-100 vs per-game denominators) | [Opponent](https://www.nba.com/stats/teams/opponent) |
| 09:00 → 09:15 injury diff | 72→72 rows; 0 status/reason/team changes; 1 printing variance (Mathurin) | `scripts/_gen_7ce5c0cc.py` | [09:15 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| 11/15 results: 9 finals, winner = larger printed final | 9/9 | `scripts/_gen_7ce5c0cc_b.py` | [Games 11/15](https://www.nba.com/games?date=2026-11-15) |
| Home-win rate from HOME splits | 102-94 = 0.5204 → +0.614 pts (PROPOSED, NOT APPLIED) | `scripts/_gen_7ce5c0cc_c.py` (NormalDist inverse) | [Standings](https://www.nba.com/standings) |
| Engine suite after review fixes | 300 tests OK on the branch (47+43+17+10+135+48); 327 across seven suites after the parallel scheduled-refresh suite merged | `python3 -m unittest discover -s tests -t .` | [Repo tests](https://github.com/wingbangboozle1-lang/NBA4/tree/main/tests) |

## 3. Corrections made during the pass (transparently, before publication)

* The first draft of `team-stats-2026-11-16.json`'s `cross_checks` claimed the
  traditional page "was re-read (30 rows visible)" and claimed an equal-value
  DefRtg/Opp-PTS match. Both were wrong: the traditional extraction serves no
  rows (P9-06), and DefRtg is per 100 possessions while Opp PTS is per game. The
  claim text was corrected to what is computed (set-level agreement), and the
  correction is recorded here rather than hidden.
* A mid-pass suspicion that the Lakers row (12-2) was mis-transcribed was
  resolved by re-reading the standings page: 12-2 is what the page prints; the
  transcription stands. The suspicion itself is logged so nobody re-litigates it.
* `scripts/build_snapshots.py` diff-render labels (previously hard-coded
  "06:00/06:15") were made data-driven from the diff file's revision labels.

## 4. Flags opened by this pass (all on review.html)

| Flag | State | What | Official source |
| --- | --- | --- | --- |
| P9-01 | closed | 09:15 report prints "Mathurin, Benedict" where 09:00 prints "Mathurin, Benedict"→"Bennedict" spelling drift; recorded as printing variance, not a status change | [09:15 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| P9-02 | open | 7 rows in the 09:15 report lost their Team cell at page breaks (MEM@WAS ×4, GSW@NOP ×2 + 1 reason-only); team left blank + flagged, never re-attributed | [09:15 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| P9-03 | open | GSW block prints no reason cell on 6 rows; Butler III's lone status cell reads "Injury/Illness - Right ACL Repair / Surgery" with no status; blank + flagged | [09:15 PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf) |
| P9-04 | open (owner) | Tip conflicts rows 266 BOS@DEN (games page 9:30 PM ET vs schedule PDF 9:00) and 267 GSW@DAL (8:00 vs 9:30/8:30-local). Both readings kept; never reconciled. AN-02 (rows 256/257) reconfirmed the same way | [Games 11/18](https://www.nba.com/games?date=2026-11-18) |
| P9-05 | open (owner) | Quarter scores for the 11/15 games are not printed on the scoreboard cards and were not transcribed; the brief's per-team Q1–Q4 cells stay blank + flagged; settlement blocked (with D-01/IR-T4) | [Games 11/15](https://www.nba.com/games?date=2026-11-15) |
| P9-06 | resolved (read gap) / open (publication decision) | The traditional team-stat page served only filter controls to this session's chunk-0 fetch; the parallel BG pass read all five chunks (30 of 30 rows, printed 28-column + RANK schema, six machine checks). No row count is claimed from this session's own read; transcription of the traditional rows onto the site remains an owner decision | [Traditional](https://www.nba.com/stats/teams/traditional) |
| P9-07 | closed | The superseded 11/15 06:15 snapshot's `matchups_not_in_snapshot` label "CHA@LAC" is wrong (the game is CHA@LAL). Historical file not edited; corrected on review.html and in the render code | [Games 11/16](https://www.nba.com/games?date=2026-11-16) |
| P9-08 | open (owner) | `engine/surfaces.py` `audit_page_surface` is unit-tested but not wired into `scripts/check_site.py`, though its docstring claims it is; wiring is a policy decision (which blocked headers per page) | [Repo code](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/surfaces.py) |

## 5. Engine review (task BD)

The line-by-line review of the PR #53 modules is recorded in
[`docs/engine-modules-7ce5c0cc.md`](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/engine-modules-7ce5c0cc.md):
3 defects fixed with 3 regression tests (publish-after-seal refused; settlement
requires seal verification; NaN serialises as null), 3 items flagged rather than
fixed (external timestamp anchoring, unwired surface audit, IR-09 tie-breaker),
and the `engine/__init__.py` public-API decision (keep one flat API, both sets
exported) documented in `docs/engine.md`.

## 6. What this pass did not do

* No pick, probability, line, stake or settlement was produced; the gates (G0 /
  D-01 / IR-T4) stand and the ledger stays empty.
* No value was inferred to fill a blank: lost team cells, missing reason cells,
  missing quarter scores and the untranscribed traditional page all publish as
  blanks with flags.
* No older snapshot was edited; the P9-07 correction is carried on the review
  page instead.
