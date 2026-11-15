"""Tamper-evident sealing of published picks.

The brief requires a tamper-evident ledger: **hash each published pick,
publish the hash before tip, and verify after settlement**.

This module provides the mechanism:

* :func:`canonical_hash` produces the SHA-256 of a record in a canonical
  form (sorted keys, no incidental whitespace), so the same record always
  produces the same hash;
* :func:`seal_record` wraps a record in a chain entry that carries the
  record's own hash *and* the hash of the previous entry, so removing or
  editing an earlier entry breaks every later hash;
* :func:`verify_chain` re-computes the chain and reports exactly which
  entry first fails;
* :func:`verify_published_hash` checks a hash that was published before tip
  against the record that was later settled.

The published hash must exist **before** the tip time.  A hash that is
published after the game tipped is not evidence of anything, so that is
reported as a failure.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "GENESIS_HASH",
    "SealEntry",
    "canonical_json",
    "canonical_hash",
    "seal_record",
    "verify_chain",
    "verify_published_hash",
]

GENESIS_HASH = "0" * 64
"""The previous-hash value of the first entry in a chain."""


@dataclass
class SealEntry:
    """One sealed, published pick."""

    index: int
    record_id: str
    sealed_at: str
    payload_hash: str
    previous_hash: str
    chain_hash: str
    payload: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "record_id": self.record_id,
            "sealed_at": self.sealed_at,
            "payload_hash": self.payload_hash,
            "previous_hash": self.previous_hash,
            "chain_hash": self.chain_hash,
            "payload": self.payload,
        }


def canonical_json(payload: Any) -> str:
    """The canonical JSON form used for hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def canonical_hash(payload: Any) -> str:
    """SHA-256 of the canonical JSON form of ``payload``."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def seal_record(
    payload: Dict[str, Any],
    record_id: str,
    sealed_at: Optional[datetime] = None,
    previous_hash: str = GENESIS_HASH,
    index: int = 0,
) -> SealEntry:
    """Seal one published record into the chain."""
    when = (sealed_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    payload_hash = canonical_hash(payload)
    chain_hash = canonical_hash(
        {
            "previous_hash": previous_hash,
            "payload_hash": payload_hash,
            "record_id": record_id,
            "sealed_at": when,
            "index": index,
        }
    )
    return SealEntry(
        index=index,
        record_id=record_id,
        sealed_at=when,
        payload_hash=payload_hash,
        previous_hash=previous_hash,
        chain_hash=chain_hash,
        payload=payload,
    )


def verify_chain(entries: Sequence[Any]) -> Tuple[bool, Tuple[str, ...]]:
    """Re-compute a sealed chain and report the first break, if any.

    Accepts :class:`SealEntry` objects or the plain dictionaries produced by
    :meth:`SealEntry.as_dict`.
    """
    problems: List[str] = []
    previous = GENESIS_HASH
    for i, entry in enumerate(entries):
        if isinstance(entry, SealEntry):
            index, record_id = entry.index, entry.record_id
            sealed_at, payload_hash = entry.sealed_at, entry.payload_hash
            prev_hash, chain_hash = entry.previous_hash, entry.chain_hash
            payload = entry.payload
        else:
            index = entry.get("index", i)
            record_id = entry.get("record_id", "")
            sealed_at = entry.get("sealed_at", "")
            payload_hash = entry.get("payload_hash", "")
            prev_hash = entry.get("previous_hash", "")
            chain_hash = entry.get("chain_hash", "")
            payload = entry.get("payload", {})
        if index != i:
            problems.append(f"entry {i}: index {index} is out of sequence")
        if prev_hash != previous:
            problems.append(
                f"entry {i} ({record_id}): previous_hash does not match the "
                "previous entry's chain_hash"
            )
        recomputed_payload = canonical_hash(payload)
        if recomputed_payload != payload_hash:
            problems.append(
                f"entry {i} ({record_id}): payload hash does not match the "
                "record content"
            )
        recomputed_chain = canonical_hash(
            {
                "previous_hash": prev_hash,
                "payload_hash": payload_hash,
                "record_id": record_id,
                "sealed_at": sealed_at,
                "index": index,
            }
        )
        if recomputed_chain != chain_hash:
            problems.append(f"entry {i} ({record_id}): chain hash does not verify")
        previous = chain_hash
    return (not problems), tuple(problems)


def verify_published_hash(
    published_hash: Optional[str],
    payload: Dict[str, Any],
    published_at: Optional[datetime] = None,
    tip_time: Optional[datetime] = None,
) -> Tuple[bool, Tuple[str, ...]]:
    """Check a hash that was published before the tip against the record.

    Returns ``(ok, reasons)``.  The hash must exist, must match the
    payload, and - when both times are supplied - must have been published
    before the game tipped.
    """
    reasons: List[str] = []
    if not published_hash:
        reasons.append("no hash was published for this pick")
        return False, tuple(reasons)
    if not isinstance(published_hash, str) or len(published_hash) != 64:
        reasons.append("the published hash is not a 64-character SHA-256 digest")
        return False, tuple(reasons)
    recomputed = canonical_hash(payload)
    if recomputed != published_hash:
        reasons.append("the published hash does not match the settled record")
        return False, tuple(reasons)
    if published_at is not None and tip_time is not None:
        pub = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
        tip = tip_time if tip_time.tzinfo else tip_time.replace(tzinfo=timezone.utc)
        if pub >= tip:
            reasons.append(
                "the hash was published at or after the tip time, so it cannot "
                "evidence what was published before the game"
            )
            return False, tuple(reasons)
    return True, tuple(reasons)
