"""Snapshot store for official injury reports: revisions, alignment, refusals.

``engine/injuries.py`` resolves a *status* into an availability scenario. This
module owns the layer below it: reading a dated extraction of the official report,
keeping the cells exactly as printed, comparing two consecutive revisions, and
refusing to attach a player to a team when the extracted row lost its team cell at
a page break.

Rules carried from ``data/snapshots/README.md`` and the 2026-11-15 pair
(``data/snapshots/raw/*.pipes``):

* a blank cell stays blank — the report printed nothing there;
* ``NOT YET SUBMITTED`` is a reporting state, not a player status;
* a name-cell difference between two revisions of the same day is a printing
  variance, not a status change;
* alignment is positional when the row counts match, and key-set based (with the
  difference reported as realignment) when they do not.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from .inputs import NO_INPUT, MissingInput, official_link, require

__all__ = [
    "InjuryRow",
    "InjuryRevision",
    "load_revision",
    "diff_revisions",
    "RevisionDiff",
    "team_for_row",
    "status_counts",
    "NOT_YET_SUBMITTED",
]

NOT_YET_SUBMITTED = "NOT YET SUBMITTED"
REPORTING_STATES = (NOT_YET_SUBMITTED,)
CELLS = ("team", "player", "status", "reason")


@dataclass(frozen=True)
class InjuryRow:
    """One printed player row, with a flag for every cell the document omitted."""

    game_date: str
    game_time: str
    matchup: str
    team: str
    player: str
    status: str
    reason: str
    printed: tuple[str, ...] = ("game_date", "game_time", "matchup", "team", "player", "status", "reason")
    position: int = 0

    @property
    def aligned(self) -> bool:
        """True when the row itself says which game/team it belongs to."""
        return bool(self.matchup or self.team)

    @property
    def is_reporting_state(self) -> bool:
        return NOT_YET_SUBMITTED in (self.status, self.reason)

    def as_dict(self) -> dict[str, Any]:
        return {
            "game_date": self.game_date,
            "tip_et": self.game_time,
            "matchup": self.matchup or NO_INPUT,
            "team": self.team or NO_INPUT,
            "player": self.player,
            "status": self.status or NO_INPUT,
            "reason": self.reason or NO_INPUT,
            "unverified": not self.aligned,
            "position": self.position,
        }


@dataclass(frozen=True)
class InjuryRevision:
    """One dated revision of the report, with the timestamps the page prints."""

    revision_label: str  # e.g. "06:00 AM ET" — the report's own revision stamp
    document: str  # the header line the PDF prints, verbatim
    source_url: str
    retrieved_utc: str
    rows: tuple[InjuryRow, ...]
    source_index_url: str = ""

    def __len__(self) -> int:
        return len(self.rows)

    def player_rows(self) -> list[InjuryRow]:
        return [r for r in self.rows if r.player and not r.is_reporting_state]

    def as_dict(self) -> dict[str, Any]:
        return {
            "revision_label": self.revision_label,
            "document": self.document,
            "source_url": self.source_url,
            "retrieved_utc": self.retrieved_utc,
            "rows": len(self.rows),
            "player_rows": len(self.player_rows()),
            "unaligned_rows": sum(1 for r in self.rows if not r.aligned),
        }


def load_revision(path: str | Path) -> InjuryRevision:
    """Read a snapshot JSON produced by ``scripts/build_brief_data.py``."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows: list[InjuryRow] = []
    for game in payload["games"]:
        for raw in game["rows"]:
            rows.append(
                InjuryRow(
                    game_date=game.get("game_date", ""),
                    game_time=game.get("tip_et", ""),
                    matchup=game.get("matchup", ""),
                    team=raw.get("team", ""),
                    player=raw.get("player", ""),
                    status=raw.get("status", ""),
                    reason=raw.get("reason", ""),
                    printed=tuple(k for k in ("team",) if raw.get(k + "_printed", True)),
                    position=len(rows),
                )
            )
    official_link(payload["source_url"], where=f"{payload['snapshot_id']}")
    return InjuryRevision(
        revision_label=payload["revision_et_label"],
        document=payload["source_document"],
        source_url=payload["source_url"],
        retrieved_utc=payload["fetched_at_utc"],
        rows=tuple(rows),
        source_index_url=payload.get("source_index_url", ""),
    )


def team_for_row(row: InjuryRow, blocks: Sequence[tuple[str, str]] = ()) -> str:
    """Return the team a row prints, or refuse.

    ``blocks`` may carry ``(team, first_row_position)`` pairs from a layout-aware
    reader; without that information the team cell of a page-break row is not
    knowable from the row alone, and guessing it from alphabetical order is exactly
    the inference the snapshot rules forbid.
    """
    if row.team:
        return row.team
    for team, start in blocks:
        if start == row.position:
            return team
    raise MissingInput(
        f"{row.player or 'row'}: the row carries no team cell (the document drops it at a page break) and no "
        "block assignment was supplied; the team is not inferred from row order"
    )


