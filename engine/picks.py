"""Pick generator: originated lines -> forecast records, <= 3-day horizon.

Horizon rule (docs/decision-register.md Q10): a pick may only target games
whose tip time falls in (issued_at, issued_at + 72h]. The timezone is UTC
in code and must be declared before production; on missing/stale inputs the
generator returns NO PICK rows - never a stale or guessed forecast.

Status rules:
  * ledger empty / gates not passed -> "NO PICK" with reason codes
  * forecasts may be recorded in shadow mode (G11) after calibration inputs
    exist, but this generator only emits SHADOW when explicitly allowed and
    never ELIGIBLE while any gate is blocked (the current repository state).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence, Tuple

from . import ENGINE_VERSION, MODEL_VERSION
from .injuries import roster_scenario
from .ledger import Ledger
from .ratings import cover_probability, margin_forecast, win_probability
from .schema import PickRecord, STATUS_NO_PICK, STATUS_SHADOW, SlateGame

HORIZON_HOURS = 72  # hard 3-day cap from the project requirements


@dataclass
class SlateDecision:
    game: SlateGame
    records: Tuple[PickRecord, ...]


def in_horizon(tip_time: str, issued_at: datetime, hours: int = HORIZON_HOURS) -> bool:
    tip = datetime.fromisoformat(tip_time).astimezone(timezone.utc)
    issued = issued_at.astimezone(timezone.utc)
    return issued < tip <= issued + timedelta(hours=hours)


def generate_slate_picks(
    ledger: Ledger,
    issued_at: Optional[datetime] = None,
    allow_shadow: bool = False,
    horizon_hours: int = HORIZON_HOURS,
) -> Tuple[List[SlateDecision], dict]:
    """Generate forecast records for every slate game within the horizon.

    Returns (decisions, run_report). With the current repository state
    (no authorized inputs, G0 blocked) every record is NO PICK; the run
    report explains exactly why, for the site's slate page.
    """
    issued = issued_at or datetime.now(timezone.utc)
    decisions: List[SlateDecision] = []
    reasons: List[str] = []

    if ledger.is_empty:
        reasons.append("no authorized inputs in ledger (G1 blocked)")
    if not ledger.slate:
        reasons.append("no authorized schedule feed loaded")

    for game in sorted(ledger.slate, key=lambda g: g.tip_time):
        if not in_horizon(game.tip_time, issued, horizon_hours):
            continue
        recs: List[PickRecord] = []
        snapshot = tuple(ledger.all_record_ids())
        base = dict(
            issued_at=issued.isoformat(),
            model_version=MODEL_VERSION,
            code_version=ENGINE_VERSION,
            horizon_end=(issued + timedelta(hours=horizon_hours)).isoformat(),
            input_snapshot=snapshot,
        )
        # Injury-unresolved check for both rosters (only named players we have
        # observations for can be resolved; unknown rosters stay unresolved).
        _, all_resolved = roster_scenario(ledger.injuries, [])
        block_reasons = list(reasons)
        if not all_resolved:
            block_reasons.append("availability unresolved for at least one player (G9)")

        forecast = None
        if ledger.games:
            forecast = margin_forecast(
                ledger.games, game.home_team, game.away_team, issued
            )
            if forecast.expected_home_margin is None:
                block_reasons.extend(forecast.notes)
        else:
            block_reasons.append("no authorized team game log; cannot originate a line")

        for market, selection, line_fn, prob_fn in (
            ("spread", f"{game.home_team} (originated line)",
             lambda f: f.originated_spread,
             lambda f: win_probability(f.expected_home_margin, f.margin_sd)),
            ("total", "game total (originated line)",
             lambda f: f.originated_total,
             lambda f: None),
        ):
            if block_reasons:
                recs.append(PickRecord(
                    pick_id=f"{game.game_id}-{market}",
                    market=market,
                    selection=selection,
                    originated_line=None,
                    forecast_probability=None,
                    fair_price=None,
                    benchmark_quote_id=None,
                    status=STATUS_NO_PICK,
                    reason_codes=tuple(dict.fromkeys(block_reasons)),
                    verification="unverified",
                    **base,
                ))
            else:
                # Only reachable once authorized inputs exist and are fresh.
                status = STATUS_SHADOW if allow_shadow else STATUS_NO_PICK
                reasons_here = [] if allow_shadow else [
                    "gates not passed; forecast kept out of picks (enable shadow ledger only after G3-G5)"
                ]
                recs.append(PickRecord(
                    pick_id=f"{game.game_id}-{market}",
                    market=market,
                    selection=selection,
                    originated_line=line_fn(forecast),
                    forecast_probability=prob_fn(forecast),
                    fair_price=None,
                    benchmark_quote_id=None,
                    status=status,
                    reason_codes=tuple(reasons_here) or ("shadow record",),
                    verification="unverified",
                    **base,
                ))
        decisions.append(SlateDecision(game, tuple(recs)))

    run_report = {
        "issued_at": issued.isoformat(),
        "horizon_hours": horizon_hours,
        "slate_games_in_horizon": len(decisions),
        "no_pick_reasons": sorted(set(reasons)),
        "engine_version": ENGINE_VERSION,
        "model_version": MODEL_VERSION,
    }
    return decisions, run_report


def parlay_record(
    legs: Sequence[PickRecord],
    leg_probabilities: Sequence[Optional[float]],
    joint_probability: Optional[float],
    issued_at: datetime,
    game_ids: Sequence[str],
) -> PickRecord:
    """Build a parlay/prop-combo record.

    Same-game legs REQUIRE a measured joint_probability (G8): passing None
    yields NO PICK with reason 'joint dependence unverified'. Cross-game legs
    may use the product of marginals only when the legs share no game.
    """
    same_game = len(set(game_ids)) < len(game_ids)
    reasons: List[str] = []
    prob: Optional[float] = None
    if same_game:
        if joint_probability is None:
            reasons.append("same-game legs: joint dependence unverified (G8)")
        else:
            prob = joint_probability
    else:
        if any(p is None for p in leg_probabilities):
            reasons.append("leg probability missing; parlay not priced")
        else:
            prob = 1.0
            for p in leg_probabilities:
                prob *= float(p)
    status = STATUS_NO_PICK if reasons else STATUS_SHADOW
    return PickRecord(
        pick_id="parlay-" + "+".join(l.pick_id for l in legs),
        issued_at=issued_at.isoformat(),
        model_version=MODEL_VERSION,
        code_version=ENGINE_VERSION,
        market="parlay",
        selection=" + ".join(l.selection for l in legs),
        originated_line=None,
        forecast_probability=prob,
        fair_price=None,
        benchmark_quote_id=None,
        horizon_end=issued_at.isoformat(),
        status=status,
        reason_codes=tuple(reasons) or ("shadow record",),
        input_snapshot=tuple(i for l in legs for i in l.input_snapshot),
        verification="unverified",
    )
