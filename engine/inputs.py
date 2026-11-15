"""Shared input discipline for the brief-gap modules (task AN).

Every module added under task AN answers the same question first: *do I actually
have the official input this number requires?* If the answer is no, the module
raises :class:`MissingInput` (or returns a ``REFUSED`` result) instead of
substituting a guess. That is the engine-side form of the publication rule in
``data/snapshots/README.md`` — "a cell the source did not print is published as
not printed, never filled in" — and of the standing instruction that no NBA value
is ever invented.

The helpers here exist so the twelve modules state the rule once rather than
each inventing its own variant (see COORDINATION.md IR-T1 on duplicate modules).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "MissingInput",
    "NO_INPUT",
    "REFUSED",
    "require",
    "require_all",
    "require_min",
    "official_link",
    "InputRefusal",
]

# Rendered in tables when a value is not available; never a number.
NO_INPUT = "[NO INPUT]"
REFUSED = "REFUSED"


class MissingInput(Exception):
    """A required official input is absent.

    Raised instead of computing a value from a default, an assumption, or a
    nearby game. The message always names the missing input and the document
    that would supply it, so the refusal is actionable rather than mysterious.
    """


@dataclass(frozen=True)
class InputRefusal:
    """A refusal as a *value*, for places that must render a row, not raise.

    Carries the reason and the missing input so the page can print both; it has
    no numeric field, which is the point.
    """

    subject: str
    missing: tuple[str, ...]
    reason: str
    source_url: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": REFUSED,
            "subject": self.subject,
            "missing_input": list(self.missing),
            "reason": self.reason,
            "source_url": self.source_url,
        }

    def __str__(self) -> str:  # pragma: no cover - rendering helper
        return f"{REFUSED} {self.subject}: {self.reason} (missing: {', '.join(self.missing)})"


def require(value: Any, name: str, *, needed_for: str, source: str = "") -> Any:
    """Return ``value`` when it is present; raise :class:`MissingInput` otherwise.

    ``None``, empty strings, empty sequences and empty mappings all count as
    absent. ``0`` and ``0.0`` count as present: a printed zero is a number.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        _raise(name, needed_for, source)
    if isinstance(value, (list, tuple, set, dict, frozenset)) and len(value) == 0:
        _raise(name, needed_for, source)
    return value


def _raise(name: str, needed_for: str, source: str) -> None:
    where = f" Source that would supply it: {source}." if source else ""
    raise MissingInput(f"{name} is required to compute {needed_for}; no value invented.{where}")


def require_all(mapping: Mapping[str, Any], keys: Iterable[str], *, needed_for: str, source: str = "") -> dict:
    out = {}
    for key in keys:
        out[key] = require(mapping.get(key), key, needed_for=needed_for, source=source)
    return out


def require_min(rows: Sequence[Any], n: int, *, needed_for: str, source: str = "") -> Sequence[Any]:
    """Refuse a statistic whose sample is smaller than ``n`` observations."""
    if len(rows) < n:
        raise MissingInput(
            f"{needed_for} needs at least {n} observations; {len(rows)} are available, so the statistic "
            f"is not computed.{f' Source: {source}.' if source else ''}"
        )
    return rows


def official_link(url: Any, *, where: str) -> str:
    """Guard the checker's requirement that every published row cites an https official page.

    ``scripts/check_site.py`` requires an ``https://`` link to an official host in
    the last cell of every data row; a row built without one must not be rendered
    at all, because a number with no citable source is exactly what the rights
    gate and the snapshot rules forbid.
    """
    require(url, "source_url", needed_for=f"the {where} row")
    if not str(url).startswith("https://"):
        raise MissingInput(f"{where}: source_url must be an https:// official URL, got {url!r}")
    return str(url)
