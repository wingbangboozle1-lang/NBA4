"""NBA4 reference engine.

This package is a *reference implementation* of the line-origination, validation
and leaderboard machinery described in ``docs/``. It contains no NBA data, no
market data and no team/player identifiers.

Hard rules enforced by this package:

* Every record that can influence a published output must carry provenance
  (source id, source URL, source timestamp, observed-at timestamp, version).
* Records are refused for betting use unless their licence/permission flag is
  set (``allowed_use=True``). The engine never infers permission.
* No model parameter has a default. A caller must supply parameters that were
  estimated from an authorised dataset; the engine refuses to invent them.
* Nothing here talks to the network. Adapters for licensed feeds live outside
  this package and are responsible for populating the contracts.
"""

from __future__ import annotations

__all__ = [
    "contracts",
    "distributions",
    "lineorigination",
    "parlay",
    "correlation",
    "validation",
    "leaderboard",
    "pipeline",
    "sources",
]

__version__ = "0.1.0"
