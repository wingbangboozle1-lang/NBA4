"""Official per-game results, final-score verification and settlement.

The brief requires an official per-game result feed with one row per game
(date, teams, final score, quarter scores) that is settled **only after the
final score is verified**, with the settlement stamp kept visible.

Two rules are enforced here:

1. **Verification before settlement.**  A result is settled only when at
   least two independent official observations agree on the final score and
   the game status is ``Final``.  A single observation, a non-final status or
   a disagreement between the observations leaves the result unverified and
   the settlement blocked.
2. **The settlement stamp is a fact of record.**  It carries the time the
   settlement was made, the hash of the sealed ledger entry it settles, and
   the rule that was applied, so a reader can check the settlement later.

The rights note matters here: NBA Statistics (which includes box scores and
final scores) may not be used in connection with gambling activity without
the Operator's express prior consent (NBA.com Terms of Use §9).  This module
therefore works on results that the caller has obtained lawfully; it does
not fetch them and it does not decide whether the caller may use them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "FINAL",
    "SETTLEMENT_RULES",
    "GameResult",
    "ResultVerification",
    "Settlement",
    "verify_final",
    "settle_pick",
    "settlement_stamp",
]

FINAL = "Final"

SETTLEMENT_RULES: Dict[str, str] = {
    "spread_home_covers": (
        "the home team covers when (home_points - away_points) + spread > 0; "
        "the bet pushes when the result is exactly 0"
    ),
    "total": (
        "the game total is compared with the line: the 'over' side wins when "
        "(home_points + away_points) is above the line and the 'under' side "
        "wins when it is below; the bet pushes when the total is exactly equal "
        "to the line"
    ),
    "moneyline_home": "the home team wins; there is no push on a moneyline",
    "parlay_conjunction": (
        "every leg of the parlay must win for the parlay to win; a pushed leg "
        "is removed from the parlay and the remaining legs must all win; a void "
        "leg voids the whole parlay"
    ),
    "player_points_over": (
        "the player scores more than the line; the bet pushes when the "
        "player's points equal the line"
    ),
}
"""The settlement rules this engine can apply, each stated exactly.

