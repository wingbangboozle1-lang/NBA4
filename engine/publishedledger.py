"""Tamper-evident ledger for published picks: seal before tip, verify after.

Brief items implemented (2026-11-15):

* "Add a tamper-evident ledger: hash each published pick, publish the hash
  before tip, and verify after settlement."
* "Settle the sealed ledger from official finals as soon as each game day ends,
  and keep the settlement stamp visible."

Mechanics, and what each part actually proves:

1. **Per-pick hash.** Every published pick is canonicalised (sorted keys, no
   whitespace) and hashed with SHA-256. The published artefact is the pick hash.
2. **Append-only hash chain.** Each ledger entry carries ``prev_hash`` and its
   own ``entry_hash = sha256(prev_hash || entry payload)``. Editing, deleting or
   reordering an earlier entry breaks every later hash, which
   ``verify_chain`` detects.
3. **Seal before tip.** For a game day, the pick hashes are the leaves of a
   binary Merkle tree; the root is written as a ``SEAL`` entry whose timestamp
   must be at or before the earliest tip time of that day. ``verify_against_seal``
   proves a published pick was inside the sealed set, and an inclusion proof
   gives the path.
4. **Verify after settlement.** A ``SETTLE`` entry stores the settlement stamp,
   the official final-score observation hashes and the outcome. Settlement is
   refused unless ``engine.officialresults.verify_final`` reports two agreeing
   official observations - the ledger never settles on a single source.

This module proves *integrity and timing*, not correctness of a forecast, and
it makes no claim about external anchoring: a truly external timestamp (e.g. a
third-party transparency log or a notary) is a separate owner decision, recorded
as an open question, because this repository cannot bind its own hash to a
timestamp it does not control.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

KIND_PUBLISH = "PUBLISH"
KIND_SEAL = "SEAL"
KIND_SETTLE = "SETTLE"
GENESIS = "0" * 64


class LedgerError(ValueError):
    """Raised on a seal/settle ordering violation or a broken chain."""


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pick_hash(pick: Dict[str, object]) -> str:
    """Hash of a published pick: the artefact the seal commits to."""
    payload = {k: v for k, v in sorted(dict(pick).items()) if k not in ("ledger_meta",)}
    return sha256_hex(canonical(payload))


def _parse_iso(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise LedgerError(f"{name} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise LedgerError(f"{name} must carry a UTC offset")
    return parsed.astimezone(timezone.utc)


# --- Merkle tree -----------------------------------------------------------

def merkle_root(leaves: Sequence[str]) -> str:
    """Binary SHA-256 Merkle root; duplicate-pairing on odd levels."""
    if not leaves:
        raise LedgerError("cannot seal an empty set of picks")
    level = list(leaves)
    while len(level) > 1:
        nxt: List[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            nxt.append(sha256_hex(left + right))
        level = nxt
    return level[0]


def merkle_proof(leaves: Sequence[str], index: int) -> List[Tuple[str, str]]:
    """Path of (sibling_hash, side) pairs from leaf to root."""
    if not 0 <= index < len(leaves):
        raise LedgerError("leaf index out of range")
    level = list(leaves)
    path: List[Tuple[str, str]] = []
    pos = index
    while len(level) > 1:
        nxt: List[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            if i == pos or i + 1 == pos:
                side, sibling = ("right", right) if i == pos else ("left", left)
                path.append((sibling, side))
            nxt.append(sha256_hex(left + right))
        level = nxt
        pos = pos // 2
    return path


def verify_merkle_proof(leaf: str, proof: Sequence[Tuple[str, str]], root: str) -> bool:
    node = leaf
    for sibling, side in proof:
        node = sha256_hex(node + sibling) if side == "right" else sha256_hex(sibling + node)
    return node == root


# --- the ledger -------------------------------------------------------------

@dataclass(frozen=True)
class LedgerEntry:
    seq: int
    kind: str
    stamped_at: str
    payload: Dict[str, object]
    prev_hash: str
    entry_hash: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "seq": self.seq,
                "kind": self.kind,
                "stamped_at": self.stamped_at,
                "payload": self.payload,
                "prev_hash": self.prev_hash,
                "entry_hash": self.entry_hash,
            },
            sort_keys=True,
        )


@dataclass
class PublishedLedger:
    """Append-only JSONL ledger in ``directory`` (``ledger.jsonl`` + ``seals.json``)."""

    directory: Path
    _entries: List[LedgerEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.directory = Path(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._entries = []
        self._reload()

    # -- internals
    @property
    def path(self) -> Path:
        return self.directory / "ledger.jsonl"

    def _tail_hash(self) -> str:
        return self._entries[-1].entry_hash if self._entries else GENESIS

    def _reload(self) -> None:
        if not self.path.is_file():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            self._entries.append(
                LedgerEntry(
                    seq=raw["seq"], kind=raw["kind"], stamped_at=raw["stamped_at"],
                    payload=raw["payload"], prev_hash=raw["prev_hash"], entry_hash=raw["entry_hash"],
                )
            )

    def _append(self, kind: str, stamped_at: str, payload: Dict[str, object]) -> LedgerEntry:
        prev = self._tail_hash()
        body = {
            "seq": len(self._entries),
            "kind": kind,
            "stamped_at": stamped_at,
            "payload": payload,
            "prev_hash": prev,
        }
        entry = LedgerEntry(**body, entry_hash=sha256_hex(canonical(body)))  # type: ignore[arg-type]
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(entry.to_json() + "\n")
        self._entries.append(entry)
        return entry

    # -- public API
    @property
    def entries(self) -> Tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def publish(
        self,
        pick: Dict[str, object],
        pick_id: str,
        tip_time: str,
        published_at: str,
        source_urls: Sequence[str] = (),
    ) -> LedgerEntry:
        """Record a published pick. The hash must be published before tip."""
        if not pick_id:
            raise LedgerError("pick_id required")
        if any(e.kind == KIND_PUBLISH and e.payload.get("pick_id") == pick_id for e in self._entries):
            raise LedgerError(f"{pick_id}: already published; a published pick is never rewritten")
        for url in source_urls:
            if not str(url).startswith("https://"):
                raise LedgerError(f"{pick_id}: every published pick must cite its https source")
        published_dt, tip_dt = _parse_iso(published_at, "published_at"), _parse_iso(tip_time, "tip_time")
        if published_dt > tip_dt:
            raise LedgerError(
                f"{pick_id}: refused - the hash must be published before tip "
                f"(published {published_dt.isoformat()} > tip {tip_dt.isoformat()})"
            )
        game_date = str(dict(pick).get("game_date", ""))
        if any(e.kind == KIND_SEAL and str(e.payload.get("game_date")) == game_date for e in self._entries):
            raise LedgerError(
                f"{pick_id}: refused - the game day {game_date} is already sealed; "
                "a sealed day's pick set is closed so the pre-tip seal cannot be diluted"
            )
        return self._append(
            KIND_PUBLISH,
            published_at,
            {
                "pick_id": pick_id,
                "pick_hash": pick_hash(pick),
                "tip_time": tip_time,
                "pick": pick,
                "source_urls": list(source_urls),
            },
        )

    def seal_day(self, game_date: str, sealed_at: str) -> Dict[str, object]:
        """Publish the Merkle root of the day's pick hashes; must precede the earliest tip."""
        todays = [e for e in self._entries if e.kind == KIND_PUBLISH and str(e.payload.get(
            "pick", {}).get("game_date", "")) == game_date]
        if not todays:
            raise LedgerError(
                f"{game_date}: nothing to seal; a seal over an empty day would let picks appear later"
            )
        leaves = [str(e.payload["pick_hash"]) for e in sorted(todays, key=lambda e: str(e.payload["pick_id"]))]
        root = merkle_root(leaves)
        earliest_tip = min(_parse_iso(str(e.payload["tip_time"]), "tip_time") for e in todays)
        sealed_dt = _parse_iso(sealed_at, "sealed_at")
        if sealed_dt > earliest_tip:
            raise LedgerError(
                f"{game_date}: seal timestamp {sealed_dt.isoformat()} is after the earliest tip "
                f"{earliest_tip.isoformat()}; the hash set must be published before tip"
            )
        entry = self._append(
            KIND_SEAL,
            sealed_at,
            {
                "game_date": game_date,
                "root": root,
                "count": len(leaves),
                "earliest_tip": earliest_tip.isoformat(),
                "leaf_order": [str(e.payload["pick_id"]) for e in sorted(todays, key=lambda e: str(e.payload["pick_id"]))],
            },
        )
        seals_path = self.directory / "seals.json"
        seals = json.loads(seals_path.read_text(encoding="utf-8")) if seals_path.is_file() else {}
        seals[game_date] = {
            "root": root,
            "count": len(leaves),
            "sealed_at": sealed_at,
            "seq": entry.seq,
            "leaf_order": [str(e.payload["pick_id"]) for e in sorted(
                todays, key=lambda e: str(e.payload["pick_id"]))],
        }
        seals_path.write_text(json.dumps(seals, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"game_date": game_date, "root": root, "count": len(leaves), "sealed_at": sealed_at}

    def settle(
        self,
        pick_id: str,
        settled_at: str,
        final_observations: Sequence[Dict[str, object]],
        outcome: Dict[str, object],
        verification_verdict: Dict[str, object],
    ) -> LedgerEntry:
        """Append the settlement record for a published pick.

        ``verification_verdict`` is the output of
        ``engine.officialresults.verify_final``: settlement is refused unless it
        says the finals are verified from two agreeing official observations.
        """
        publish_entry = next(
            (e for e in self._entries if e.kind == KIND_PUBLISH and e.payload.get("pick_id") == pick_id), None
        )
        if publish_entry is None:
            raise LedgerError(f"{pick_id}: cannot settle a pick that was never published")
        if any(e.kind == KIND_SETTLE and e.payload.get("pick_id") == pick_id for e in self._entries):
            raise LedgerError(f"{pick_id}: already settled")
        if not verification_verdict.get("verified"):
            raise LedgerError(
                f"{pick_id}: settlement refused - official finals are not verified "
                f"({verification_verdict.get('code')}: {verification_verdict.get('detail')})"
            )
        tip_dt = _parse_iso(str(publish_entry.payload["tip_time"]), "tip_time")
        settled_dt = _parse_iso(settled_at, "settled_at")
        if settled_dt < tip_dt:
            raise LedgerError(f"{pick_id}: settlement stamp {settled_dt.isoformat()} precedes tip")
        if not final_observations:
            raise LedgerError(f"{pick_id}: no official final-score observation supplied")
        seals = self.directory / "seals.json"
        game_date = str(publish_entry.payload.get("pick", {}).get("game_date", ""))
        if not seals.is_file() or game_date not in json.loads(seals.read_text(encoding="utf-8")):
            raise LedgerError(f"{pick_id}: {game_date or 'this game day'} was never sealed before tip")
        seal_check = self.verify_against_seal(pick_id)
        if not seal_check.get("verified"):
            raise LedgerError(
                f"{pick_id}: settlement refused - the pick does not verify against its day's seal "
                f"({seal_check.get('code')}); a sealed ledger settles only sealed picks"
            )
        return self._append(
            KIND_SETTLE,
            settled_at,
            {
                "pick_id": pick_id,
                "settled_at": settled_at,
                "final_observations": list(final_observations),
                "outcome": outcome,
                "verification": dict(verification_verdict),
                "settled_after_tip_hours": round((settled_dt - tip_dt).total_seconds() / 3600.0, 3),
            },
        )

    # -- verification
    def verify_chain(self) -> Dict[str, object]:
        """Recompute every hash and linkage; report the first break, if any."""
        prev = GENESIS
        breaks: List[int] = []
        for i, entry in enumerate(self._entries):
            body = {
                "seq": entry.seq, "kind": entry.kind, "stamped_at": entry.stamped_at,
                "payload": entry.payload, "prev_hash": entry.prev_hash,
            }
            if entry.prev_hash != prev or sha256_hex(canonical(body)) != entry.entry_hash:
                breaks.append(entry.seq)
            prev = entry.entry_hash
        return {
            "entries": len(self._entries),
            "intact": not breaks,
            "broken_at": breaks,
            "head": self._tail_hash(),
        }

    def verify_against_seal(self, pick_id: str) -> Dict[str, object]:
        """Does a published pick sit inside its day's sealed Merkle root?"""
        publish_entry = next(
            (e for e in self._entries if e.kind == KIND_PUBLISH and e.payload.get("pick_id") == pick_id), None
        )
        if publish_entry is None:
            return {"pick_id": pick_id, "verified": False, "code": "NOT_PUBLISHED"}
        game_date = str(publish_entry.payload.get("pick", {}).get("game_date", ""))
        seals_path = self.directory / "seals.json"
        if not seals_path.is_file():
            return {"pick_id": pick_id, "verified": False, "code": "NO_SEAL_FILE"}
        seal = json.loads(seals_path.read_text(encoding="utf-8")).get(game_date)
        if not seal:
            return {"pick_id": pick_id, "verified": False, "code": "DAY_NOT_SEALED", "game_date": game_date}
        ordered = [
            e for e in self._entries
            if e.kind == KIND_PUBLISH
            and str(e.payload.get("pick", {}).get("game_date", "")) == game_date
        ]
        ordered.sort(key=lambda e: str(e.payload["pick_id"]))
        leaves = [str(e.payload["pick_hash"]) for e in ordered]
        if "leaf_order" not in seal:
            return {"pick_id": pick_id, "verified": False, "code": "SEAL_ORDER_UNRECORDED",
                    "game_date": game_date}
        if [str(e.payload["pick_id"]) for e in ordered] != list(seal["leaf_order"]):
            return {"pick_id": pick_id, "verified": False, "code": "SEAL_ORDER_MISMATCH", "game_date": game_date}
        index = next((i for i, e in enumerate(ordered) if str(e.payload["pick_id"]) == pick_id), None)
        if index is None:
            return {"pick_id": pick_id, "verified": False, "code": "NOT_IN_SEALED_SET", "game_date": game_date}
        proof = merkle_proof(leaves, index)
        ok = verify_merkle_proof(str(publish_entry.payload["pick_hash"]), proof, str(seal["root"]))
        return {
            "pick_id": pick_id,
            "verified": ok,
            "code": "MATCHES_SEAL" if ok else "HASH_MISMATCH_AFTER_SEAL",
            "game_date": game_date,
            "root": seal["root"],
            "proof_length": len(proof),
        }

    def settlement_stamps(self) -> List[Dict[str, object]]:
        """Visible settlement stamps: what the settlement table publishes."""
        out: List[Dict[str, object]] = []
        for entry in self._entries:
            if entry.kind != KIND_SETTLE:
                continue
            payload = entry.payload
            out.append(
                {
                    "pick_id": payload.get("pick_id"),
                    "settlement_stamp": payload.get("settled_at"),
                    "settled_after_tip_hours": payload.get("settled_after_tip_hours"),
                    "verification_code": (payload.get("verification") or {}).get("code"),
                    "outcome": canonical(payload.get("outcome") or {}),
                    "entry_hash": entry.entry_hash,
                }
            )
        return out

    def audit(self, now: Optional[str] = None) -> Dict[str, object]:
        """A one-call summary the automation page publishes."""
        chain = self.verify_chain()
        now_dt = _parse_iso(now, "now") if now else None
        pending: List[str] = []
        for entry in self._entries:
            if entry.kind != KIND_PUBLISH:
                continue
            pick_id = str(entry.payload["pick_id"])
            settled = any(
                e.kind == KIND_SETTLE and e.payload.get("pick_id") == pick_id for e in self._entries
            )
            if not settled and now_dt is not None:
                tip = _parse_iso(str(entry.payload["tip_time"]), "tip_time")
                if now_dt > tip:
                    pending.append(pick_id)
        return {
            "entries": chain["entries"],
            "chain_intact": chain["intact"],
            "broken_at": chain["broken_at"],
            "head": chain["head"],
            "published": sum(1 for e in self._entries if e.kind == KIND_PUBLISH),
            "sealed_days": sum(1 for e in self._entries if e.kind == KIND_SEAL),
            "settled": sum(1 for e in self._entries if e.kind == KIND_SETTLE),
            "past_tip_but_unsettled": pending,
        }
