"""Per-player game-log capture for the players who appear on an injury report.

Brief item implemented (2026-11-16): "Capture per-player game logs (minutes,
points, rebounds, assists, and the opponent) for at least the players who
appear on an injury report."

Why the opponent is a required field and not a nice-to-have: without it a
game log cannot be conditioned on opponent defensive quality, which is the only
reason to store per-game (rather than per-season) logs at all. A row that does
not know who it was played against is therefore rejected at ingest rather than
stored with a blank and filled in later.

The module deliberately stops at *capture*. It does not model: the shrinkage
and minutes-x-rate machinery already lives in :mod:`engine.player_props`, and
duplicating it here would put two unvalidated copies of the same estimate in
one repository.

Rules enforced, all of them refusing rather than repairing:

* **One row per player-game.** A second row for the same ``(player_id,
  event_id)`` either agrees with the first (recorded as corroboration) or
  raises :class:`LogConflict`. It never overwrites.
* **Minutes cannot exceed the game.** ``minutes`` is checked against
  ``48 + 5 * overtime_periods``; a player cannot play more minutes than the game
  lasted, so a higher value is a source error, not a rounding issue.
* **A missing player is missing, not zero.** :func:`PlayerLogBook.coverage`
  reports the roster players with no log as ``LOG_MISSING``. Absence from a
  game log means "did not play / not captured", and both are different from
  "played and produced nothing"; the module refuses to collapse them.
* **Rights gate at the point of use.** :func:`PlayerLogBook.model_inputs`
  runs :func:`engine.contracts.require_allowed_use`, so an uncleared log can be
  stored for research but cannot feed a bet surface.

Nothing here fetches and nothing here holds NBA data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .contracts import Provenance, canonical_json, require_allowed_use, snapshot_hash

__all__ = [
    "PlayerLogError",
    "LogConflict",
    "PlayerGameLog",
    "CoverageReport",
    "PlayerLogBook",
    "LOG_MISSING",
    "REGULATION_MINUTES",
    "OVERTIME_MINUTES",
]

REGULATION_MINUTES = 48.0
OVERTIME_MINUTES = 5.0
LOG_MISSING = "LOG_MISSING"
LOG_CAPTURED = "LOG_CAPTURED"
LOG_UNCLEARED = "LOG_UNCLEARED"


class PlayerLogError(ValueError):
    """Raised when a game-log row violates the capture contract."""


class LogConflict(PlayerLogError):
    """Raised when two observations of the same player-game disagree."""


@dataclass(frozen=True)
class PlayerGameLog:
    """One player in one game, as an official game log prints it."""

    player_id: str
    player_name: str
    team_id: str
    opponent_team_id: str
    event_id: str
    game_date: str
    minutes: float
    points: float
    rebounds: float
    assists: float
    provenance: Provenance
    overtime_periods: int = 0

    def __post_init__(self) -> None:
        if not self.player_id or not self.event_id:
            raise PlayerLogError("player_id and event_id are required")
        if not self.team_id or not self.opponent_team_id:
            raise PlayerLogError(
                f"{self.player_id}/{self.event_id}: team_id and opponent_team_id are both "
                "required; a log that does not know the opponent cannot be conditioned on it"
            )
        if self.team_id == self.opponent_team_id:
            raise PlayerLogError(
                f"{self.player_id}/{self.event_id}: a team cannot play itself"
            )
        for name in ("minutes", "points", "rebounds", "assists"):
            if getattr(self, name) < 0:
                raise PlayerLogError(f"{self.player_id}/{self.event_id}: {name} cannot be negative")
        if self.overtime_periods < 0:
            raise PlayerLogError(
                f"{self.player_id}/{self.event_id}: overtime_periods cannot be negative"
            )
        ceiling = REGULATION_MINUTES + OVERTIME_MINUTES * self.overtime_periods
        if self.minutes > ceiling:
            raise PlayerLogError(
                f"{self.player_id}/{self.event_id}: minutes {self.minutes} exceed the game "
                f"length {ceiling} ({self.overtime_periods} overtime period(s)); "
                "a player cannot play longer than the game lasted"
            )

    @property
    def key(self) -> Tuple[str, str]:
        return (self.player_id, self.event_id)

    @property
    def played(self) -> bool:
        return self.minutes > 0

    def per_minute(self, stat: str) -> Optional[float]:
        """Rate for one counting stat, or ``None`` when the player did not play.

        A zero-minute game has no rate; returning 0.0 would be a fabricated
        value, so the module returns ``None`` and the caller decides.
        """
        if not self.played:
            return None
        if stat not in ("points", "rebounds", "assists"):
            raise PlayerLogError(f"unknown stat {stat!r}")
        return getattr(self, stat) / self.minutes

    def as_dict(self) -> Dict[str, object]:
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "team_id": self.team_id,
            "opponent_team_id": self.opponent_team_id,
            "event_id": self.event_id,
            "game_date": self.game_date,
            "minutes": self.minutes,
            "points": self.points,
            "rebounds": self.rebounds,
            "assists": self.assists,
            "overtime_periods": self.overtime_periods,
            "source_url": self.provenance.source_url,
            "allowed_use": self.provenance.allowed_use,
        }


@dataclass(frozen=True)
class CoverageReport:
    """Who on the requested roster has logs, and who does not.

    ``unknown`` holds roster entries that are not in the book under any id, so
    an id-mismatch between the injury report and the game log shows up as a
    coverage gap rather than as a silent zero.
    """

    roster: Tuple[str, ...]
    captured: Tuple[str, ...]
    missing: Tuple[str, ...]
    uncleared: Tuple[str, ...]

    @property
    def coverage_fraction(self) -> float:
        if not self.roster:
            return 0.0
        return len(self.captured) / len(self.roster)

    def as_dict(self) -> Dict[str, object]:
        return {
            "roster_size": len(self.roster),
            "captured": len(self.captured),
            "missing": list(self.missing),
            "uncleared": list(self.uncleared),
            "coverage_fraction": round(self.coverage_fraction, 4),
            "note": (
                "missing means no log row exists for that player; it is never treated as a "
                "line of zeros"
            ),
        }


@dataclass
class PlayerLogBook:
    """An append-only book of player-game logs with corroboration."""

    logs: Dict[Tuple[str, str], PlayerGameLog] = field(default_factory=dict)
    corroborations: Dict[Tuple[str, str], int] = field(default_factory=dict)
    rejected: List[str] = field(default_factory=list)

    def add(self, log: PlayerGameLog) -> bool:
        """Ingest one log. Returns True when it is new, False when corroborated.

        A second observation that agrees is counted and not stored twice; one
        that disagrees raises :class:`LogConflict` so the disagreement is
        investigated rather than averaged away.
        """
        existing = self.logs.get(log.key)
        if existing is None:
            self.logs[log.key] = log
            return True
        if (
            existing.minutes == log.minutes
            and existing.points == log.points
            and existing.rebounds == log.rebounds
            and existing.assists == log.assists
            and existing.opponent_team_id == log.opponent_team_id
        ):
            self.corroborations[log.key] = self.corroborations.get(log.key, 0) + 1
            return False
        raise LogConflict(
            f"{log.player_id}/{log.event_id}: a second official observation disagrees "
            f"(stored min {existing.minutes} pts {existing.points} reb {existing.rebounds} "
            f"ast {existing.assists} vs new min {log.minutes} pts {log.points} "
            f"reb {log.rebounds} ast {log.assists}); the conflict is not resolved here"
        )

    def extend(self, logs: Iterable[PlayerGameLog]) -> int:
        added = 0
        for log in logs:
            if self.add(log):
                added += 1
        return added

    def __len__(self) -> int:
        return len(self.logs)

    def logs_for(self, player_id: str) -> Tuple[PlayerGameLog, ...]:
        return tuple(
            sorted(
                (log for log in self.logs.values() if log.player_id == player_id),
                key=lambda log: (log.game_date, log.event_id),
            )
        )

    def coverage(self, roster: Sequence[str]) -> CoverageReport:
        """Coverage of the roster that appears on an injury report."""
        roster_tuple = tuple(dict.fromkeys(roster))
        captured, missing, uncleared = [], [], []
        for player_id in roster_tuple:
            rows = self.logs_for(player_id)
            if not rows:
                missing.append(player_id)
                continue
            captured.append(player_id)
            if any(not log.provenance.allowed_use for log in rows):
                uncleared.append(player_id)
        return CoverageReport(
            roster=roster_tuple,
            captured=tuple(captured),
            missing=tuple(missing),
            uncleared=tuple(uncleared),
        )

    def model_inputs(self, roster: Sequence[str], purpose: str = "betting model input") -> Dict[str, object]:
        """The rows a model may consume, or a rights refusal.

        Runs the rights gate over every log of every rostered player and raises
        :class:`~engine.contracts.RightsError` on the first uncleared row. A
        partial roster is never returned: a model that saw some of the injured
        players and not others would be conditioning on an arbitrary subset.
        """
        report = self.coverage(roster)
        if report.missing:
            raise PlayerLogError(
                f"{LOG_MISSING}: {', '.join(report.missing)}; a game log is not inferred "
                "for a player who has none"
            )
        for player_id in report.roster:
            for log in self.logs_for(player_id):
                require_allowed_use(log, purpose=purpose)
        rows: List[Dict[str, object]] = []
        for player_id in report.roster:
            for log in self.logs_for(player_id):
                row = log.as_dict()
                row["source_retrieved_at"] = log.provenance.observed_at.isoformat()
                rows.append(row)
        return {
            "rows": rows,
            "players": list(report.roster),
            "corroborated_rows": sum(self.corroborations.values()),
            "coverage": report.as_dict(),
            "inputs_hash": self.canonical_hash(roster),
        }

    def canonical_hash(self, roster: Sequence[str] = ()) -> str:
        """A tamper-evident digest of the book (or of one roster's rows)."""
        if roster:
            keys = sorted(
                (player_id, log.event_id)
                for player_id in dict.fromkeys(roster)
                for log in self.logs_for(player_id)
            )
        else:
            keys = sorted(self.logs)
        payload = [self.logs[key].as_dict() for key in keys]
        return snapshot_hash({"logs": payload})

    def summary(self) -> Dict[str, object]:
        players = {log.player_id for log in self.logs.values()}
        games = {log.event_id for log in self.logs.values()}
        return {
            "log_rows": len(self.logs),
            "distinct_players": len(players),
            "distinct_games": len(games),
            "corroborated_rows": sum(self.corroborations.values()),
            "corroborated_distinct": len(self.corroborations),
            "uncleared_rows": sum(
                1 for log in self.logs.values() if not log.provenance.allowed_use
            ),
            "canonical_hash": self.canonical_hash(),
        }