A strategy's pre-registration file must name one of these keys verbatim; a
rule that is not in this table is never applied.
"""


@dataclass
class GameResult:
    """One official per-game result row."""

    record_id: str
    game_id: str
    game_date: str
    home_team: str
    away_team: str
    home_points: Optional[int]
    away_points: Optional[int]
    quarter_scores: Tuple[Tuple[Optional[int], Optional[int]], ...] = ()
    status: str = FINAL
    source_url: str = ""
    source_label: str = ""
    source_time: str = ""
    observed_at: str = ""
    confirmation_urls: Tuple[str, ...] = ()

    @property
    def total_points(self) -> Optional[int]:
        if self.home_points is None or self.away_points is None:
            return None
        return int(self.home_points) + int(self.away_points)

    @property
    def margin(self) -> Optional[int]:
        if self.home_points is None or self.away_points is None:
            return None
        return int(self.home_points) - int(self.away_points)

    def quarter_summary(self) -> str:
        if not self.quarter_scores:
            return ""
        return ", ".join(
            f"Q{i + 1} {h}-{a}" for i, (h, a) in enumerate(self.quarter_scores)
        )


@dataclass
class ResultVerification:
    """Whether a final score is confirmed well enough to settle."""

    verified: bool
    reasons: Tuple[str, ...] = ()
    confirmations: Tuple[str, ...] = ()

    @property
    def status(self) -> str:
        return "VERIFIED" if self.verified else "NOT VERIFIED"


@dataclass
class Settlement:
    """The outcome of settling one market against a verified result."""

    market: str
    rule: str
    outcome: str  # "WON" | "LOST" | "PUSH" | "VOID" | "NOT SETTLED"
    stake: Optional[float] = None
    return_amount: Optional[float] = None
    settled_at: str = ""
    notes: Tuple[str, ...] = ()


def verify_final(
    result: GameResult,
    observations: Sequence[GameResult] = (),
    required_confirmations: int = 2,
) -> ResultVerification:
    """Verify a final score against independent official observations.

    A result is verified when the game status is ``Final``, the final score
    is present, and at least ``required_confirmations`` distinct official
    source URLs (the result's own plus those of the confirmations) report
    the same final score.
    """
    reasons: List[str] = []
    if result.status != FINAL:
        reasons.append(f"status is {result.status!r}, not {FINAL!r}")
    if result.home_points is None or result.away_points is None:
        reasons.append("final score is not present")
    if not result.source_url.startswith("https://"):
        reasons.append("the result has no official https source URL")

    urls: List[str] = [result.source_url] if result.source_url else []
    agreeing: List[str] = []
    for obs in observations:
        if obs.game_id != result.game_id:
            continue
        if obs.status != FINAL:
            reasons.append(
                f"confirmation {obs.source_url or obs.record_id} is not a final result"
            )
            continue
        if obs.home_points != result.home_points or obs.away_points != result.away_points:
            reasons.append(
                f"confirmation {obs.source_url or obs.record_id} reports a different "
                f"final score ({obs.home_points}-{obs.away_points})"
            )
            continue
        if not obs.source_url.startswith("https://"):
            reasons.append(
                f"confirmation {obs.record_id} has no official https source URL"
            )
            continue
        if obs.source_url not in urls:
            urls.append(obs.source_url)
            agreeing.append(obs.source_url)

    if len(urls) < required_confirmations:
        reasons.append(
            f"only {len(urls)} independent official confirmation(s); "
            f"{required_confirmations} are required before settlement"
        )

    return ResultVerification(
        verified=not reasons, reasons=tuple(reasons), confirmations=tuple(urls)
    )


def settle_pick(
    market: str,
    side: str,
    line: Optional[float],
    result: GameResult,
    rule: str,
    verification: Optional[ResultVerification] = None,
    stake: Optional[float] = None,
    settled_at: Optional[datetime] = None,
) -> Settlement:
    """Settle one market against a verified official result."""
    now = (settled_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    if rule not in SETTLEMENT_RULES:
        return Settlement(
            market, rule, "VOID", stake, None, now,
            (f"settlement rule {rule!r} is not in the registered rule table",),
        )
    if verification is not None and not verification.verified:
        return Settlement(
            market, rule, "NOT SETTLED", stake, None, now,
            tuple(verification.reasons) + ("settlement requires a verified final score",),
        )
    if verification is None:
        return Settlement(
            market, rule, "NOT SETTLED", stake, None, now,
            ("no verification record was supplied; a final score must be verified first",),
        )
    if stake is not None and stake <= 0:
        raise ValueError("stake must be positive when supplied")

    outcome: Optional[str] = None
    notes: List[str] = []
    if rule == "spread_home_covers":
        if line is None or result.margin is None:
            notes.append("line or final margin is missing")
        else:
            adjusted = result.margin + line
            if adjusted > 0:
                outcome = "WON"
            elif adjusted < 0:
                outcome = "LOST"
            else:
                outcome = "PUSH"
        if side not in ("home", "away"):
            notes.append(f"side {side!r} is not a recognised side for this rule")
    elif rule == "total":
        if line is None or result.total_points is None:
            notes.append("line or final total is missing")
        elif side not in ("over", "under"):
            notes.append(f"side {side!r} is not a recognised side for this rule")
        else:
            if side == "over":
                outcome = "WON" if result.total_points > line else (
                    "LOST" if result.total_points < line else "PUSH"
                )
            else:
                outcome = "WON" if result.total_points < line else (
                    "LOST" if result.total_points > line else "PUSH"
                )
    elif rule == "moneyline_home":
        if result.margin is None:
            notes.append("final margin is missing")
        else:
            if side == "home":
                outcome = "WON" if result.margin > 0 else "LOST"
            elif side == "away":
                outcome = "WON" if result.margin < 0 else "LOST"
            else:
                notes.append(f"side {side!r} is not a recognised side for this rule")
    elif rule == "player_points_over":
        if line is None:
            notes.append("line is missing")
        notes.append(
            "player points are not part of the per-game result row; settle this "
            "market from the official player game log instead"
        )
    if outcome is None:
        return Settlement(market, rule, "VOID", stake, None, now, tuple(notes))

    ret: Optional[float] = None
    if stake is not None:
        ret = stake if outcome == "WON" else (stake if outcome == "PUSH" else 0.0)
    return Settlement(market, rule, outcome, stake, ret, now, tuple(notes))


def settlement_stamp(
    result: GameResult,
    verification: ResultVerification,
    settled_at: Optional[datetime] = None,
    ledger_hash: Optional[str] = None,
) -> str:
    """The visible settlement stamp for one game.

    Format: ``<settled-at UTC> | verified=<sources> | result=<score> |
    rule=<rule> | ledger=<hash>``.  It is a plain string so it can be
    printed in a table cell without interpretation.
    """
    now = (settled_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    sources = len(verification.confirmations)
    score = (
        f"{result.home_points}-{result.away_points}"
        if result.home_points is not None and result.away_points is not None
        else "not available"
    )
    return (
        f"{now} | verified={sources} source(s) | result={score} | "
        f"status={result.status} | ledger={ledger_hash or 'none'}"
    )
