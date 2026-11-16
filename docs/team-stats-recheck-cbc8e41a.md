# Official team-stat pages re-check (AN-04 closure)

**Session:** `arena/cbc8e41a-nba4` (task BG) · **Observation window:** 2026-11-16T14:41Z–14:47Z (UTC) · **Status:** read complete; publication decision left to the owner.

**What this closes.** Flag **AN-04** (open on the Flagged for Review page) recorded that the official
[opponent](https://www.nba.com/stats/teams/opponent) and [advanced](https://www.nba.com/stats/teams/advanced)
team-stat pages are multi-chunk documents of which only chunk 0 had been read, covering part of the league,
so no league-wide defensive table could be published or consumed. The 2026-11-16 brief additionally asks to
"re-read the three official team-stat pages (traditional, opponent, advanced) and re-cut the model inputs."
This pass reads **every chunk of all three pages** and records what the read does — and does not — license.

**Method.** Each page was fetched with the session's page-fetch tool in its chunked form; every chunk was
retrieved until `hasMore: false`. Values used in the checks below were transcribed from those fetch results
on 2026-11-16 and re-checked by machine (six independent checks, results in section 3). Nothing on the site,
in `engine/`, or in `data/snapshots/` was changed by this pass.

## 1. Pages read, chunk by chunk

| Page | Official source | Chunks fetched (complete) | Rows marker printed | Distinct team rows read | Notes |
| --- | --- | --- | --- | --- | --- |
| Teams — Traditional (2026-27, Regular Season) | [nba.com/stats/teams/traditional/](https://www.nba.com/stats/teams/traditional/) | 5 of 5 (indices 0–4, last has `hasMore: false`) | `30 Rows` · `All 1 of 1` | 30 of 30 | Header row prints 28 value columns plus 26 `RANK` columns (see flag BG-02). |
| Teams — Opponent | [nba.com/stats/teams/opponent](https://www.nba.com/stats/teams/opponent) | 2 of 2 (indices 0–1) | `30 Rows` · `All 1 of 1` | 30 of 30 | Chunk 0 ends mid-Detroit; chunk 1 completes it through Utah. |
| Teams — Advanced | [nba.com/stats/teams/advanced](https://www.nba.com/stats/teams/advanced) | 2 of 2 (indices 0–1) | `30 Rows` · `All 1 of 1` | 30 of 30 | Chunk 0 ends mid-Dallas; chunk 1 completes it through Utah. |

Column schemas as printed (abbreviated verbatim):

- Traditional: `| | Team | GP | W | L | WIN% | Min | PTS | FGM | FGA | FG% | 3PM | 3PA | 3P% | FTM | FTA | FT% | OREB | DREB | REB | AST | TOV | STL | BLK | BLKA | PF | PFD | +/- | GP RANK | … | +/− RANK |` — source: [traditional page](https://www.nba.com/stats/teams/traditional/).
- Opponent: `| | TEAM | GP | W | L | MIN | Opp FGM | Opp FGA | Opp FG% | … | Opp PTS | +/- | GP RANK | … | +/− RANK |` — source: [opponent page](https://www.nba.com/stats/teams/opponent).
- Advanced: `| | TEAM | GP | W | L | MIN | OffRtg | DefRtg | NetRtg | AST% | … | PACE | PIE | POSS | GP RANK | … | PIE RANK |` — source: [advanced page](https://www.nba.com/stats/teams/advanced).

## 2. Reading-completeness notes

- The 30 team names on each page are exactly the 30 NBA franchises; no team is absent and no team appears
  twice (checked by set comparison across the three transcriptions; 30 = 30 = 30).
- Prior note **AN-04** said chunk 0 "covers 13 of 30 teams". In today's fetch that is exact for
  [advanced](https://www.nba.com/stats/teams/advanced) (13 complete rows, Dallas truncated), but
  [opponent](https://www.nba.com/stats/teams/opponent) chunk 0 ends with 10 complete rows (Detroit
  truncated). Chunk boundaries are content-derived and are not stable across fetches, so the earlier count
  is not reproducible as a fixed fact — see flag BG-01. Either way, chunk 1 had never been read before this
  pass, and that is the gap that is now closed.
- The first column of each page is unlabelled (`| | TEAM …`). Its semantics were derived, not assumed:
  traditional orders by `WIN%`, opponent and advanced order by `W` (tie cases verified: Portland 9-3 sits
  alone at traditional rank 6 while all four 9-win teams share advanced/opponent rank 6; Sacramento 1-12
  sits at traditional rank 28 while all three 1-win teams share advanced/opponent rank 28).

## 3. Machine cross-checks (six, all passing on 2026-11-16)

| # | Check | Scope | Result | Source |
| --- | --- | --- | --- | --- |
| 1 | `W + L == GP` on every row | 30 rows × 3 pages = 90 | 90 / 90 pass | [traditional](https://www.nba.com/stats/teams/traditional/) · [opponent](https://www.nba.com/stats/teams/opponent) · [advanced](https://www.nba.com/stats/teams/advanced) |
| 2 | `GP, W, L` identical across the three pages for each team | 30 teams | 30 / 30 pass | [advanced](https://www.nba.com/stats/teams/advanced) |
| 3 | Printed `WIN%` equals `W / GP` to 3 decimals | 30 rows | 30 / 30 pass | [traditional](https://www.nba.com/stats/teams/traditional/) |
| 4 | Traditional `+/-` equals the negation of opponent `+/-` | 30 teams | 30 / 30 pass (after correcting a transcription of ours: the opponent page prints positive values for the teams whose traditional value is negative — the check caught our first pass) | [opponent page](https://www.nba.com/stats/teams/opponent) |
| 5 | Advanced `NetRtg` within 0.1 of `OffRtg − DefRtg` (1-decimal rounding band) | 30 rows | 30 / 30 pass | [advanced](https://www.nba.com/stats/teams/advanced) |
| 6 | First-column rank semantics (competition rank by `WIN%` on traditional; by `W` on opponent/advanced) reproduce all printed ranks | 30 + 30 + 30 rank cells | 90 / 90 pass | [traditional](https://www.nba.com/stats/teams/traditional/) |

Check 4 records an irregularity in our own first-pass transcription (a sign convention was applied instead
of the printed value); it was corrected to the printed source values **before** these results were recorded.
The check script was a session-local scratch file and is not part of the repository; the results above are
what each future pass must reproduce.

## 4. Team coverage (games–wins–losses as printed, agreeing on all three pages)

Every row below was read independently on all three pages and agrees field by field (check 2).
`✓ trad · opp · adv` means GP/W/L matched on each page; links go to the pages themselves.

| Team | GP | W | L | Agreement | Sources |
| --- | --- | --- | --- | --- | --- |
| Los Angeles Lakers | 14 | 12 | 2 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| San Antonio Spurs | 14 | 12 | 2 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Boston Celtics | 13 | 11 | 2 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Houston Rockets | 14 | 11 | 3 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Philadelphia 76ers | 14 | 11 | 3 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Portland Trail Blazers | 12 | 9 | 3 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Memphis Grizzlies | 13 | 9 | 4 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Minnesota Timberwolves | 13 | 9 | 4 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Oklahoma City Thunder | 14 | 9 | 5 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Atlanta Hawks | 14 | 8 | 6 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Detroit Pistons | 12 | 8 | 4 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Golden State Warriors | 13 | 8 | 5 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Cleveland Cavaliers | 14 | 7 | 7 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Dallas Mavericks | 14 | 7 | 7 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Denver Nuggets | 11 | 7 | 4 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Miami Heat | 13 | 7 | 6 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| New York Knicks | 13 | 7 | 6 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Indiana Pacers | 14 | 5 | 9 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Orlando Magic | 12 | 5 | 7 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Phoenix Suns | 12 | 5 | 7 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Toronto Raptors | 13 | 5 | 8 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Charlotte Hornets | 13 | 4 | 9 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| LA Clippers | 12 | 4 | 8 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| New Orleans Pelicans | 14 | 4 | 10 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Washington Wizards | 14 | 4 | 10 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Brooklyn Nets | 12 | 3 | 9 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Chicago Bulls | 12 | 3 | 9 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Sacramento Kings | 13 | 1 | 12 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Milwaukee Bucks | 14 | 1 | 13 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |
| Utah Jazz | 14 | 1 | 13 | ✓ trad · opp · adv | [trad](https://www.nba.com/stats/teams/traditional/) · [opp](https://www.nba.com/stats/teams/opponent) · [adv](https://www.nba.com/stats/teams/advanced) |

The pages print no revision stamp; only the retrieval time above can be verified (flag BG-04).

## 5. Model-input re-cut (the brief item)

The brief asks to "re-cut the model inputs" from these three pages. The re-cut is delivered as a verified
column inventory and mapping, **not** as numbers wired into the engine: the engine's input contracts are
per-game logs supplied by a caller with provenance, and rights gate G0 (NBA Terms §9; NBA Stats FAQ —
statistics "are not available for download for either academic or personal use") is still uncleared.
No value was added to any module by this pass.

| Official column group | Page | Intended engine consumer | Current status | Source |
| --- | --- | --- | --- | --- |
| `GP / W / L / WIN%` | [traditional](https://www.nba.com/stats/teams/traditional/) | cross-check against `standings-2026-11-15.json` and the measured home-win-rate anchor | verified 30/30 here; engine still reads only caller-supplied `TeamGame` rows ([engine/ratings.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/ratings.py)) | [trad page](https://www.nba.com/stats/teams/traditional/) |
| `OffRtg / DefRtg / NetRtg / PACE / POSS` (season aggregates) | [advanced](https://www.nba.com/stats/teams/advanced) | pace/efficiency anchor for `engine/totals.py` (possessions × PPP) — the module deliberately takes possessions from a licensed feed or caller, never from a default | full 30/30 inventory now readable; **not consumed**: no rights-cleared source is registered | [adv page](https://www.nba.com/stats/teams/advanced) |
| `Opp PTS / Opp FG% / Opp eFG-style rates` | [opponent](https://www.nba.com/stats/teams/opponent) | opponent-adjustment inputs for the PPP-for/against terms in `engine/ratings.py` | full 30/30 inventory now readable (AN-04 gap closed); **not consumed** — same gate | [opp page](https://www.nba.com/stats/teams/opponent) |
| `Min / PTS / REB / AST …` (per team-game) | [traditional](https://www.nba.com/stats/teams/traditional/) | sanity bounds for rotation/minutes redistribution (`engine/rotations.py` conserves 240 team minutes) and prop shrinkage (`engine/player_props.py` reads `PlayerGame`) | mapping recorded; team-season aggregates are not a substitute for per-game logs | [trad page](https://www.nba.com/stats/teams/traditional/) |
| `RANK` columns (all three pages) | all three | none — ranks are derived locally if ever needed | **no values rendered in the fetched text**; left blank, never inferred (flag BG-02) | [adv page](https://www.nba.com/stats/teams/advanced) |

Practical effect of the re-cut: a future licensed build can now start from a complete 30-team opponent and
advanced inventory (the half-league gap that AN-04 documented is gone), with the per-mode caveat in BG-03
pinned explicitly in any extraction contract.

## 6. Irregularities flagged by this pass

| Flag | Severity | Finding | Status / action | Source |
| --- | --- | --- | --- | --- |
| BG-01 | Low | AN-04's "chunk 0 covers 13 of 30 teams" is exact for advanced in today's fetch but opponent chunk 0 ends with 10 complete rows; chunk boundaries are content-derived and not stable across fetches. | Open (recorded); the substantive gap — unread chunk 1 — is closed by this pass regardless of chunk sizing. | [opponent page](https://www.nba.com/stats/teams/opponent) |
| BG-02 | Low | All three pages print `RANK` column headers, but the fetched text renders **no rank values**; only the unlabelled first column carries the ordering. | Open; rank cells treated as not printed — blank, never inferred. | [advanced page](https://www.nba.com/stats/teams/advanced) |
| BG-03 | Low | Per-mode defaults differ across pages: traditional and opponent render per-game values (e.g. `Min 48.0`, `PTS 122.8`), advanced renders totals (`MIN 672.0`, `POSS 1,408`). The fetched text does not mark which selector option is active, so the mode is inferred from the printed magnitudes. | Open; any future extraction must pin `PerMode` explicitly rather than trust the default. | [traditional page](https://www.nba.com/stats/teams/traditional/) |
| BG-04 | Low | None of the three pages prints a revision/timestamp; only retrieval time is verifiable (same class as the standings observation). | Open; both times recorded in this document's header. | [traditional page](https://www.nba.com/stats/teams/traditional/) |
| BG-05 | Decision (owner) | The full 30-row statistic tables are **not** published on the site: the repository's standing rule publishes no NBA statistics values without a rights decision (NBA Terms §1/§9; [Stats FAQ](https://www.nba.com/stats/help/faq)). This log therefore quotes schemas, ranks semantics and games–wins–losses only. | Open — reviewer decision; suggested path logged on the coordination board for the decision-support session. | [NBA Terms of Use](https://www.nba.com/termsofuse) |
| BG-06 | Low | Sort/first-column semantics differ: traditional ranks by `WIN%`, opponent and advanced by `W` (verified tie cases: Portland, Sacramento). | Recorded; must be pinned in any extraction contract. | [traditional page](https://www.nba.com/stats/teams/traditional/) |
| BG-07 | Info | The prior claim "traditional all 30" (task AY) is confirmed today: all 5 chunks read, 30 distinct teams. | Closed. | [traditional page](https://www.nba.com/stats/teams/traditional/) |

## 7. Sources (all re-read on 2026-11-16, UTC)

| Source | What was verified from it | Link |
| --- | --- | --- |
| NBA Stats — Teams Traditional, 2026-27 | 5 chunks, `30 Rows`, full schema, 30 team rows, WIN% arithmetic, rank semantics | [nba.com/stats/teams/traditional/](https://www.nba.com/stats/teams/traditional/) |
| NBA Stats — Teams Opponent, 2026-27 | 2 chunks, `30 Rows`, full schema, 30 team rows, `+/-` sign relation to traditional | [nba.com/stats/teams/opponent](https://www.nba.com/stats/teams/opponent) |
| NBA Stats — Teams Advanced, 2026-27 | 2 chunks, `30 Rows`, full schema, 30 team rows, Off/Def/Net rounding band, PACE/POSS present as totals | [nba.com/stats/teams/advanced](https://www.nba.com/stats/teams/advanced) |
| NBA Stats FAQ | Statistics "are not available for download for either academic or personal use" — the gate behind BG-05 | [nba.com/stats/help/faq](https://www.nba.com/stats/help/faq) |
| NBA.com Terms of Use | §§1 and 9 publication/gambling restrictions cited by the standing owner decision | [nba.com/termsofuse](https://www.nba.com/termsofuse) |
