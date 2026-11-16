# Verification pass 9 — brief re-read, rights gate and status map (task BB)

**Session:** `arena/4b8d8ab1-nba4` · **Date:** 2026-11-16 (UTC) · **Scope:** this file only, plus the task row in `COORDINATION.md`.
**Not changed:** engine code, tests, data files, snapshot tables, and the published slate/injury/results/strategy pages.

This pass re-reads the sources the project depends on, runs the repository's own checks, and records what can and cannot be done under the sources. It does not add data, lines, probabilities, picks or results.

---

## 1. Decision: the betting scope is not started

The 2026-11-16 brief asks for originated NBA lines, picks for each slate, parlay and prop-combo prices, a strategy leaderboard with rewards, and a "bet" surface. Those outputs would use NBA statistics and odds in connection with gambling. The NBA Terms of Use prohibit that use. This session did **not** build, publish or enable any such output.

Re-read live on 2026-11-16 at <https://www.nba.com/termsofuse> (fetched chunk 4 of 10, which contains the end of section 9):

> "…atistics may not be used in connection with any gambling activity (including legal gambling activity); (v) the NBA Statistics may not be used in connection with any fantasy game or other commercial product or service; … (vii) the NBA Statistics may not be used in connection with any website, product, or service that features a database (in any medium or format) of comprehensive, regularly updated statistics from NBA, WNBA or G-League games, competitions, or events without the Operator's express prior consent."

The chunk begins mid-word ("…atistics"), so the sentence's opening clause is in the previous chunk. The gambling sentence is quoted exactly as read; this pass does not assign it a sub-letter. The existing register (`docs/source-verification.md`, NBA-02) cites it as section 9.

Section 1 of the same page (chunk 0), re-read live:

> "No Basketball Content from the Services may be reproduced, republished, uploaded, posted, modified, reused, transmitted, reproduced, distributed, copied, publicly displayed, linked to, or otherwise used except as provided in these Terms of Use without the written permission of the Operator."

