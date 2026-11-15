"""Pre-registration ledger: model/code hash registered before a cycle's run.

The brief requires each model cycle's code hash to be registered *before* the
cycle runs, and requires that a registered run cannot be edited. This module is
the append-only record and the gate:

* :func:`register` writes an entry and refuses to overwrite an existing ``run_id``;
* :func:`amend` is the only way to correct a mistake, and appends a new entry that
  names the entry it supersedes (the old entry stays in the file);
* :func:`assert_covers` is what a pipeline run calls before it computes anything:
  it refuses when the running code hash has no entry with a ``registered_at``
  strictly earlier than the run's start, or when the entry was registered by a
  different commit than the one being run.

Nothing here decides whether a *pick* may be published — that stays with
``engine/contracts.require_allowed_use`` (rights gate G0, NBA Terms of Use §1 and
§9(ii)).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from .inputs import MissingInput, official_link, require

__all__ = ["Entry", "PreReg", "code_hash", "register", "amend", "assert_covers", "verify_file"]


@dataclass(frozen=True)
class Entry:
    run_id: str
    cycle: str  # e.g. "2026-11-15-am"
    code_sha256: str
    registered_at: str  # ISO-8601 with offset, when the entry was written
    inputs_commit: str = ""  # git commit of the snapshot inputs, when known
    source_url: str = ""
    supersedes: str = ""
    note: str = ""

    def validated(self) -> "Entry":
        for name in ("run_id", "cycle", "code_sha256", "registered_at"):
            require(getattr(self, name), name, needed_for=f"preregistration entry {self.run_id or '(new)'}")
        if len(self.code_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.code_sha256):
            raise MissingInput(f"{self.run_id}: code_sha256 must be 64 hex characters")
        stamp = datetime.fromisoformat(self.registered_at)
        if stamp.tzinfo is None:
            raise MissingInput(f"{self.run_id}: registered_at must carry a UTC offset")
        return self


def code_hash(paths: Iterable[Path | str]) -> str:
    """SHA-256 over the *bytes* of the given files, in the order given.

    The digest covers file contents only, so the same engine checkout hashes the
    same way regardless of mtime; the entry additionally records ``inputs_commit``
    so a reader can tie the run to a git object.
    """
    digest = hashlib.sha256()
    for path in sorted(str(p) for p in paths):
        digest.update(path.encode("utf-8"))
        digest.update(Path(path).read_bytes())
    return digest.hexdigest()


class PreReg:
    """Append-only JSONL file of registrations."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def entries(self) -> list[Entry]:
        if not self.path.exists():
            return []
        return [
            Entry(**json.loads(line))
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _append(self, entry: Entry) -> Entry:
        entry.validated()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        return entry

    def latest_for(self, run_id: str) -> Entry | None:
        found = [e for e in self.entries() if e.run_id == run_id]
        return found[-1] if found else None


def register(
    store: PreReg,
    *,
    run_id: str,
    cycle: str,
    code_sha256: str,
    inputs_commit: str = "",
    source_url: str = "",
    registered_at: str | None = None,
) -> Entry:
    """Record a registration; refuse if the run id is already registered."""
    if store.latest_for(run_id) is not None:
        raise MissingInput(
            f"{run_id}: already registered in {store.path}; a registration is never edited in place — use "
            "amend() to append a correcting entry that supersedes it"
        )
    when = registered_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return store._append(
        Entry(
            run_id=run_id,
            cycle=cycle,
            code_sha256=code_sha256,
            registered_at=when,
            inputs_commit=inputs_commit,
            source_url=official_link(source_url, where=f"prereg entry {run_id}") if source_url else "",
        )
    )


def amend(store: PreReg, *, supersedes: str, **fields: Any) -> Entry:
    """Append a correcting entry naming the run id it corrects."""
    prior = store.latest_for(supersedes)
    if prior is None:
        raise MissingInput(f"{supersedes}: nothing to amend; no registration exists for that run id")
    entry = Entry(
        run_id=fields.pop("run_id", f"{supersedes}-amended"),
        cycle=fields.pop("cycle", prior.cycle),
        code_sha256=fields.pop("code_sha256", prior.code_sha256),
        registered_at=fields.pop("registered_at", datetime.now(timezone.utc).isoformat(timespec="seconds")),
        inputs_commit=fields.pop("inputs_commit", prior.inputs_commit),
        source_url=fields.pop("source_url", prior.source_url),
        supersedes=supersedes,
        note=fields.pop("note", ""),
    )
    if fields:
        raise MissingInput(f"amend(): unknown field(s) {sorted(fields)}; registered fields are fixed")
    return store._append(entry)


def assert_covers(store: PreReg, *, run_id: str, code_sha256: str, run_started_at: str) -> Entry:
    """Gate: the run may proceed only if a matching registration predates it."""
    entry = require(store.latest_for(run_id), "registration", needed_for=f"run {run_id}")
    if entry.code_sha256 != code_sha256:
        raise MissingInput(
            f"{run_id}: running code hash {code_sha256[:12]}… does not match the registered "
            f"{entry.code_sha256[:12]}… — the cycle is not the one that was pre-registered"
        )
    started = datetime.fromisoformat(run_started_at)
    if started.tzinfo is None:
        raise MissingInput(f"{run_id}: run_started_at must carry a UTC offset")
    if datetime.fromisoformat(entry.registered_at) >= started.astimezone(timezone.utc):
        raise MissingInput(
            f"{run_id}: registered_at {entry.registered_at} is not before the run start {run_started_at}; "
            "a registration written after the fact does not pre-register anything"
        )
    return entry


def verify_file(store: PreReg) -> dict[str, Any]:
    """Integrity report for the page: entry count, supersession chain, duplicate run ids."""
    entries = store.entries()
    seen: dict[str, int] = {}
    for e in entries:
        seen[e.run_id] = seen.get(e.run_id, 0) + 1
    return {
        "path": str(store.path),
        "entries": len(entries),
        "unique_run_ids": len(seen),
        "duplicates": sorted(k for k, v in seen.items() if v > 1),
        "amendments": sum(1 for e in entries if e.supersedes),
        "cycles": sorted({e.cycle for e in entries}),
    }
