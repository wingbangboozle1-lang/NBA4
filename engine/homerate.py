"""Home-court advantage: measured from the standings split, pinned, never free (task AN, gap 4).

``engine/ratings.py`` ships ``HOME_ADVANTAGE_POINTS = 0.0`` with the comment
"unfitted; must be calibrated on authorized data". This module is the calibration
path, and it is deliberately narrow:

* the *only* fitted quantity is the league home-win rate taken from the standings
  page's HOME column (``data/snapshots/standings-2026-11-15.json``: 99-88 over 187
  home games = 0.5294, with the 2 neutral-site games held out);
* that rate is converted to points through one published conversion, the normal
  approximation the repo already uses for win probability
  (``ratings.win_probability``: ``p = Phi(margin / MARGIN_SD_DEFAULT)``), inverted;
* the result is a *pin*, and :func:`for_ratings` refuses to hand the number to
  ``ratings.margin_forecast`` until the caller asserts that the run is
  pre-registered and that the rights gate cleared the inputs.

No arena, altitude, travel or attendance feature is fitted: the inputs those would
need (per-arena results, official travel notices) are not in the authorized set, so
:func:`arena_adjustment` returns a refusal rather than a coefficient.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .distributions import normal_quantile
from .inputs import MissingInput, official_link, require
from .ratings import MARGIN_SD_DEFAULT

__all__ = ["HomeWinRate", "HomeAdvantagePin", "measure_home_win_rate", "pin_home_advantage", "for_ratings", "arena_adjustment"]

NEUTRAL = "neutral"


@dataclass(frozen=True)
class HomeWinRate:
    home_wins: int
    home_losses: int
    home_games: int
    rate: float | None
    neutral_wins: int
    neutral_losses: int
    source_url: str

    @property
    def as_dict(self) -> dict[str, Any]:
        return {
            "home_wins": self.home_wins,
            "home_losses": self.home_losses,
            "home_games": self.home_games,
            "measured_home_win_rate": None if self.rate is None else round(self.rate, 4),
            "neutral_wins": self.neutral_wins,
            "neutral_losses": self.neutral_losses,
            "source_url": self.source_url,
        }


def _rec(value: str) -> tuple[int, int]:
    wins, _, losses = str(value).partition("-")
    if not losses.isdigit() or not wins.isdigit():
        return (0, 0)
    return int(wins), int(losses)


def measure_home_win_rate(rows: Sequence[dict[str, Any]], *, source_url: str = "") -> tuple[HomeWinRate, int]:
    """Sum the HOME (and NEUTRAL) split columns of a standings extraction.

    A row whose HOME cell is blank counts as zero games, and the total is reported;
    a caller that needs every team's split present checks :attr:`HomeWinRate.home_games`.
    """
    require(rows, "standings rows", needed_for="a home-win rate")
    hw = hl = nw = nl = 0
    missing = 0
    for row in rows:
        a, b = _rec(row.get("home", ""))
        if not (row.get("home") or "").strip():
            missing += 1
        hw += a
        hl += b
        a, b = _rec(row.get(NEUTRAL, ""))
        nw += a
        nl += b
    games = hw + hl
    if games == 0:
        raise MissingInput("home-win rate: the standings extraction prints no HOME split games")
    link = official_link(source_url or (rows[0].get("source_url") if rows else ""), where="home-win rate")
    return HomeWinRate(hw, hl, games, hw / games, nw, nl, link), missing


@dataclass(frozen=True)
class HomeAdvantagePin:
    rate: float
    margin_sd_points: float
    z: float
    points: float
    conversion: str
    rows_used: int
    rows_without_home_cell: int = 0
    source_url: str = ""
    authorized: bool = False
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "measured_home_win_rate": round(self.rate, 4),
            "margin_sd_points": self.margin_sd_points,
            "z": round(self.z, 4),
            "home_advantage_points": round(self.points, 3),
            "conversion": self.conversion,
            "rows_used": self.rows_used,
            "rows_without_home_cell": self.rows_without_home_cell,
            "authorized_for_ratings": self.authorized,
            "source_url": self.source_url,
            "note": self.note,
        }


def pin_home_advantage(
    rows: Sequence[dict[str, Any]],
    *,
    margin_sd: float = MARGIN_SD_DEFAULT,
    source_url: str = "",
) -> HomeAdvantagePin:
    """Convert the measured rate to a point value with the repo's own normal model.

    ``points = margin_sd * Phi^-1(rate)`` is the exact inverse of
    ``ratings.win_probability``, so the pin makes the model's neutral-home win
    probability equal the measured league rate and nothing else. It is *not* fitted
    per team, per arena or per season segment, and it does not move when a slate
    changes.
    """
    if margin_sd <= 0:
        raise MissingInput("margin_sd must be positive")
    measured, missing = measure_home_win_rate(rows, source_url=source_url)
    rate = measured.rate
    assert rate is not None
    z = normal_quantile(max(min(rate, 1 - 1e-9), 1e-9))
    return HomeAdvantagePin(
        rate=rate,
        margin_sd_points=margin_sd,
        z=z,
        points=margin_sd * z,
        conversion="points = MARGIN_SD_DEFAULT * Phi^-1(measured home-win rate); inverse of ratings.win_probability",
        rows_used=len(rows),
        rows_without_home_cell=missing,
        source_url=measured.source_url,
        authorized=False,
        note="neutral-site games held out of the rate",
    )


def load_and_pin(path: str | Path, **kw: Any) -> HomeAdvantagePin:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return pin_home_advantage(payload["rows"], source_url=payload["source_url"], **kw)


def for_ratings(
    pin: HomeAdvantagePin,
    *,
    pre_registered: bool,
    rights_cleared: bool,
    input_source_url: str = "",
) -> float:
    """The value to pass as ``ratings.margin_forecast(home_advantage=...)``.

    Both flags must be asserted True by the caller (the runbook passes them from
    ``engine/prereg.py`` and ``engine/contracts.require_allowed_use``). Anything else
    raises, and ``ratings`` keeps its 0.0 default.
    """
    if not pre_registered:
        raise MissingInput(
            f"home advantage {pin.points:.3f} pts not applied: this run is not pre-registered "
            "(engine/prereg.py); an unregistered calibration cannot enter a model line"
        )
    if not rights_cleared:
        raise MissingInput(
            "home advantage not applied: rights gate G0 has not cleared the standings input for model use "
            "(NBA Terms of Use §1/§9); engine/contracts.require_allowed_use must pass first"
        )
    official_link(pin.source_url or input_source_url, where="home-advantage pin")
    return round(pin.points, 4)


def arena_adjustment(arena: str, *, per_arena_records: Sequence[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Refusal by design: no per-arena/altitude feature is fitted.

    Fitting one needs per-arena results and a licence to use them; neither is in the
    authorized input set, so the honest output is a refusal with the reason.
    """
    require(arena, "arena", needed_for="any arena-level adjustment")
    if not per_arena_records:
        return {
            "arena": arena,
            "adjustment_points": None,
            "status": "REFUSED",
            "reason": "no per-arena split in the authorized inputs; an arena coefficient would be invented",
        }
    raise MissingInput(
        "arena adjustment: per-arena records were supplied but no authorized licence covers arena-level "
        "modelling; refusing to fit"
    )