def status_counts(rows: Iterable[InjuryRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row.status or (NOT_YET_SUBMITTED if row.reason == NOT_YET_SUBMITTED else "(not printed)")
        counts[key] = counts.get(key, 0) + 1
    return counts


@dataclass(frozen=True)
class RevisionDiff:
    old: dict[str, Any]
    new: dict[str, Any]
    alignment: str
    changes: tuple[dict[str, Any], ...]
    counts: dict[str, int]
    source_url: str

    @property
    def status_changes(self) -> list[dict[str, Any]]:
        return [c for c in self.changes if c["kind"] == "STATUS_CHANGE"]

    def as_rows(self) -> list[list[str]]:
        """Rows for the Injuries page: change, who, from, to, official link."""
        out = []
        for c in self.changes:
            out.append(
                [
                    c["kind"],
                    c.get("player") or c.get("key") or f"position {c.get('position')}",
                    str(c.get("old", "")) or NO_INPUT,
                    str(c.get("new", "")) or NO_INPUT,
                    self.source_url,
                ]
            )
        if not out:
            out.append(
                [
                    "NO_CHANGES",
                    f"{self.counts['new_rows']} rows in both revisions",
                    NO_INPUT,
                    NO_INPUT,
                    self.source_url,
                ]
            )
        return out


def diff_revisions(old: InjuryRevision, new: InjuryRevision, *, source_url: str = "") -> RevisionDiff:
    """Compare two consecutive revisions of the same day's report.

    The report prints rows in one order (game block, team, player alphabetically).
    When both revisions carry the same number of rows the comparison is positional
    and a differing row is a real change; otherwise rows are matched on
    (matchup, team, player) and every unmatched key is reported as a realignment,
    never as a status change.
    """
    require(old.rows, "old revision rows", needed_for="a revision diff")
    require(new.rows, "new revision rows", needed_for="a revision diff")
    old_rows, new_rows = list(old.rows), list(new.rows)
    changes: list[dict[str, Any]] = []

    def ident(row: InjuryRow) -> tuple:
        return (row.matchup, row.team, row.player)

    # Match on what the row itself prints (matchup, team, player). When a key occurs
    # more than once - two page-break rows that print only a name - the nearest
    # unused position wins, because the report keeps its order between revisions.
    used: set[int] = set()
    pairs: list[tuple[int, int]] = []
    unmatched_old: list[int] = []
    for i, a in enumerate(old_rows):
        candidates = [
            j for j, b in enumerate(new_rows) if j not in used and ident(b) == ident(a) and (b.matchup or b.team or b.player)
        ]
        if candidates:
            j = min(candidates, key=lambda j: abs(j - i))
            used.add(j)
            pairs.append((i, j))
        else:
            unmatched_old.append(i)
    unmatched_new = [j for j in range(len(new_rows)) if j not in used]
    alignment = (
        f"key(matchup/team/player) with positional tie-break; {len(pairs)} of {len(old_rows)} old rows and "
        f"{len(new_rows)} new rows matched"
    )
    for i, j in pairs:
        a, b = old_rows[i], new_rows[j]
        for cell, kind in (
            ("status", "STATUS_CHANGE"),
            ("reason", "REASON_CHANGE"),
            ("team", "TEAM_CHANGE"),
        ):
            if a.__dict__[cell] != b.__dict__[cell]:
                changes.append(
                    {
                        "kind": kind,
                        "position": j,
                        "matchup": b.matchup or a.matchup or NO_INPUT,
                        "team": b.team or a.team or NO_INPUT,
                        "player": b.player or a.player,
                        "old": a.__dict__[cell] or NO_INPUT,
                        "new": b.__dict__[cell] or NO_INPUT,
                        "note": "matched on the row's own printed identity cells",
                    }
                )
    # A one-for-one leftover with identical status and reason is the name-spelling
    # case the 2026-11-15 pair actually shows: report it as a printing variance.
    while len(unmatched_old) == len(unmatched_new) == 1:
        i, j = unmatched_old.pop(), unmatched_new.pop()
        a, b = old_rows[i], new_rows[j]
        if a.status == b.status and a.reason == b.reason:
            changes.append(
                {
                    "kind": "PRINTING_VARIANCE",
                    "position": j,
                    "matchup": b.matchup or a.matchup or NO_INPUT,
                    "team": b.team or a.team or NO_INPUT,
                    "player": b.player,
                    "old": a.player or NO_INPUT,
                    "new": b.player or NO_INPUT,
                    "note": "status and reason cells are identical; only the name cell differs in the "
                    "extracted text, so this is a printing variance and not a status change",
                }
            )
        else:
            for k, row in (("REMOVED_OR_REALIGNED", a), ("ADDED_OR_REALIGNED", b)):
                changes.append(
                    {
                        "kind": k,
                        "position": row.position,
                        "key": " / ".join(x or NO_INPUT for x in ident(row)),
                        "note": "no counterpart with the same printed identity cells; reported as a "
                        "realignment, not as a status change",
                    }
                )
    for i in unmatched_old:
        changes.append({"kind": "REMOVED_OR_REALIGNED", "position": i,
                        "key": " / ".join(x or NO_INPUT for x in ident(old_rows[i]))})
    for j in unmatched_new:
        changes.append({"kind": "ADDED_OR_REALIGNED", "position": j,
                        "key": " / ".join(x or NO_INPUT for x in ident(new_rows[j]))})
    link = official_link(source_url or new.source_url, where="injury revision diff")
    return RevisionDiff(
        old=old.as_dict(),
        new=new.as_dict(),
        alignment=alignment,
        changes=tuple(changes),
        counts={
            "old_rows": len(old_rows),
            "new_rows": len(new_rows),
            "status_changes": sum(1 for c in changes if c["kind"] == "STATUS_CHANGE"),
            "reason_changes": sum(1 for c in changes if c["kind"] == "REASON_CHANGE"),
            "team_changes": sum(1 for c in changes if c["kind"] == "TEAM_CHANGE"),
            "printing_variances": sum(1 for c in changes if c["kind"] == "PRINTING_VARIANCE"),
            "realigned": sum(1 for c in changes if c["kind"].endswith("REALIGNED")),
        },
        source_url=link,
    )
