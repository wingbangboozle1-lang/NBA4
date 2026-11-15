"""Luck as a per-team z-score, and the noise band that gates publication.

A team's *luck* in a game is the difference between what the model expected
and what actually happened, expressed in units of the model's own residual
dispersion.  A team whose luck z-score sits far from zero produced an
outcome that the model did not predict - that is variance, not skill.

The publication rule the brief asks for is strict: **a strategy that leans
on a team outside the noise band is refused.**  "Leans on" is made
operational by a declared minimum exposure: a strategy whose weight on a
team is at or above the declared share is said to lean on that team.

Nothing here removes luck from a game; it only makes a strategy's reliance
on variance explicit and refuses to publish strategies that rely on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

__all__ = [
    "NOISE_BAND_Z",
    "DEFAULT_MIN_EXPOSURE",
    "LuckCheck",
    "luck_zscore",
    "team_luck_zscores",
    "is_within_noise_band",
    "teams_outside_noise_band",
    "check_strategy_luck",
]

# --- PROPOSED, UNFITTED policy constants -----------------------------------
# The band is a preregisterable policy choice: a team is "in the noise band"
# while |z| <= NOISE_BAND_Z.  It is declared here so the rule is explicit;
# it is not fitted to any result, because no result exists yet.
NOISE_BAND_Z = 1.0
# A strategy "leans on" a team when its weight on that team reaches this
# share of the strategy's total weight.
DEFAULT_MIN_EXPOSURE = 0.25
# ---------------------------------------------------------------------------


@dataclass
class LuckCheck:
    """Verdict on whether a strategy may be published."""

    verdict: str  # "PUBLISH" | "REFUSE" | "NOT MEASURABLE"
    band_z: float
    min_exposure: float
    offending_teams: Tuple[str, ...]
    zscores: Mapping[str, float]
    notes: Tuple[str, ...] = ()

    @property
    def refused(self) -> bool:
        return self.verdict == "REFUSE"


def luck_zscore(
    expected: Optional[float], actual: Optional[float], residual_sd: Optional[float]
) -> Optional[float]:
    """Signed z-score of a realised result against the model's expectation.

    ``z = (actual - expected) / residual_sd``.  Returns ``None`` when any
    input is missing or the dispersion is not positive: a blank means "not
    measured", never zero.
    """
    if expected is None or actual is None or residual_sd is None:
        return None
    if residual_sd <= 0:
        raise ValueError("residual_sd must be positive")
    return (actual - expected) / residual_sd


def team_luck_zscores(
    expected: Mapping[str, Optional[float]],
    actual: Mapping[str, Optional[float]],
    residual_sds: Mapping[str, Optional[float]],
) -> Dict[str, Optional[float]]:
    """Per-team luck z-scores."""
    teams = set(expected) | set(actual) | set(residual_sds)
    return {
        team: luck_zscore(expected.get(team), actual.get(team), residual_sds.get(team))
        for team in sorted(teams)
    }


def is_within_noise_band(z: Optional[float], band_z: float = NOISE_BAND_Z) -> bool:
    """True when the z-score sits inside the declared noise band."""
    if z is None:
        return False
    return abs(z) <= band_z


def teams_outside_noise_band(
    zscores: Mapping[str, Optional[float]], band_z: float = NOISE_BAND_Z
) -> Tuple[str, ...]:
    """Teams whose measured luck z-score is outside the band."""
    return tuple(
        sorted(
            team
            for team, z in zscores.items()
            if z is not None and abs(z) > band_z
        )
    )


def check_strategy_luck(
    exposures: Mapping[str, float],
    zscores: Mapping[str, Optional[float]],
    band_z: float = NOISE_BAND_Z,
    min_exposure: float = DEFAULT_MIN_EXPOSURE,
) -> LuckCheck:
    """Refuse a strategy that leans on a team outside the noise band.

    ``exposures`` maps a team to the share of the strategy's weight on that
    team.  ``zscores`` maps a team to its measured luck z-score.

    Verdict:

    * ``REFUSE`` - at least one team with a material exposure (weight at or
      above ``min_exposure``) has a measured z-score outside the band;
    * ``PUBLISH`` - every materially exposed team is inside the band;
    * ``NOT MEASURABLE`` - the exposure of a materially relevant team has no
      measured z-score, so the check cannot be made and the strategy is not
      published.
    """
    notes = []
    if not exposures:
        notes.append("no exposures supplied; the luck check cannot be made")
        return LuckCheck("NOT MEASURABLE", band_z, min_exposure, (), {}, tuple(notes))
    total = sum(abs(v) for v in exposures.values())
    if total <= 0:
        notes.append("exposures sum to zero; the luck check cannot be made")
        return LuckCheck("NOT MEASURABLE", band_z, min_exposure, (), {}, tuple(notes))

    offending: list[str] = []
    unmeasured: list[str] = []
    for team, weight in sorted(exposures.items()):
        share = abs(weight) / total
        if share < min_exposure:
            continue
        z = zscores.get(team)
        if z is None:
            unmeasured.append(team)
        elif abs(z) > band_z:
            offending.append(team)

    if unmeasured:
        notes.append(
            "no measured luck z-score for: " + ", ".join(unmeasured)
            + "; the strategy is not published because the check cannot be made"
        )
        return LuckCheck(
            "NOT MEASURABLE", band_z, min_exposure, tuple(offending), dict(zscores),
            tuple(notes),
        )
    if offending:
        notes.append(
            "the strategy leans on team(s) outside the noise band: "
            + ", ".join(offending)
            + f" (|z| > {band_z})"
        )
        notes.append(
            "refused: a strategy that depends on outcomes the model did not "
            "predict is a variance strategy, not a skill strategy"
        )
        return LuckCheck(
            "REFUSE", band_z, min_exposure, tuple(offending), dict(zscores), tuple(notes)
        )
    notes.append(
        f"every materially exposed team (share >= {min_exposure}) is inside the "
        f"noise band (|z| <= {band_z})"
    )
    return LuckCheck(
        "PUBLISH", band_z, min_exposure, (), dict(zscores), tuple(notes)
    )
