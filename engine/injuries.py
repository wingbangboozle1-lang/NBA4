"""Injury status -> availability scenarios (hypothesis S5).

The official NBA injury report supplies a reported participation status and
reason at a point in time (see docs/sources.md NBA-03/NBA-04). It does NOT
supply minutes or production. This module therefore keeps three separate,
explicitly labelled steps:

    status observation  ->  availability scenario  ->  minutes multiplier

The mapping tables below are PROPOSED, UNVALIDATED scenario parameters
(docs/engine.md). They are placeholders for a model that must later be
validated prospectively against authorized minutes outcomes. An unknown or
missing status yields an UNRESOLVED state which suppresses picks (G9).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

from .schema import InjuryObservation, VALID_STATUSES

# --- PROPOSED, UNVALIDATED scenario mapping ---------------------------------
AVAILABILITY_PROB: Dict[str, float] = {
    "Out": 0.0,
    "Doubtful": 0.25,
    "Questionable": 0.5,
    "Probable": 0.9,
    "Available": 1.0,
}
MINUTES_MULTIPLIER: Dict[str, float] = {
    "Out": 0.0,
    "Doubtful": 0.4,
    "Questionable": 0.7,
    "Probable": 1.0,
    "Available": 1.0,
}
# ---------------------------------------------------------------------------

UNRESOLVED = "UNRESOLVED"


@dataclass
class AvailabilityScenario:
    player: str
    status: str
    availability_prob: Optional[float]
    minutes_multiplier: Optional[float]
    report_time: Optional[str]
    source_url: Optional[str]
    resolved: bool
    notes: Tuple[str, ...]


def latest_status(
    observations: Sequence[InjuryObservation], player: str
) -> Optional[InjuryObservation]:
    """Most recent report row for a player (by the report's own timestamp)."""
    rows = [o for o in observations if o.player == player]
    if not rows:
        return None

    def _report_dt(o: InjuryObservation):
        from datetime import datetime

        return datetime.fromisoformat(o.report_time)

    return max(rows, key=_report_dt)


def availability_scenario(
    observations: Sequence[InjuryObservation], player: str
) -> AvailabilityScenario:
    obs = latest_status(observations, player)
    if obs is None:
        return AvailabilityScenario(
            player, UNRESOLVED, None, None, None, None, False,
            ("no authorized injury observation for this player; pick suppression on",),
        )
    if obs.status not in VALID_STATUSES:
        return AvailabilityScenario(
            player, UNRESOLVED, None, None, obs.report_time,
            obs.provenance.source_url, False,
            (f"status {obs.status!r} is not a recognised report value",),
        )
    return AvailabilityScenario(
        player,
        obs.status,
        AVAILABILITY_PROB[obs.status],
        MINUTES_MULTIPLIER[obs.status],
        obs.report_time,
        obs.provenance.source_url,
        True,
        (
            "availability/minutes mapping is PROPOSED and UNVALIDATED; "
            "the report status is an observation, not a minutes projection",
        ),
    )


def roster_scenario(
    observations: Sequence[InjuryObservation], players: Sequence[str]
) -> Tuple[Dict[str, AvailabilityScenario], bool]:
    """Scenario state for a list of players.

    Returns (scenarios, all_resolved). all_resolved=False means at least one
    player has no/unknown status and any dependent pick must be suppressed.
    """
    out: Dict[str, AvailabilityScenario] = {}
    all_resolved = True
    for p in players:
        scen = availability_scenario(observations, p)
        out[p] = scen
        if not scen.resolved:
            all_resolved = False
    return out, all_resolved
