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
* A computation whose required official input is missing raises
  ``engine.inputs.MissingInput`` or returns a refusal record instead of using a
  stand-in default. Refusal-by-default modules are listed in ``docs/engine.md``.
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
    # task AN: brief-gap modules. Each one refuses to emit a number whose
    # official input is absent (see engine.inputs.MissingInput).
    "inputs",
    "resultfeed",
    "injurystore",
    "prereg",
    "seallayer",
    "dualestimate",
    "homerate",
    "luckscore",
    "travel",
    "minutesshare",
    "marketprior",
]

__version__ = "0.1.0"


# Version constants used by the ratings/props/injuries/gameflow/picks
# subsystem (documented in docs/engine.md). See also MODEL_VERSION.
ENGINE_VERSION = "0.1.0"
MODEL_VERSION = "nba4-hypothesis-model-0.1.0"
