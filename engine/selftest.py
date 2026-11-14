"""End-to-end mechanics demo on clearly labelled SYNTHETIC fixtures.

These fixtures are NOT NBA data. They exist only to prove that the pipeline
runs: ledger -> ratings -> originated lines -> injury scenarios -> game-flow
scenarios -> correlation estimates -> forecast records. Nothing produced
here is written into the repository's data or site, and the fixture rows use
the reserved source host `synthetic.invalid`, which load_ledger() filters
out of every production run.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .correlation import joint_event_estimate, residual_correlation_estimate
from .gameflow import minutes_multiplier_by_flow, scenario_distribution
from .injuries import roster_scenario
from .picks import generate_slate_picks
from .player_props import player_prop_forecast
from .ratings import margin_forecast, win_probability
from .schema import InjuryObservation, PlayerGame, Provenance, SlateGame, TeamGame

SYNTH_BANNER = (
    "*** SYNTHETIC FIXTURES - NOT REAL NBA DATA - NOT PICKS *** "
    "Numbers below come from fabricated test inputs used only to prove the "
    "engine mechanics."
)

BASE = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
PROV = Provenance(
    source_url="https://synthetic.invalid/fixture",
    source_time=BASE.isoformat(),
    observed_at=BASE.isoformat(),
)


def build_synthetic_games() -> list:
    """Two fictional teams with 8 fabricated games each."""
    games = []
    for team, base_for, base_against, opp in (
        ("SYNTH-H", 112.0, 106.0, "SYNTH-A"),
        ("SYNTH-A", 106.0, 112.0, "SYNTH-H"),
    ):
        for i in range(8):
            date = (BASE - timedelta(days=i * 3 + 1)).isoformat()
            jitter = (i % 3) - 1
            games.append(TeamGame(
                record_id=f"synth-g-{team}-{i}",
                game_id=f"synth-game-{team}-{i}",
                game_date=date,
                team=team,
                opponent=opp,
                is_home=(i % 2 == 0),
                points=base_for + 2 * jitter,
                opp_points=base_against - 2 * jitter,
                possessions=100.0,
                provenance=PROV,
            ))
    return games


def build_synthetic_ledger() -> list:
    """JSONL rows for load_ledger(allow_synthetic=True) in tests."""
    rows = []
    for g in build_synthetic_games():
        rows.append(("games.jsonl", {
            "record_id": g.record_id, "game_id": g.game_id, "game_date": g.game_date,
            "team": g.team, "opponent": g.opponent, "is_home": g.is_home,
            "points": g.points, "opp_points": g.opp_points, "possessions": g.possessions,
            "provenance": {"source_url": PROV.source_url,
                           "source_time": PROV.source_time,
                           "observed_at": PROV.observed_at},
        }))
    rows.append(("slate.jsonl", {
        "record_id": "synth-slate-1", "game_id": "synth-game-next",
        "tip_time": (BASE + timedelta(days=1)).isoformat(),
        "home_team": "SYNTH-H", "away_team": "SYNTH-A",
        "provenance": {"source_url": PROV.source_url,
                       "source_time": PROV.source_time,
                       "observed_at": PROV.observed_at},
    }))
    rows.append(("injuries.jsonl", {
        "record_id": "synth-inj-1", "report_time": BASE.isoformat(),
        "game_id": "synth-game-next", "team": "SYNTH-H", "player": "SYNTH-PLAYER",
        "status": "Questionable", "reason": "SYNTHETIC - fixture reason",
        "provenance": {"source_url": PROV.source_url,
                       "source_time": PROV.source_time,
                       "observed_at": PROV.observed_at},
    }))
    return rows


def run_selftest() -> int:
    print(SYNTH_BANNER)
    games = build_synthetic_games()
    issued = BASE

    f = margin_forecast(games, "SYNTH-H", "SYNTH-A", issued)
    print(f"\n[1] ratings -> originated spread (home margin): {f.expected_home_margin}")
    print(f"    originated total: {f.expected_total}")
    if f.expected_home_margin is not None:
        print(f"    P(home win): {win_probability(f.expected_home_margin, f.margin_sd):.4f}")

    inj_obs = [
        InjuryObservation(
            "synth-inj-1", issued.isoformat(), "synth-game-next", "SYNTH-H",
            "SYNTH-PLAYER", "Questionable", "SYNTHETIC - fixture reason", PROV,
        )
    ]
    scen, resolved = roster_scenario(inj_obs, ["SYNTH-PLAYER", "SYNTH-MISSING"])
    print(f"\n[2] injuries: all_resolved={resolved}")
    for name, s in scen.items():
        print(f"    {name}: status={s.status} avail={s.availability_prob} "
              f"min_mult={s.minutes_multiplier}")

    if f.expected_home_margin is not None:
        flow = scenario_distribution(f.expected_home_margin, f.margin_sd)
        print(f"\n[3] game flow: P(competitive)={flow.p_competitive:.4f} "
              f"P(sep home)={flow.p_separation_home:.4f} "
              f"P(sep away)={flow.p_separation_away:.4f}")
        print(f"    minutes multiplier by flow: {minutes_multiplier_by_flow(flow):.4f}")

    residuals_a = [("g1", 2.0), ("g1", 1.0), ("g2", -1.0), ("g2", -2.0),
                   ("g3", 0.5), ("g3", -0.5), ("g4", 1.5), ("g4", -1.5)]
    residuals_b = [("g1", 1.0), ("g1", 2.0), ("g2", -2.0), ("g2", -1.0),
                   ("g3", -0.5), ("g3", 0.5), ("g4", -1.5), ("g4", 1.5)]
    est = residual_correlation_estimate(residuals_a, residuals_b)
    print(f"\n[4] correlation (synthetic residuals): value={est.value} "
          f"ci=({est.ci_low}, {est.ci_high}) n={est.n} clusters={est.clusters}")
    joint = joint_event_estimate(
        [("g1", True), ("g2", False), ("g3", True), ("g4", False)],
        [("g1", True), ("g2", False), ("g3", False), ("g4", False)],
    )
    print(f"    binary legs: phi={joint.value} ({joint.notes[0]})")

    prop = player_prop_forecast(
        [
            PlayerGame(
                record_id=f"synth-p-{i}", game_id=f"synth-game-{i}",
                game_date=(BASE - timedelta(days=i * 3 + 1)).isoformat(),
                player="SYNTH-PLAYER", team="SYNTH-H", minutes=30.0,
                points=18.0 + i % 4, rebounds=5.0, assists=4.0, provenance=PROV,
            )
            for i in range(8)
        ],
        "SYNTH-PLAYER", "points", 0.5, issued,
    )
    print(f"\n[5] player prop (points): E={prop.expected_value} sd={prop.sd:.3f} "
          f"minutes={prop.minutes_mean} games={prop.games_used}")

    slate = [SlateGame("synth-slate-1", "synth-game-next",
                       (BASE + timedelta(days=1)).isoformat(),
                       "SYNTH-H", "SYNTH-A", PROV)]
    class _L:
        def __init__(self, games, slate):
            self.games, self.players, self.injuries = games, [], inj_obs
            self.slate, self.quotes, self.rejected = slate, [], []
        @property
        def is_empty(self):
            return False
        def all_record_ids(self):
            return ["synthetic"]
    decisions, report = generate_slate_picks(_L(games, slate), issued_at=issued,
                                             allow_shadow=True)
    print(f"\n[6] pick generator (shadow on synthetic data):")
    for d in decisions:
        for r in d.records:
            print(f"    {r.pick_id}: status={r.status} line={r.originated_line} "
                  f"P={r.forecast_probability} reasons={r.reason_codes}")

    print("\n" + SYNTH_BANNER)
    print("Mechanics OK. Production runs with the real ledger remain NO PICK "
          "until rights (G0) and data (G1) are cleared.")
    return 0
