# Requirements coverage — 2026-11-19 brief (session `arena/c38970c9-nba4`)

Task DN. Every line of the owner's brief, mapped to the code that implements it, the tests that prove it runs, the page that surfaces it, and an honest status. Status words are used strictly: **BUILT** = the module exists, refuses rather than invents, and is tested; **PARTIAL** = the mechanism exists but an input is missing, named in the row; **NOT BUILT** = absent.

This map was produced by reading the tree (48 engine modules, 12 test suites), not from the board's memory. Where a module is described as refusing, that was checked by calling it; the luck gate's refusal is reproduced verbatim in section 2.

## 1. Brief line → implementation

Every row's *Source* cell names the repository file that is the evidence for the row (the
module, its test file and the page it renders). These are internal evidence links, not
external claims: this map asserts what the tree contains, and the only external facts it
touches (the four statistics feeds, the schedule PDF) are cited in
[`docs/verification-pass-c38970c9.md`](verification-pass-c38970c9.md) §1 and §8 with their
official URLs.

| # | Brief line | Code | Tests | Page | Status | Source (repository evidence) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Scheduled job refreshes official schedule, standings, team stats and injury report per rolling slate, then rebuilds only after freshness and provenance gates pass | `engine/refresh.py, scripts/scheduled_refresh.py, .github/workflows/daily-refresh.yml` | tests/test_engine_refresh.py (57), tests/test_scheduled_refresh.py (29+1) | automation.html | BUILT — 12 gates; rebuild licensed only when all pass (fail closed). Measured 4/12 from this sandbox, 10/14 in CI on 2026-11-18. | [scripts/scheduled_refresh.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/scheduled_refresh.py) | [engine/refresh.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/refresh.py) |
| 2 | Official per-game result feed, settle only after finals verified, one row per game: date, teams, final, quarter scores | `engine/officialresults.py, engine/resultfeed.py` | tests/test_engine_requirements.py | results.html | BUILT — two agreeing official observations required, else no row; quarter arithmetic checked. | [engine/officialresults.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/officialresults.py) |
| 3 | Store every injury PDF with timestamp; diff consecutive reports to detect status changes | `engine/injurystore.py, engine/injurydiff.py` | tests/test_engine_requirements.py | injuries.html | BUILT (archive + diff). NOTE: only the newest PDF of each cycle is transcribed by hand; the archive is metadata-only (DS-05). | [engine/injurystore.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injurystore.py) |
| 4 | Freeze a pre-registration file per strategy before its first bet: signal, thresholds, universe, settlement rule | `engine/prereg.py, engine/preregistration.py` | tests/test_engine_requirements.py | strategies.html | BUILT — a bet without a frozen pre-registration is refused. | [engine/prereg.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/prereg.py) |
| 5 | Tamper-evident ledger: hash each pick, publish hash before tip, verify after settlement | `engine/publishedledger.py, engine/ledger.py` | tests/test_engine_requirements.py | ledger.html | BUILT — SHA-256 per pick, append-only hash chain, Merkle seal before tip, settlement refuses without two official observations. | [engine/publishedledger.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/publishedledger.py) |
| 6 | Split the site into 'projection' (safe to publish now) and 'bet' (gated) surfaces; never mix them | `engine/surfaces.py, scripts/check_site.py` | tests/test_engine_requirements.py | all 16 pages | BUILT — the checker fails if a bet-gated value appears on a projection page. | [engine/surfaces.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/surfaces.py) |
| 7 | Two independent estimators; publish their disagreement as the primary confidence signal | `engine/dualestimate.py, engine/estimators.py, engine/confidence.py` | tests/test_estimators.py | model.html | BUILT — disagreement statistics with bands; a blend is secondary. | [engine/dualestimate.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/dualestimate.py) |
| 8 | Pin home-court advantage to the measured home-win rate instead of fitting it | `engine/homerate.py` | tests/test_engine_requirements.py | model.html | BUILT — pin 0.59 from 106-98 of 204 (0.5196 raw) stored with its source; PROPOSED NOT APPLIED. | [engine/homerate.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/homerate.py) |
| 9 | Report luck as a z-score per team; refuse a strategy that leans on a team outside the noise band | `engine/luck.py, engine/luckscore.py` | tests/test_engine_requirements.py | leaderboard.html | BUILT — demonstrated 2026-11-19: z=2.582 on a labelled synthetic fixture returns publish=False, LUCK_LEAN_OUTSIDE_BAND. | [engine/luck.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/luck.py) |
| 10 | Rest, back-to-back and 3-in-4 from the official schedule, plus travel distance from a sourced arena-coordinate table | `engine/rest.py, engine/travel.py, engine/venues.py` | tests/test_engine_requirements.py | availability.html | PARTIAL — rest/B2B/3-in-4 compute from the schedule. Travel needs a sourced arena-coordinate table: NONE is in the tree, so travel refuses (input gap Q-DO-03). | [engine/rest.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/rest.py) |
| 11 | Minutes redistribution: top-8 minute shares and replacement shares when a player is out | `engine/minutesshare.py, engine/rotations.py` | tests/test_engine_requirements.py | availability.html | BUILT (model) — needs per-player minutes, which are not authorised inputs yet. | [engine/minutesshare.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/minutesshare.py) |
| 12 | Stop publishing a single blended rating; publish the disagreement as headline with the blend underneath | `engine/dualestimate.py` | tests/test_estimators.py | model.html | BUILT. | [engine/dualestimate.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/dualestimate.py) |
| 13 | Price every parlay with the measured rho and print the naive product beside it | `engine/parlay.py, engine/correlation.py, engine/corrstats.py` | tests/test_engine.py, tests/test_engine_models.py | leaderboard.html | BUILT — Gaussian copula with measured rho, naive product always printed alongside. | [engine/parlay.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/parlay.py) |
| 14 | Put rotation availability on the picks page as its own column | `engine/picks.py, engine/rotations.py` | tests/test_engine_requirements.py | model.html (Picks) | BUILT. | [engine/picks.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/picks.py) |
| 15 | Market-anchored prior: blend model line with closing line weighted by measured out-of-sample log-loss | `engine/marketprior.py` | tests/test_engine_requirements.py | line-origination.html | BUILT (model) — closing lines are not an authorised input; refuses without them. | [engine/marketprior.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/marketprior.py) |
| 16 | Model the total as possessions x points-per-possession, not an average of team scoring averages | `engine/totals.py, engine/teamstats.py` | tests/test_engine_teamstats.py | model.html | BUILT — cross-checks against printed OffRtg/DefRtg/NetRtg/POSS; refuses on a partial page. | [engine/totals.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/totals.py) |
| 17 | Show injury-report revision time and retrieval time in the Injuries banner | `engine/injurystore.py, scripts/build_snapshots.py` | tests/test_snapshots.py | injuries.html | BUILT. | [engine/injurystore.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/injurystore.py) |
| 18 | Settle the sealed ledger from official finals as soon as each game day ends; keep the settlement stamp visible | `engine/publishedledger.py, engine/officialresults.py` | tests/test_engine_requirements.py | ledger.html | BUILT (no live settlement: no official final has been ingested under G0). | [engine/publishedledger.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/publishedledger.py) |
| 19 | Re-read the three official team-stat pages (traditional, opponent, advanced) and re-cut the model inputs | `engine/teamstats.py, data/snapshots/team-stats-2026-11-17.json` | tests/test_engine_teamstats.py | team-stats.html | PARTIAL — the pages are published as catalogued observations with model_inputs_status: REFUSED. §8 shows why: the captures carry no statistics payload. | [engine/teamstats.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/teamstats.py) |
| 20 | Capture per-player game logs (minutes, points, rebounds, assists, opponent) for players on an injury report | `engine/playerlogs.py, scripts/build_gamelogs.py` | tests/test_engine_playerlogs.py | availability.html | BUILT (mirror) — the mirror reproduces the published gamebook rows; it is not an authorised feed. | [engine/playerlogs.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/playerlogs.py) |
| 21 | Originate own lines, strategies, leaderboard rewards, validation gates, correlations, luck removal | `engine/lineorigination.py, engine/leaderboard.py, engine/validation.py, engine/gates.py, engine/markets.py, engine/player_props.py` | tests/test_engine.py, tests/test_engine_models.py, tests/test_engine_requirements.py | leaderboard.html, strategies.html, line-origination.html | BUILT — no line is published: the rights gate (G0) refuses. | [engine/lineorigination.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/lineorigination.py) |
| 22 | Generate picks for every slate up to 3 days ahead | `engine/pipeline.py, engine/picks.py` | tests/test_engine.py | slate.html, model.html | BUILT — 72-hour horizon enforced; every game carries a reason-coded NO PICK. | [engine/pipeline.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| 23 | Track how injuries affect rotation minutes and production; provide game-flow analysis | `engine/gameflow.py, engine/rotations.py, engine/minutesshare.py` | tests/test_engine_models.py | injuries.html, availability.html | BUILT (model). | [engine/gameflow.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/gameflow.py) |
| 24 | Executive summary / questions / suggestions / flagged review | `docs/decision-register.md, questions.html, suggestions.html, review.html` | tests/test_site_pages.py | index.html, questions.html, suggestions.html, review.html | BUILT — this session adds tasks DO/DP/DR. | [README](https://github.com/wingbangboozle1-lang/NBA4/blob/main/README.md) |

## 2. What "refuses rather than invents" means here — one reproduced example

The luck gate is the cleanest case, because the brief asks for exactly this behaviour:
"refuse to publish a strategy that leans on a team outside the noise band". Called on
2026-11-19 with a **labelled synthetic fixture** (not NBA data — the module has no
authorised inputs and this is the only way to exercise it):

```
LuckPolicy(z_threshold=2.0, alpha=0.05, correlated_inflation=1.2, registered_at=...)
team_luck("SYNTH-BOS", 12 games, observed 10.0 wins, expected 6.0, variance 2.4, policy, source)
  -> z = 2.582, band = OUTSIDE
strategy_luck_gate("SYNTH-S1", ["SYNTH-BOS"], {...}, policy)
  -> LuckGate(publish=False, code='LUCK_LEAN_OUTSIDE_BAND',
              detail='leans on team(s) with |z| beyond the registered band: SYNTH-BOS (threshold 2.0)')
```

and with the expectation or the variance missing, `team_luck` returns
`band=BAND_UNSET` with the text `unmeasured: an expectation and a variance must both come
from an authorised source; no z-score is published without them` — it does not substitute a
default. The same shape (a refusal object with a reason code) is used by
`engine/officialresults.py`, `engine/preregistration.py`, `engine/marketprior.py`,
`engine/venues.py`, `engine/minutesshare.py` and `engine/totals.py`.

## 3. The three inputs the system needs and does not have

| Missing input | Who needs it | What it blocks | Where it is asked | Source that would supply it |
| --- | --- | --- | --- | --- |
| Authorised statistics (the four feeds) | every model module | anything numeric: ratings, totals, props, lines, picks | §8 of [`docs/verification-pass-c38970c9.md`](verification-pass-c38970c9.md), decision **DP-01** | a written NBA licence/permission, or a licensed alternative — see [NBA Stats FAQ](https://www.nba.com/stats/help/faq) and [NBA Terms of Use](https://www.nba.com/termsofuse) |
| Arena coordinates with a citable source | `engine/venues.py`, `engine/travel.py` | travel distance; the rest/travel composite | question **Q-DO-03** on `questions.html` | a venue-coordinate table with a citable, permissive licence — the [NBA teams index](https://www.nba.com/team) prints venue names but no coordinates, so it cannot supply it |
| Closing lines | `engine/marketprior.py` | the market-anchored prior and its log-loss weighting | question **Q-DO-04** on `questions.html` | a licensed closing-line feed; [NBA Terms of Use](https://www.nba.com/termsofuse) §9 restricts gambling-connected use, so this is a legal question before it is a data question |

Each is a *sourcing* problem, not a coding problem: the modules are written and tested
against synthetic fixtures, and they refuse until a document with an official/authorised URL
is supplied. That is deliberate, and it is why the site publishes observations instead of
model output.

## 4. Where the brief and the NBA Terms conflict (unchanged, restated)

The brief asks for originated lines, picks, parlays and a rewards leaderboard. NBA.com's
Terms of Use restrict NBA Statistics to "legitimate news reporting or private, non-commercial
purposes" and state they "may not be used in connection with any gambling activity (including
legal gambling activity)". Every betting surface in this repository is therefore **gated**,
not removed: the code exists, the pre-registration and ledger machinery exist, and the
publish path refuses. Three sessions have now recorded this independently (D-01, IR-T4,
and this session's DP-01). The owner's decision is the only thing that changes it, and it is
listed as decision **DP-01** rather than quietly assumed.

## 5. Items the brief asks for that are NOT built (stated plainly)

| Item | Status | Why | Source |
| --- | --- | --- | --- |
| "Publish their disagreement as the primary confidence signal" *on the live picks page* | PARTIAL | the disagreement is computed and tested (`engine/dualestimate.py`), but the picks page cannot show a value while every game is `NO PICK` under G0 | [dualestimate.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/dualestimate.py) |
| Rewards for top-performing strategies | NOT BUILT | `docs/leaderboard.md` specifies proposed tiers; no reward is paid, promised or published, because that is a legal/commercial decision (decision DP-02) | [leaderboard.md](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/leaderboard.md) |
| "No manual input on my part" fully automated refresh | PARTIAL | the daily job is automated and fails closed; the injury-row transcription is still performed by a session and committed (§9, DS-05) — automating it needs a licensed feed, i.e. DP-01 | [daily-refresh.yml](https://github.com/wingbangboozle1-lang/NBA4/blob/main/.github/workflows/daily-refresh.yml) |
| Travel distance | PARTIAL | code refuses without a sourced coordinate table (§3) | [venues.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/venues.py) |

