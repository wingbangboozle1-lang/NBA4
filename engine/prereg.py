"""Frozen strategy pre-registration files.

The brief requires a pre-registration file per strategy, frozen **before its
first bet**, holding four things:

* the **signal** - what the strategy predicts;
* the **thresholds** - when it publishes and when it is refused;
* the **universe** - which games it may act on;
* the **exact settlement rule** - how a bet is decided.

The point of freezing is that the file cannot be edited after results
exist.  This module therefore:

* writes the file in a canonical form and stores its SHA-256 next to it;
* refuses to overwrite a frozen file whose content differs (the first
  freeze wins; a change means a new version);
* verifies a file against its stored hash on load;
* refuses to let a strategy act if any bet it placed is dated before its
  freeze time.

Every threshold in a pre-registration is a declared policy choice.  A file
that has never been frozen cannot be used to publish anything.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .seal import canonical_hash
from .results import SETTLEMENT_RULES

__all__ = [
    "REQUIRED_FIELDS",
    "Preregistration",
    "freeze",
    "load_preregistration",
    "verify_preregistration",
    "check_first_bet",
]

REQUIRED_FIELDS = ("strategy_id", "signal", "thresholds", "universe", "settlement_rule")
"""The four content fields the brief requires, plus the strategy's identity."""


@dataclass
class Preregistration:
    """One frozen strategy pre-registration."""

    strategy_id: str
    signal: str
    thresholds: Dict[str, Any]
    universe: Dict[str, Any]
    settlement_rule: str
    version: str = "1"
    frozen_at_utc: str = ""
    notes: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def payload(self) -> Dict[str, Any]:
        """The canonical payload that is hashed and written."""
        body = {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "signal": self.signal,
            "thresholds": self.thresholds,
            "universe": self.universe,
            "settlement_rule": self.settlement_rule,
            "frozen_at_utc": self.frozen_at_utc,
            "notes": self.notes,
        }
        if self.extra:
            body["extra"] = self.extra
        return body


def _validate(prereg: Preregistration) -> None:
    for field_name in REQUIRED_FIELDS:
        value = getattr(prereg, field_name)
        if value is None or value == "" or value == {}:
            raise ValueError(f"pre-registration is missing {field_name!r}")
    if prereg.settlement_rule not in SETTLEMENT_RULES:
        raise ValueError(
            f"settlement_rule {prereg.settlement_rule!r} is not a registered rule; "
            f"choose one of {sorted(SETTLEMENT_RULES)}"
        )
    if not prereg.frozen_at_utc:
        raise ValueError("frozen_at_utc is required")


def freeze(prereg: Preregistration, directory: str | Path) -> Tuple[Path, Path, str]:
    """Freeze a pre-registration file and its hash.

    Returns ``(json_path, sha256_path, hash)``.  If a file already exists
    for the same strategy and version, the existing freeze is kept and the
    stored hash is returned; the new content is only written when the file
    does not exist yet.  A different body for an existing version is an
    error - that is a new version, not an edit.
    """
    _validate(prereg)
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{prereg.strategy_id}-v{prereg.version}.json"
    sha_path = root / f"{prereg.strategy_id}-v{prereg.version}.sha256"
    payload = prereg.payload()
    body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    digest = canonical_hash(payload)

    if json_path.exists():
        existing = json.loads(json_path.read_text(encoding="utf-8"))
        if canonical_hash(existing) != digest:
            raise ValueError(
                f"{json_path.name} is already frozen with a different body; "
                "publish a new version instead of editing a frozen file"
            )
        stored = sha_path.read_text(encoding="utf-8").split()[0] if sha_path.exists() else digest
        return json_path, sha_path, stored

    json_path.write_text(body, encoding="utf-8")
    sha_path.write_text(f"{digest}  {json_path.name}\n", encoding="utf-8")
    return json_path, sha_path, digest


def load_preregistration(path: str | Path) -> Preregistration:
    """Load a frozen pre-registration file."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    known = {
        "strategy_id", "version", "signal", "thresholds", "universe",
        "settlement_rule", "frozen_at_utc", "notes",
    }
    extra = {k: v for k, v in payload.items() if k not in known}
    return Preregistration(
        strategy_id=payload["strategy_id"],
        signal=payload["signal"],
        thresholds=payload.get("thresholds", {}),
        universe=payload.get("universe", {}),
        settlement_rule=payload.get("settlement_rule", ""),
        version=str(payload.get("version", "1")),
        frozen_at_utc=payload.get("frozen_at_utc", ""),
        notes=payload.get("notes", ""),
        extra=extra,
    )


def verify_preregistration(path: str | Path) -> Tuple[bool, Tuple[str, ...]]:
    """Check a frozen file against its stored hash."""
    json_path = Path(path)
    reasons: List[str] = []
    if not json_path.is_file():
        return False, (f"{json_path.name} does not exist",)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    digest = canonical_hash(payload)
    sha_path = json_path.with_suffix(".sha256")
    if not sha_path.is_file():
        reasons.append(f"{sha_path.name} is missing; the freeze cannot be verified")
    else:
        stored = sha_path.read_text(encoding="utf-8").split()[0]
        if stored != digest:
            reasons.append(
                "the stored hash does not match the file content; the frozen "
                "pre-registration has been altered"
            )
    try:
        prereg = Preregistration(
            strategy_id=payload["strategy_id"],
            signal=payload["signal"],
            thresholds=payload.get("thresholds", {}),
            universe=payload.get("universe", {}),
            settlement_rule=payload.get("settlement_rule", ""),
            version=str(payload.get("version", "1")),
            frozen_at_utc=payload.get("frozen_at_utc", ""),
            notes=payload.get("notes", ""),
        )
        _validate(prereg)
    except (KeyError, ValueError) as exc:
        reasons.append(f"the file is not a complete pre-registration: {exc}")
    return (not reasons), tuple(reasons)


def check_first_bet(
    prereg: Preregistration,
    bet_times: Sequence[str],
) -> Tuple[bool, Tuple[str, ...]]:
    """Refuse a strategy whose first bet predates its freeze.

    ``bet_times`` are ISO-8601 timestamps of the bets the strategy placed.
    """
    reasons: List[str] = []
    if not prereg.frozen_at_utc:
        reasons.append("the pre-registration has no freeze time")
        return False, tuple(reasons)
    try:
        frozen = datetime.fromisoformat(prereg.frozen_at_utc)
    except ValueError:
        reasons.append("the freeze time is not ISO-8601")
        return False, tuple(reasons)
    if frozen.tzinfo is None:
        frozen = frozen.replace(tzinfo=timezone.utc)
    for raw in bet_times:
        try:
            bet = datetime.fromisoformat(raw)
        except ValueError:
            reasons.append(f"bet timestamp {raw!r} is not ISO-8601")
            continue
        if bet.tzinfo is None:
            bet = bet.replace(tzinfo=timezone.utc)
        if bet < frozen:
            reasons.append(
                f"a bet was placed at {raw}, before the strategy was frozen at "
                f"{prereg.frozen_at_utc}"
            )
    return (not reasons), tuple(reasons)