The NBA Stats FAQ (<https://www.nba.com/stats/help/faq>, re-read live) also states: "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats."

**What unblocks this:** written permission from the NBA (the Operator) for the specific use, or a licensed data contract. Until then, the engine keeps refusing records without an authorized flag (`python3 -m engine.cli status` → "NO AUTHORIZED INPUTS -> no lines, no picks"). Legal review of gambling-advertising rules is recorded separately on the existing Ksa pages in [`docs/source-verification.md`](source-verification.md) (KSA-01…KSA-04); those were not re-read in this pass.

## 2. Repository baseline (run on the branch, 2026-11-16)

- **`python3 -m unittest discover -s tests -t .`:** `Ran 297 tests … OK`
- **`python3 scripts/check_site.py --with-tests`:** PASS: 12 pages, 470 HTML data rows and 797 Markdown data rows (run before this file was added)
- **`python3 scripts/build_snapshots.py --check`:** `unchanged results.html` (snapshot tables in sync with `data/snapshots/`)
- **`python3 -m engine.cli status`:** Ledger has 0 records; missing `games.jsonl`, `players.jsonl`, `injuries.jsonl`, `slate.jsonl`, `quotes.jsonl`; state NO AUTHORIZED INPUTS
- **`engine/venues.py` arena-coordinate table:** `VENUES` is empty (0 rows), so travel distance is not computed and is reported as `TRAVEL_NO_SOURCE`

## 3. Freshness flags (not fixed in this pass)

- **BB-01** — **Injury table is one day behind.** The published injury snapshot is the 2026-11-15 06:15 AM ET report. [`data/snapshots/injuries-2026-11-15-0615am.json`](../data/snapshots/injuries-2026-11-15-0615am.json) Open. The official index (re-read 2026-11-16) lists 11/16 reports from 12:00 AM through 9:15 AM ET. Transcription is a shared-output change and is left to the integration session.
- **BB-02** — **Slate window is behind the calendar.** The published three-day window is the 2026-11-15 to 11/17 rows, built on 11/15. [`data/snapshots/slate-2026-11-15.json`](../data/snapshots/slate-2026-11-15.json) Open. A rolling refresh is needed.
- **BB-03** — **Official index shows the daily report sequence, but its date labels were not re-checked against the PDFs.** [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/) Open. Check against the PDF header on the next refresh.

## 4. Requirement status map (2026-11-16 brief)

Status values: **Engine module (synthetic only)** = code and tests exist, but no NBA data is loaded. **Blocked: rights** = not built or published, because it needs NBA data used in gambling. **Not started** = no implementation found in the repository.

| # | Brief item | Status | Where it stands / source | Official source |
| --- | --- | --- | --- | --- |
| 1 | Rolling refresh of schedule, standings, team stats, injuries; rebuild after freshness gates | Partial. Schedule window and injury snapshots exist, but they are stale (BB-01, BB-02). Standings and team stats are not ingested. | `data/snapshots/`, `scripts/build_snapshots.py` | [NBA schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf); [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 2 | Official per-game result feed, one row per game, settle after verified finals | Engine module (synthetic only). Published results are blocked by D-01/IR-T4. | `engine/officialresults.py`, `results.html` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 3 | Store each injury PDF with timestamp; diff consecutive reports | Engine module (synthetic only); the 11/14 and 11/15 snapshots are stored. | `engine/injurydiff.py`, `data/snapshots/` | [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 4 | Pre-registration file per strategy, frozen before the first bet | Engine module. No strategy has been registered. | `engine/preregistration.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 5 | Tamper-evident ledger: hash each pick, publish before tip, verify after settlement | Engine module (synthetic only). No real picks exist. | `engine/publishedledger.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 6 | Split site into projection and bet surfaces | Engine module. The bet surface is **blocked: rights**. | `engine/surfaces.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§1, §9) |
| 7 | Two independent estimators; disagreement as the headline | Engine module (synthetic only). Not published. | `engine/estimators.py`, `engine/confidence.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 8 | Home-court pinned to the measured home-win rate | Engine module (synthetic only). Measured rate is not published. | `engine/homerate.py`, `engine/ratings.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 9 | Luck z-score per team; refuse strategies that lean on a team outside the noise band | Engine module. No band is registered. | `engine/luck.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 10 | Rest, back-to-back, 3-in-4 from the schedule; travel distance from a sourced arena table | Rest: engine module. Travel: **blocked, no sourced table** (`VENUES` is empty). | `engine/rest.py`, `engine/venues.py` | [NBA schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| 11 | Minutes redistribution (top-8 shares, replacement shares) | Engine module (synthetic only). | `engine/rotations.py`, `engine/minutesshare.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 12 | Headline = disagreement; blend underneath | Engine module (synthetic only). | `engine/confidence.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 13 | Parlay priced with measured rho, naive product beside it | Engine module (synthetic only). Pricing for gambling is **blocked: rights**. | `engine/totals.py`, `engine/markets.py`, `engine/parlay.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 14 | Rotation availability as its own picks column | Engine module. No picks are published. | `engine/rotations.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 15 | Market-anchored prior weighted by out-of-sample log loss | Engine module. No closing-line data is loaded. **Blocked: rights** for any odds use. | `engine/markets.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 16 | Total = possessions × points per possession | Engine module (synthetic only). | `engine/totals.py` | [NBA Stats glossary](https://www.nba.com/stats/help/glossary); [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 17 | Injury-report revision and retrieval time in the Injuries banner | Done for the 11/15 snapshot. Goes stale until BB-01 is fixed. | `injuries.html` | [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 18 | Settle the sealed ledger from official finals; keep the settlement stamp visible | Blocked: no verified finals are published (D-01/IR-T4). | `results.html`, `engine/publishedledger.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 19 | Re-read the three official team-stat pages (traditional, opponent, advanced) and re-cut inputs | **Not started.** Team-stat pages are NBA Statistics; reading them for gambling inputs is **blocked: rights**. | NBA Stats FAQ (see §1) | [NBA Stats FAQ](https://www.nba.com/stats/help/faq); [NBA Terms of Use](https://www.nba.com/termsofuse) (§1, §9) |
| 20 | Per-player game logs for players on an injury report | **Not started.** Same rights limit as item 19. | — | [NBA Terms of Use](https://www.nba.com/termsofuse) (§1, §9) |
| 21 | Originate NBA lines; picks for every slate up to 3 days ahead | **Blocked: rights.** Not built for real data. | §1 | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 22 | Strategy leaderboard with rewards; single, parlay, prop-combo strategies; correlation values | Design only (synthetic). Rewards and gambling use are **blocked: rights**; reward products also need legal review. | [`docs/leaderboard.md`](leaderboard.md) | [NBA Terms of Use](https://www.nba.com/termsofuse) (§9) |
| 23 | Injury effects on rotation and game flow | Engine modules (synthetic only). | `engine/injuries.py`, `engine/gameflow.py` | [NBA injury index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| 24 | Executive summary | Exists. This pass did not rewrite it. | [`docs/decision-register.md`](decision-register.md), `index.html` | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| 25 | Suggestions section for reviewer choice before any change | Exists. | `suggestions.html`, [`docs/suggestions.md`](suggestions.md) | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| 26 | Clear list of questions, information and answers | Exists. This pass adds the rights question in §5. | `questions.html` | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| 27 | Verification with an official source for every table row; blank and flag unverified values | Exists and checked by `scripts/check_site.py`. This pass did not add rows. | `scripts/check_site.py` | [NBA Terms of Use](https://www.nba.com/termsofuse) |

## 5. Questions that decide the betting scope

These questions need an answer before any betting-related output can be considered. The repository cannot answer them.

1. **Permission.** Will the NBA (the Operator) grant written permission for NBA statistics or odds to be used in connection with gambling, or for a comprehensive, regularly updated statistics database (Terms §9 (vii))? Answer source: the NBA. Not answerable from the repo.
2. **Licensed alternative.** If not, is there a licensed data provider whose contract allows the intended use? Source: that provider's terms (not yet identified or verified).
3. **Product scope.** If the answer to (1) and (2) is no, will the project publish research only, with no picks, prices or leaderboard rewards? That is a product decision for the owner.
4. **Jurisdiction.** Who is the audience, and which gambling-advertising and licensing rules apply? The Ksa pages in the register are Dutch-jurisdiction references; their applicability has not been established.

## 6. Limits of this pass

- No NBA statistic, odds, player row, pick or probability was fetched or published.
- The 11/16 injury PDFs were not opened. Only the index, which lists them, was read (BB-01).
- Ksa pages were not re-read in this pass.
- No external source outside the repository's approved list was added.
