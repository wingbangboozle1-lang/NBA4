# Per-player game logs and the team-stat re-cut

Two brief items, two new modules, one rule they share: **a value that cannot be
traced to a document is refused, not estimated.**

* [Per-player game logs](#per-player-game-logs) —
  [`engine/playerlogs.py`](../engine/playerlogs.py)
* [The three team-stat pages](#the-three-team-stat-pages) —
  [`engine/teamstats.py`](../engine/teamstats.py)

## Per-player game logs

Brief item: *"Capture per-player game logs (minutes, points, rebounds, assists,
and the opponent) for at least the players who appear on an injury report."*

### Why the opponent is a required field

Without the opponent, a game log cannot be conditioned on opponent defensive
quality — and conditioning on the opponent is the only reason to store per-game
logs instead of per-season averages. A row that does not know who it was played
against is therefore rejected at ingest (`PlayerLogError`) rather than stored
with a blank to be filled in later.

### Rules the capture enforces

* **One row per `(player_id, event_id)`.** Two observations of the same game are
  either the same game or a conflict. A second agreeing row is counted as
  corroboration; a disagreeing one raises `LogConflict` and never overwrites.
* **`minutes <= 48 + 5 x overtime_periods`.** A player cannot play longer than
  the game lasted, so a larger value is a source error. The overtime count is
  part of the row rather than assumed away.
* **A team cannot play itself.** That is a source error, not a data point, so
  the row is rejected at ingest.
* **A missing player is missing.** "Did not play", "not captured" and "played
  and produced nothing" are three different facts. Coverage reports a player
  with no log as `LOG_MISSING` and nothing is zero-filled.
* **Rights gate at the point of use.** `model_inputs()` runs
  `require_allowed_use` over every log of every rostered player, which is rights
  gate G0 under [NBA Terms of Use](https://www.nba.com/termsofuse) sections 1
  and 9.

The last rule is why the module has two entry points: logs can be *stored* for
research, but `model_inputs()` refuses to hand a partial roster to a model. A
model that saw some of the injured players and not others would be conditioning
on an arbitrary subset.

### Coverage against an injury-report roster

```python
from engine import playerlogs

book = playerlogs.PlayerLogBook()
book.extend(rows)                     # rows are PlayerGameLog, one per player-game
report = book.coverage(injury_report_player_ids)
report.missing        # players with no log at all
report.uncleared      # players whose log is not cleared for the intended use
report.coverage_fraction
```

`coverage_fraction` is a completeness measure, not a quality measure: 1.0 means
every rostered player has at least one log, nothing more.

### What this module is not

It is not a model. The minutes-x-rate shrinkage machinery already lives in
[`engine/player_props.py`](../engine/player_props.py), and a second unvalidated
copy of the same estimate is exactly the kind of duplication the board records as
IR-T1. `playerlogs.py` captures and audits; `player_props.py` estimates.

## The three team-stat pages

Brief item: *"Re-read the three official team-stat pages (traditional, opponent,
advanced) and re-cut the model inputs."*

The pages, and what each one is used for:

| Page | Used for | Source |
| --- | --- | --- |
| [Teams Traditional](https://www.nba.com/stats/teams/traditional) | the team's own box score: PTS, MIN, FGA, FGM, FTA, OREB, TOV, GP | [traditional](https://www.nba.com/stats/teams/traditional) |
| [Teams Opponent](https://www.nba.com/stats/teams/opponent) | the same columns for the opposition, including opponent points | [opponent](https://www.nba.com/stats/teams/opponent) |
| [Teams Advanced](https://www.nba.com/stats/teams/advanced) | PACE, POSS, OffRtg, DefRtg, NetRtg, eFG%, TOV%, OREB% as the page prints them | [advanced](https://www.nba.com/stats/teams/advanced) |

### The read-completeness gate

A page arrives as a `PageRead` that records how many rows were read and how many
chunks of the document were consumed. `recut` refuses unless all 30 rows and all
chunks of all three pages were read.

This is the mechanical form of flag AN-04 on the
[Flagged for Review page](../review.html): the opponent and advanced pages are
served in more than one chunk, and a reader that stops after one gets 13 of 30
rows with no error at all. The count is part of the provenance so a partial read
cannot be presented as a full one. The pages were re-read in full on 2026-11-16
— all 30 rows of all three are recorded in
[docs/verification-pass-cc82e369.md](verification-pass-cc82e369.md).

### The re-cut

Possessions come from pace, not from a scoring average:

```
possessions_per_game = PACE x (minutes_per_game / 48)
offensive_ppp        = PTS      / possessions_per_game
defensive_ppp        = Opp PTS  / possessions_per_game
```

`minutes_per_game` is the traditional page's own MIN column, which exceeds 48.0
for a team that has played overtime. Using it is what makes the pace conversion
honest for a team whose games are longer than regulation.

The definitions are the NBA's own, quoted in
[the verification pass](verification-pass-cc82e369.md#2-the-official-definitions-the-re-cut-relies-on):
pace is "the number of possessions per 48 minutes", and "an Offensive Rebound
does not create another possession, it simply makes the existing possession
longer".

### Verification against the publisher's own arithmetic

The advanced page prints OffRtg, DefRtg, NetRtg and POSS, so the re-cut is
checked against the page rather than asserted. Across all 30 teams on
2026-11-16 the largest gaps were 0.36 (offence), 0.48 (defence), 0.84 (net)
rating points and 3.99 possessions on 1,185. The tolerances are declared from
those measurements: 1.0 rating point and 1% of the printed possession total.

The possession identity is **not exact** for teams that played overtime — the
page counts possessions while the re-cut derives them from a printed per-48 rate.
That drift is published rather than tuned away.

### Hand-off to the totals model

Game-level projection is not done here. `matchup_inputs` returns values shaped
for [`engine/totals.py`](../engine/totals.py):

```python
inputs = teamstats.matchup_inputs(table, home, away, game_id="...")
projection = totals.project_total(
    inputs.game_id, inputs.possessions, inputs.ppp_home, inputs.ppp_away,
    scoring_averages=inputs.scoring_averages,
)
projection.model_total      # possessions x (ppp_home + ppp_away)
projection.naive_total      # the two scoring averages, summed
```

The pace rule (`pace_weighted_mean` or `pace_product_over_league`) and the
adjustment form (`multiplicative` or `additive`) are declared by the caller.
They are unvalidated modelling choices and belong in the pre-registration file,
not in a module.

### Two traps the module names explicitly

* **The opponent page's `+/-` column is the opponent's margin.** For all 30 rows
  it is the negative of the team's own margin on the traditional page. Reading it
  as the team's margin inverts the sign of the whole league. It is stored as
  `opponent_plus_minus` and the two are never averaged together.
* **The three pages print no revision stamp.** Their only timestamp is the
  retrieval time, which is why `engine/refresh.py` measures their freshness from
  retrieval and labels the basis in every verdict.

Both are recorded as CC-01 and CC-03 in
[the verification pass](verification-pass-cc82e369.md).
