"""Conference seeding and the official tie-break chain (task AN, gap 6).

The authority is the NBA.com standings page legend, "Tie-Breaking Procedures":

* **L.2.a (two teams)** — (1) better win-loss percentage in games among the tied
  clubs; (2) if all tied clubs are in the same division, better win-loss percentage
  within that division; (3) better win-loss percentage against teams in its own
  division; (4) better win-loss percentage in its own conference; (5) better
  win-loss percentage in regular-season games against playoff-eligible teams in its
  own conference; (6) the same against playoff-eligible teams in the other
  conference; (7) better regular-season point differential.
* **L.2.b (three or more teams)** — the same criteria applied to the subset of tied
  clubs, with criterion (2) applying only when all tied clubs are in one division,
  and a criterion that separates one club moving that club out before the next
  criterion is applied to the remainder.

This module implements the walk **and** the refusal: a criterion whose input was not
supplied stops the chain, because skipping ahead would produce an order the rule
does not authorise. The only permitted skip is the one the rule itself prints (an
inapplicable division criterion), and it requires an explicit flag rather than an
absent value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .inputs import NO_INPUT, MissingInput, require

__all__ = ["Criterion", "TieInputs", "TieResolution", "resolve_two_team", "resolve_multi_team", "record"]

# Criterion names in the order the rule prints them (L.2.a).
CRITERIA: tuple[str, ...] = (
    "head_to_head",
    "same_division_best_division_pct",
    "own_division_pct",
    "own_conference_pct",
    "playoff_eligible_own_conference_pct",
    "playoff_eligible_other_conference_pct",
    "point_differential",
)


@dataclass(frozen=True)
class Criterion:
    name: str
    index: int
    applied: bool
    value_a: float | None
    value_b: float | None
    outcome: str
    note: str = ""


def record(wins: int, losses: int) -> str:
    """Format a win-loss record exactly as the standings page prints it."""
    require(wins, "wins", needed_for="a record string")
    return f"{wins}-{losses}"


@dataclass(frozen=True)
class TieInputs:
    """Everything one tied club contributes to the chain.

    ``None`` means "not supplied", which is different from ``0.0`` ("the page
    prints 0.000"). Percentages are given as fractions, point differential as the
    printed league value.
    """

    team: str
    head_to_head: float | None = None  # win-loss % in games among the tied clubs
    same_division: bool | None = None  # True/False only when the division tie-break applies
    division_winner: bool | None = None
    own_division_pct: float | None = None
    own_conference_pct: float | None = None
    eligible_own_conference_pct: float | None = None
    eligible_other_conference_pct: float | None = None
    point_differential: float | None = None
    source_url: str = ""

    def value_for(self, name: str) -> float | None:
        return {
            "head_to_head": self.head_to_head,
            "same_division_best_division_pct": None,
            "own_division_pct": self.own_division_pct,
            "own_conference_pct": self.own_conference_pct,
            "playoff_eligible_own_conference_pct": self.eligible_own_conference_pct,
            "playoff_eligible_other_conference_pct": self.eligible_other_conference_pct,
            "point_differential": self.point_differential,
        }[name]


@dataclass(frozen=True)
class TieResolution:
    higher: str | None
    criteria: tuple[Criterion, ...]
    stopped_at: int | None = None
    reason: str = ""
    source_url: str = ""

    @property
    def resolved(self) -> bool:
        return self.higher is not None

    def as_rows(self) -> list[list[str]]:
        rows = []
        for c in self.criteria:
            rows.append(
                [
                    f"{c.index + 1}. {c.name}",
                    "applied" if c.applied else "not reached" if c.outcome == "NOT REACHED" else c.outcome,
                    f"{c.value_a:.4f}" if isinstance(c.value_a, float) else (c.value_a or NO_INPUT),
                    f"{c.value_b:.4f}" if isinstance(c.value_b, float) else (c.value_b or NO_INPUT),
                    c.note or NO_INPUT,
                    self.source_url,
                ]
            )
        return rows


def _compare(a: TieInputs, b: TieInputs, name: str, index: int, *, exception_note: str = "") -> Criterion:
    va, vb = a.value_for(name), b.value_for(name)
    if name == "same_division_best_division_pct":
        if a.same_division is None or b.same_division is None:
            raise MissingInput(
                f"{name}: the rule applies this criterion only when all tied clubs are in one division, and "
                f"{a.team}/{b.team} did not supply same_division; skipping ahead is not allowed"
            )
        if not (a.same_division and b.same_division):
            return Criterion(name, index, False, None, None, "NOT APPLICABLE", exception_note or "tied clubs are in different divisions; L.2.a prints this as an inapplicable step")
        va, vb = (1.0 if a.division_winner else 0.0), (1.0 if b.division_winner else 0.0)
    if va is None or vb is None:
        raise MissingInput(
            f"{name}: one or both tied clubs ({a.team}, {b.team}) have no printed value; the chain stops "
            "rather than skipping a criterion"
        )
    if abs(va - vb) < 1e-12:
        return Criterion(name, index, True, va, vb, "NO SEPARATION", "equal on this criterion; move to the next")
    winner = a.team if va > vb else b.team
    return Criterion(name, index, True, va, vb, f"SEPARATED: {winner}", "first criterion that separates the tied clubs decides")


def resolve_two_team(a: TieInputs, b: TieInputs, *, source_url: str = "") -> TieResolution:
    """Walk the L.2.a chain for two tied clubs, stopping at the first separation."""
    seen: list[Criterion] = []
    for index, name in enumerate(CRITERIA):
        try:
            step = _compare(a, b, name, index)
        except MissingInput as exc:
            return TieResolution(None, tuple(seen), index, str(exc), source_url or a.source_url or b.source_url)
        seen.append(step)
        if step.applied and step.outcome.startswith("SEPARATED"):
            return TieResolution(step.outcome.split(": ", 1)[1], tuple(seen), None, "decided by criterion " f"{index + 1}", source_url or a.source_url or b.source_url)
    return TieResolution(None, tuple(seen), len(CRITERIA), "tied on every published criterion", source_url or a.source_url or b.source_url)


def resolve_multi_team(clubs: Sequence[TieInputs], *, source_url: str = "") -> dict[str, Any]:
    """L.2.b: peel off clubs one criterion at a time until a step separates one club.

    Returns the ordered groups found so far plus a refusal record when the chain
    cannot continue, because with three or more clubs a criterion that separates
    two of them does not fully order the group.
    """
    if len(clubs) < 3:
        raise MissingInput("L.2.b is the multi-team procedure; use resolve_two_team for two clubs")
    remaining = list(clubs)
    groups: list[list[str]] = []
    notes: list[str] = []

    def refusal(index: int, reason: str, *, club: TieInputs | None = None) -> dict[str, Any]:
        return {
            "ordered": groups,
            "unresolved": [c.team for c in remaining],
            "stopped_at": index,
            "reason": reason,
            "notes": notes,
            "source_url": source_url or (club.source_url if club else ""),
        }

    for index, name in enumerate(CRITERIA):
        if len(remaining) < 2:
            break
        if name == "same_division_best_division_pct":
            if any(c.same_division is None for c in remaining):
                return refusal(index, f"{name}: same_division is not supplied for every club in the tied group; "
                                      "the rule applies this step only when all tied clubs share a division")
            if not all(c.same_division for c in remaining):
                notes.append(f"criterion {index + 1} ({name}) not applicable: the tied clubs are in different divisions")
                continue
            values = [1.0 if c.division_winner else 0.0 for c in remaining]
        else:
            values = []
            for club in remaining:
                value = club.value_for(name)
                if value is None:
                    return refusal(index, f"{name}: {club.team} has no printed value; the chain stops rather "
                                          f"than skipping criterion {index + 1}", club=club)
                values.append(value)
        best = max(values)
        top = [c.team for c, v in zip(remaining, values) if abs(v - best) < 1e-12]
        if len(top) < len(remaining):
            groups.append(top)
            notes.append(f"criterion {index + 1} ({name}) lifted {', '.join(top)} out of the tied group")
            remaining = [c for c in remaining if c.team not in top]
        else:
            notes.append(f"criterion {index + 1} ({name}) did not separate any club")
    return {
        "ordered": groups,
        "unresolved": [c.team for c in remaining],
        "stopped_at": None if not remaining else len(CRITERIA),
        "reason": "every published criterion applied" if not remaining else "criteria exhausted; still tied",
        "notes": notes,
        "source_url": source_url or (remaining[0].source_url if remaining else ""),
    }
