"""Authorized-inputs ledger loading and integrity checks (gate G1).

The ledger is a directory of JSONL files:
    games.jsonl      TeamGame records
    players.jsonl    PlayerGame records
    injuries.jsonl   InjuryObservation records
    slate.jsonl      SlateGame records
    quotes.jsonl     MarketQuote records   (optional)

A record that lacks an official https source, source_time or observed_at is
REJECTED, never silently accepted or defaulted. `integrity_report` is the
machine-checkable part of gate G1 in docs/validation-plan.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Type

from .schema import (
    InjuryObservation,
    MarketQuote,
    PickRecord,
    PlayerGame,
    Provenance,
    SchemaError,
    SlateGame,
    TeamGame,
)

FILE_TYPES: dict = {
    "games.jsonl": TeamGame,
    "players.jsonl": PlayerGame,
    "injuries.jsonl": InjuryObservation,
    "slate.jsonl": SlateGame,
    "quotes.jsonl": MarketQuote,
}


@dataclass
class Ledger:
    """Loaded, validated ledger contents."""

    games: List[TeamGame] = field(default_factory=list)
    players: List[PlayerGame] = field(default_factory=list)
    injuries: List[InjuryObservation] = field(default_factory=list)
    slate: List[SlateGame] = field(default_factory=list)
    quotes: List[MarketQuote] = field(default_factory=list)
    rejected: List[Tuple[str, str]] = field(default_factory=list)  # (where, error)

    @property
    def is_empty(self) -> bool:
        return not (self.games or self.players or self.injuries or self.slate)

    def all_record_ids(self) -> List[str]:
        ids: List[str] = []
        for group in (self.games, self.players, self.injuries, self.slate, self.quotes):
            ids.extend(r.record_id for r in group)
        return ids


def _load_file(path: Path, record_cls: Type, ledger: Ledger, sink: List) -> None:
    if not path.is_file():
        return
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        where = f"{path.name}:{line_no}"
        try:
            payload = json.loads(line)
            prov = payload.get("provenance")
            if isinstance(prov, dict):
                payload["provenance"] = Provenance(**prov)
            record = record_cls(**payload)
            record.validate()
            sink.append(record)
        except (json.JSONDecodeError, TypeError, SchemaError) as exc:
            ledger.rejected.append((where, str(exc)))


def load_ledger(directory: str | Path, allow_synthetic: bool = False) -> Ledger:
    """Load and validate a ledger directory.

    allow_synthetic=True is for the engine's own tests/selftest only. Real
    pipeline runs must leave it False so labelled synthetic rows cannot leak
    into a published forecast.
    """
    root = Path(directory)
    ledger = Ledger()
    if not root.is_dir():
        return ledger
    _load_file(root / "games.jsonl", TeamGame, ledger, ledger.games)
    _load_file(root / "players.jsonl", PlayerGame, ledger, ledger.players)
    _load_file(root / "injuries.jsonl", InjuryObservation, ledger, ledger.injuries)
    _load_file(root / "slate.jsonl", SlateGame, ledger, ledger.slate)
    _load_file(root / "quotes.jsonl", MarketQuote, ledger, ledger.quotes)
    if not allow_synthetic:
        def _strip_synthetic(group: List) -> List:
            return [r for r in group if not getattr(r, "synthetic", False)]
        # TeamGame et al. are frozen dataclasses without a synthetic flag;
        # synthetic fixtures use source_url https://synthetic.invalid/... and
        # are filtered here so they can never enter a production run.
        def _is_synth(record) -> bool:
            return "synthetic.invalid" in record.provenance.source_url
        ledger.games = [r for r in ledger.games if not _is_synth(r)]
        ledger.players = [r for r in ledger.players if not _is_synth(r)]
        ledger.injuries = [r for r in ledger.injuries if not _is_synth(r)]
        ledger.slate = [r for r in ledger.slate if not _is_synth(r)]
        ledger.quotes = [r for r in ledger.quotes if not _is_synth(r)]
    return ledger


@dataclass
class IntegrityReport:
    """Result of the G1 structural gate."""

    loaded: int
    rejected: int
    missing_files: Tuple[str, ...]
    duplicate_record_ids: Tuple[str, ...]
    passed: bool
    notes: Tuple[str, ...]


def integrity_report(ledger: Ledger, directory: str | Path) -> IntegrityReport:
    root = Path(directory)
    missing = tuple(name for name in FILE_TYPES if not (root / name).is_file())
    ids = ledger.all_record_ids()
    duplicates = tuple(sorted({i for i in ids if ids.count(i) > 1}))
    loaded = len(ids)
    rejected = len(ledger.rejected)
    notes: List[str] = []
    if missing:
        notes.append(f"missing ledger files: {', '.join(missing)}")
    if duplicates:
        notes.append(f"duplicate record ids: {', '.join(duplicates)}")
    for where, err in ledger.rejected[:10]:
        notes.append(f"rejected {where}: {err}")
    passed = rejected == 0 and not duplicates and loaded > 0
    return IntegrityReport(
        loaded=loaded,
        rejected=rejected,
        missing_files=missing,
        duplicate_record_ids=duplicates,
        passed=passed,
        notes=tuple(notes),
    )


def write_pick_record(path: str | Path, record: PickRecord) -> None:
    """Append one forecast record to a picks ledger (JSONL, one object/line)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
