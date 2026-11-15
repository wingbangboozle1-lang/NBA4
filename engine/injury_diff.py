"""Diff two consecutive official injury reports.

The brief requires every injury PDF to be stored with its timestamp and
consecutive reports to be diffed to detect status changes.  This module does
the diffing; the storage side lives in ``data/snapshots/``.

A diff reports, per player:

* the status and reason in the earlier report and in the later one;
* whether the status changed, and to what;
* whether the player appeared, disappeared, or stayed the same.

A player whose status is unchanged but whose reason changed is reported as a
``reason`` change, not a status change, so that a status change always means
the player's participation status actually moved.

Reports are matched on (team, player).  When a player moves between teams
between two reports, the move is reported as a removal from the old team and
an addition to the new one rather than being silently merged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "InjuryRow",
    "StatusChange",
    "InjuryDiff",
    "diff_reports",
]


@dataclass(frozen=True)
class InjuryRow:
    """One row of an official injury report."""

    team: str
    player: str
    status: str
    reason: str = ""

    @property
    def key(self) -> Tuple[str, str]:
        return (self.team, self.player)


@dataclass
class StatusChange:
    """One player's movement between two reports."""

    team: str
    player: str
    previous_status: Optional[str]
    current_status: Optional[str]
    previous_reason: Optional[str]
    current_reason: Optional[str]
    change: str  # "status" | "reason" | "added" | "removed"

    @property
    def is_status_change(self) -> bool:
        return self.change == "status"


@dataclass
class InjuryDiff:
    """The difference between two consecutive official reports."""

    previous_report_time: str
    current_report_time: str
    changes: Tuple[StatusChange, ...] = ()
    unchanged_count: int = 0
    previous_row_count: int = 0
    current_row_count: int = 0
    notes: Tuple[str, ...] = ()

    @property
    def status_changes(self) -> Tuple[StatusChange, ...]:
        return tuple(c for c in self.changes if c.change == "status")

    @property
    def added(self) -> Tuple[StatusChange, ...]:
        return tuple(c for c in self.changes if c.change == "added")

    @property
    def removed(self) -> Tuple[StatusChange, ...]:
        return tuple(c for c in self.changes if c.change == "removed")

    @property
    def reason_changes(self) -> Tuple[StatusChange, ...]:
        return tuple(c for c in self.changes if c.change == "reason")


def diff_reports(
    previous_rows: Sequence[InjuryRow],
    current_rows: Sequence[InjuryRow],
    previous_report_time: str,
    current_report_time: str,
) -> InjuryDiff:
    """Diff two consecutive injury reports.

    ``previous_report_time`` and ``current_report_time`` are the timestamps
    the reports themselves carry; they are carried into the result so the
    diff is never published without the two times it compares.
    """
    notes: List[str] = []
    if not previous_report_time or not current_report_time:
        notes.append(
            "one of the reports has no timestamp; the diff is not usable as a "
            "revision history"
        )
    prev: Dict[Tuple[str, str], InjuryRow] = {r.key: r for r in previous_rows}
    curr: Dict[Tuple[str, str], InjuryRow] = {r.key: r for r in current_rows}

    changes: List[StatusChange] = []
    unchanged = 0
    for key in sorted(set(prev) | set(curr)):
        p = prev.get(key)
        c = curr.get(key)
        if p is not None and c is not None:
            if p.status != c.status:
                changes.append(
                    StatusChange(
                        c.team, c.player, p.status, c.status, p.reason, c.reason, "status"
                    )
                )
            elif p.reason != c.reason:
                changes.append(
                    StatusChange(
                        c.team, c.player, p.status, c.status, p.reason, c.reason, "reason"
                    )
                )
            else:
                unchanged += 1
        elif c is not None:
            changes.append(
                StatusChange(c.team, c.player, None, c.status, None, c.reason, "added")
            )
        elif p is not None:
            changes.append(
                StatusChange(p.team, p.player, p.status, None, p.reason, None, "removed")
            )

    return InjuryDiff(
        previous_report_time=previous_report_time,
        current_report_time=current_report_time,
        changes=tuple(changes),
        unchanged_count=unchanged,
        previous_row_count=len(previous_rows),
        current_row_count=len(current_rows),
        notes=tuple(notes),
    )
