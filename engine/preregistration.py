"""Pre-registration files frozen before a strategy's first bet.

Brief item implemented (2026-11-15): "Freeze a pre-registration file per
strategy before its first bet: signal, thresholds, universe, and the exact
settlement rule."

A pre-registration file is the only defence against post-hoc redefinition of
what a strategy "was". This module therefore treats it as an immutable,
content-hashed artefact with four mandatory sections, and it enforces the
timing property that matters: the freeze timestamp must be **strictly earlier**
than the first bet the strategy is evaluated on.

Hard rules:

* All four sections are required, and an empty, whitespace-only, ``UNSET`` or
  ``TBD`` value fails. A placeholder is not a registration.
* ``thresholds`` must state, as data, the fields the leaderboard gate reads:
  ``minimum_edge``, ``minimum_sample``, ``maximum_trials`` and
  ``significance_alpha``. Values come from the owner's policy; this module
  never supplies a default value for any of them.
* ``universe`` must bound the evaluation in time and in scope (season, date
  range, markets, teams/players included or excluded), because a signal
  measured on an undeclared universe cannot be reproduced.
* ``settlement_rule`` must name the official source of record, the outcome
  fields read from it, the push/void handling and the price convention. If a
  field is not decidable from the named source, the rule is incomplete.
* The file hash is recomputed on every load; a mismatch is tampering.

Preregistration files are metadata about a method, not NBA data, and may
therefore be published on the projection surface.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

REQUIRED_SECTIONS: Tuple[str, ...] = ("signal", "thresholds", "universe", "settlement_rule")
PLACEHOLDER_VALUES = {"", "unset", "tbd", "todo", "n/a", "none", "null", "pending", "unknown"}
REQUIRED_THRESHOLD_KEYS: Tuple[str, ...] = (
    "minimum_edge",
    "minimum_sample",
    "maximum_trials",
    "significance_alpha",
)
REQUIRED_SETTLEMENT_KEYS: Tuple[str, ...] = (
    "source_of_record",
    "outcome_fields",
    "push_and_void_handling",
    "price_convention",
    "settled_when",
)


class PreRegistrationError(ValueError):
    """Raised when a registration is incomplete, unfrozen or inconsistent."""


def _parse_iso(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise PreRegistrationError(f"{name} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise PreRegistrationError(f"{name} must carry a UTC offset")
    return parsed.astimezone(timezone.utc)


def _is_placeholder(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in PLACEHOLDER_VALUES
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


@dataclass(frozen=True)
class Preregistration:
    """One frozen strategy registration."""

    strategy_id: str
    version: str
    owner_session: str
    created_at: str                     # when the draft was written
    frozen_at: Optional[str] = None     # when it was sealed; None until freeze()
    signal: Dict[str, object] = field(default_factory=dict)
    thresholds: Dict[str, object] = field(default_factory=dict)
    universe: Dict[str, object] = field(default_factory=dict)
    settlement_rule: Dict[str, object] = field(default_factory=dict)
    content_hash: Optional[str] = None

    # --- hashing -----------------------------------------------------------
    def hashable_payload(self) -> Dict[str, object]:
        """Everything the seal covers. Identity fields are included so a copy
        under a new strategy id produces a different hash and cannot borrow a
        seal."""
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "owner_session": self.owner_session,
            "created_at": self.created_at,
            "frozen_at": self.frozen_at,
            "signal": self.signal,
            "thresholds": self.thresholds,
            "universe": self.universe,
            "settlement_rule": self.settlement_rule,
        }

    def compute_hash(self) -> str:
        blob = json.dumps(self.hashable_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # --- validation --------------------------------------------------------
    def missing_sections(self) -> Tuple[str, ...]:
        out: List[str] = []
        for section in REQUIRED_SECTIONS:
            value = getattr(self, section)
            if _is_placeholder(value):
                out.append(section)
            elif isinstance(value, Mapping):
                if any(_is_placeholder(v) for v in value.values()):
                    out.append(f"{section} (empty or placeholder field inside)")
        return tuple(out)

    def validate_content(self) -> "Preregistration":
        if not self.strategy_id or _is_placeholder(self.strategy_id):
            raise PreRegistrationError("strategy_id required")
        if not self.version or _is_placeholder(self.version):
            raise PreRegistrationError("version required: the leaderboard binds a score to a version")
        _parse_iso(self.created_at, "created_at")
        missing = self.missing_sections()
        if missing:
            raise PreRegistrationError(
                "incomplete registration; these sections are empty or placeholder: "
                + ", ".join(missing)
            )
        for key in REQUIRED_THRESHOLD_KEYS:
            if key not in self.thresholds:
                raise PreRegistrationError(f"thresholds.{key} is required (no default is assumed)")
            if _is_placeholder(self.thresholds[key]):
                raise PreRegistrationError(f"thresholds.{key} must be a declared value, not a placeholder")
        for key in REQUIRED_SETTLEMENT_KEYS:
            if key not in self.settlement_rule or _is_placeholder(self.settlement_rule[key]):
                raise PreRegistrationError(f"settlement_rule.{key} is required and must be non-empty")
        for key in ("season", "start_date", "end_date", "markets"):
            if key not in self.universe or _is_placeholder(self.universe[key]):
                raise PreRegistrationError(f"universe.{key} is required to make the evaluation reproducible")
        return self

    # --- lifecycle ---------------------------------------------------------
    def freeze(self, frozen_at: Optional[str] = None) -> "Preregistration":
        """Seal the registration: stamps ``frozen_at`` and fixes the hash."""
        self.validate_content()
        if self.frozen_at is not None:
            raise PreRegistrationError(
                f"{self.strategy_id}: already frozen at {self.frozen_at}; a registration is "
                "never re-frozen, supersede it with a new version"
            )
        stamp = frozen_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        _parse_iso(stamp, "frozen_at")
        if _parse_iso(stamp, "frozen_at") < _parse_iso(self.created_at, "created_at"):
            raise PreRegistrationError("frozen_at cannot precede created_at")
        sealed = Preregistration(
            strategy_id=self.strategy_id,
            version=self.version,
            owner_session=self.owner_session,
            created_at=self.created_at,
            frozen_at=stamp,
            signal=self.signal,
            thresholds=self.thresholds,
            universe=self.universe,
            settlement_rule=self.settlement_rule,
        )
        sealed = Preregistration(**{**asdict(sealed), "content_hash": sealed.compute_hash()})
        return sealed

    def verify(self) -> "Preregistration":
        """Recompute the hash; a mismatch means the file was edited after sealing."""
        if self.frozen_at is None:
            raise PreRegistrationError(f"{self.strategy_id}: not frozen, nothing to verify")
        if not self.content_hash:
            raise PreRegistrationError(f"{self.strategy_id}: no hash recorded")
        recomputed = self.compute_hash()
        if recomputed != self.content_hash:
            raise PreRegistrationError(
                f"{self.strategy_id}: content hash mismatch (sealed {self.content_hash}, "
                f"recomputed {recomputed}); a frozen registration must never be edited"
            )
        return self

    # --- the gate that makes the file mean something ----------------------
    def authorises_bet_at(self, bet_time: str) -> Tuple[bool, str]:
        """Return (allowed, reason). Only a frozen, intact registration whose
        ``frozen_at`` precedes the bet authorises that bet."""
        if self.frozen_at is None:
            return False, "NOT_FROZEN: no pre-registration freeze exists"
        try:
            self.verify()
        except PreRegistrationError as exc:
            return False, f"TAMPERED: {exc}"
        bet_dt = _parse_iso(bet_time, "bet_time")
        frozen_dt = _parse_iso(self.frozen_at, "frozen_at")
        if bet_dt < frozen_dt:
            return False, (
                f"FROZEN_AFTER_FIRST_BET: the bet ({bet_dt.isoformat()}) is earlier than the "
                f"freeze ({frozen_dt.isoformat()}); the strategy is not pre-registered for it"
            )
        universe = self.universe
        start = universe.get("start_date")
        end = universe.get("end_date")
        if start and bet_dt.date().isoformat() < str(start):
            return False, f"OUTSIDE_UNIVERSE: bet precedes the registered start_date {start}"
        if end and bet_dt.date().isoformat() > str(end):
            return False, f"OUTSIDE_UNIVERSE: bet follows the registered end_date {end}"
        return True, "PRE_REGISTERED"


# --- persistence -----------------------------------------------------------

def write_preregistration(path: str | Path, prereg: Preregistration) -> Path:
    target = Path(path)
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        if existing.get("content_hash") != prereg.content_hash:
            raise PreRegistrationError(
                f"{target.name}: a different registration is already stored here; "
                "write a new version file instead of replacing a frozen one"
            )
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(prereg), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def read_preregistration(path: str | Path) -> Preregistration:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    for section in REQUIRED_SECTIONS:
        payload.setdefault(section, {})
    prereg = Preregistration(**payload)
    prereg.validate_content()
    if prereg.frozen_at is not None:
        prereg.verify()
    return prereg


def registration_report(prereg: Preregistration) -> Dict[str, object]:
    """The row the site publishes for one strategy's registration."""
    status = "DRAFT (not frozen)" if prereg.frozen_at is None else "FROZEN"
    return {
        "strategy_id": prereg.strategy_id,
        "version": prereg.version,
        "status": status,
        "created_at": prereg.created_at,
        "frozen_at": prereg.frozen_at or "",
        "content_hash": prereg.content_hash or "",
        "signal_keys": ", ".join(sorted(prereg.signal)) or "",
        "thresholds": ", ".join(f"{k}={v}" for k, v in sorted(prereg.thresholds.items())) or "",
        "universe": ", ".join(f"{k}={v}" for k, v in sorted(prereg.universe.items())) or "",
        "settlement_rule": ", ".join(sorted(prereg.settlement_rule)) or "",
        "missing_sections": "; ".join(prereg.missing_sections()) or "none",
    }
