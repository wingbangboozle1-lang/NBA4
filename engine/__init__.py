"""NBA4 line-origination and pick-generation engine.

This package implements the pipeline specified in docs/strategy-framework.md
and docs/validation-plan.md:

    authorized inputs ledger
        -> team ratings / totals / player props / injury scenarios
        -> originated fair lines and probability distributions
        -> validation gates (docs/validation-plan.md, G0-G12)
        -> correlation estimation for combos (game-cluster uncertainty)
        -> pick generator (<= 3-day horizon, no-pick suppression)

Integrity rules enforced in code:
  * Every input record must carry an official source URL, a source timestamp
    and an observed-at timestamp, or the ledger loader rejects it (G1).
  * No NBA value is ever invented. With an empty ledger the engine reports
    "no authorized inputs" and emits NO PICK rows - it never fills numbers.
  * Synthetic fixtures exist only under tests/ to prove mechanics and are
    labelled SYNTHETIC everywhere they appear. They are never published.

Numeric parameters in this package are engineering defaults marked
UNFITTED in docs/engine.md. They are not estimates about the NBA and must
be calibrated on authorized data before any real forecast is issued.
"""

ENGINE_VERSION = "0.1.0"
MODEL_VERSION = "nba4-hypothesis-model-0.1.0"
