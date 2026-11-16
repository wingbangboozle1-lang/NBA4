"""The three official team-stat pages, read complete, and the re-cut of the model inputs.

Brief item implemented (2026-11-16): "Re-read the three official team-stat
pages (traditional, opponent, advanced) and re-cut the model inputs."

The three pages this module models are the ones the project already cites:

* [Teams Traditional](https://www.nba.com/stats/teams/traditional) — the team's
  own box score per game (PTS, FGM, FGA, FTM, FTA, OREB, TOV, MIN, GP).
* [Teams Opponent](https://www.nba.com/stats/teams/opponent) — the same box
  score columns for the opposition (Opp PTS, Opp FGA, Opp FTA, Opp OREB,
  Opp TOV).
* [Teams Advanced](https://www.nba.com/stats/teams/advanced) — OffRtg, DefRtg,
  NetRtg, PACE, POSS, eFG%, TOV%, OREB%, all printed by the page itself.

Official definitions this module relies on, quoted from
[NBA Stats glossary](https://www.nba.com/stats/help/glossary):

* **PACE** — "Name: Pace. Definition: The number of possessions per 48 minutes
  for a team or player."
* **Poss** — "Name: Possessions. Definition: The number of possessions played by
  a player or team. Please note: an Offensive Rebound does not create another
  possession, it simply makes the existing possession longer."
* **PPP** — "Name: Points Per Possession. Definition: The number of points a
  player or team scores per possession."

What the module does, in order:

1. **Read-completeness gate.** Each page must arrive with all 30 rows and with
   every chunk of the document read. A page read in part is refused, not
   completed by inference. This is the mechanical form of flag AN-04 on the
   Flagged-for-Review page, where the opponent and advanced pages were published
   with only 13 of 30 rows read.
2. **Rights gate.** Every row carries :class:`~engine.contracts.Provenance`;
   :func:`recut` runs :func:`engine.contracts.require_allowed_use`, so a
   re-cut that would feed a bet surface raises instead of returning numbers.
3. **The re-cut.** Possessions come from pace, not from a scoring average::

       possessions_per_game = PACE * (minutes_per_game / 48)
       offensive_ppp        = PTS / possessions_per_game
       defensive_ppp        = Opp PTS / possessions_per_game

   ``minutes_per_game`` is the traditional page's own MIN column (it exceeds 48
   when a team has played overtime), which is what makes the pace conversion
   honest for a team whose games are longer than regulation.
4. **Cross-check against what the page prints.** The advanced page prints
   OffRtg, DefRtg, NetRtg and POSS, so the re-cut is verified against the
   publisher's own arithmetic rather than asserted. A disagreement beyond the
   declared tolerance is a flag, not a silent repair.
5. **Hand-off.** Game-level projection is *not* done here.
   :func:`matchup_inputs` returns values shaped for :mod:`engine.totals`
   (``project_total``, ``adjusted_ppp``, ``pace_weighted_mean``,
   ``pace_product_over_league``), so the possession model exists in exactly one
   place.

Nothing here fetches, and nothing here holds NBA data. Every value is supplied
by the caller from a document it read, together with that document's URL and
retrieval time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .contracts import Provenance, require_allowed_use
from . import totals

__all__ = [
    "TeamStatsError",
    "StatPage",
    "TEAMS_EXPECTED",
    "TraditionalRow",
    "OpponentRow",
    "AdvancedRow",
    "PageRead",
    "TeamInputs",
    "LeagueTable",
    "MatchupInputs",
    "recut",
    "matchup_inputs",
    "DEFAULT_RATING_TOLERANCE",
    "DEFAULT_POSSESSION_TOLERANCE_PCT",
    "page_urls",
    "row_from_dict",
]

TEAMS_EXPECTED = 30
"""One row per NBA team. A page that prints fewer rows was not read in full."""

DEFAULT_RATING_TOLERANCE = 1.0
"""Permitted gap, in rating points, between a re-cut rating and the printed rating.

Measured, not guessed: across all 30 teams on 2026-11-16 the largest gap was
0.48 rating points (Orlando's defensive rating), and the residual is largest
for teams that played overtime, because the page *counts* possessions while
this module derives them from the printed per-48-minute pace. A real modelling
error - for example dividing by a scoring average instead of possessions -
moves a rating by whole points, so a 1.0 tolerance still catches it.
"""

DEFAULT_POSSESSION_TOLERANCE_PCT = 1.0
"""Permitted gap between the re-cut season possession total and printed POSS, in percent.

Measured: the largest gap on 2026-11-16 was 3.99 possessions on 1,185 (0.34%,
Orlando). It is expressed as a percentage because the gap scales with the
season: a 4-possession drift over 1,185 possessions is a rounding difference,
while 4 possessions over 100 is not.
"""

GLOSSARY_URL = "https://www.nba.com/stats/help/glossary"

# Refusal codes, declared as constants so a caller can branch on them and so the
# `python3 -m engine.cli modules` audit lists what this module will not invent.
TEAMSTATS_INCOMPLETE_READ = "TEAMSTATS_INCOMPLETE_READ"
TEAMSTATS_NO_OVERLAP = "TEAMSTATS_NO_OVERLAP"
TEAMSTATS_MISSING_TEAM = "TEAMSTATS_MISSING_TEAM"
TEAMSTATS_PARTIAL_LEAGUE = "TEAMSTATS_PARTIAL_LEAGUE"


class TeamStatsError(ValueError):
    """Raised when the three pages cannot be re-cut as the brief requires."""


class StatPage(str, Enum):
    """The three official team-stat documents, with the URL each is read from."""

    TRADITIONAL = "traditional"
    OPPONENT = "opponent"
    ADVANCED = "advanced"

    @property
    def url(self) -> str:
        return f"https://www.nba.com/stats/teams/{self.value}"

    @property
    def label(self) -> str:
        return f"Teams {self.value.capitalize()} | Stats | NBA.com"


def page_urls() -> Dict[str, str]:
    """The three official URLs, keyed by page name."""
    return {page.value: page.url for page in StatPage}


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise TeamStatsError(f"{field_name} must be timezone aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class TraditionalRow:
    """One row of the official traditional page (the team's own box score)."""

    team: str
    games_played: int
    minutes_per_game: float
    points: float
    field_goals_made: float
    field_goal_attempts: float
    free_throw_attempts: float
    offensive_rebounds: float
    turnovers: float
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.team:
            raise TeamStatsError("traditional row requires a team")
        if self.games_played <= 0:
            raise TeamStatsError(f"{self.team}: games played must be positive")
        for name in (
            "minutes_per_game",
            "points",
            "field_goals_made",
            "field_goal_attempts",
            "free_throw_attempts",
            "offensive_rebounds",
            "turnovers",
        ):
            if getattr(self, name) < 0:
                raise TeamStatsError(f"{self.team}: {name} cannot be negative")
        if self.field_goals_made > self.field_goal_attempts:
            raise TeamStatsError(f"{self.team}: field goals made exceed attempts")


@dataclass(frozen=True)
class OpponentRow:
    """One row of the official opponent page (the opposition's box score).

    The page prints every column prefixed ``Opp``. Its final ``+/-`` column is
    the *opponent's* margin, which is the negative of the team's own margin on
    the traditional page; it is stored here as ``opponent_plus_minus`` so the
    two are never confused and never averaged together.
    """

    team: str
    games_played: int
    minutes_per_game: float
    opponent_points: float
    opponent_field_goals_made: float
    opponent_field_goal_attempts: float
    opponent_free_throw_attempts: float
    opponent_offensive_rebounds: float
    opponent_turnovers: float
    provenance: Provenance
    opponent_plus_minus: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.team:
            raise TeamStatsError("opponent row requires a team")
        if self.games_played <= 0:
            raise TeamStatsError(f"{self.team}: games played must be positive")
        for name in (
            "minutes_per_game",
            "opponent_points",
            "opponent_field_goals_made",
            "opponent_field_goal_attempts",
            "opponent_free_throw_attempts",
            "opponent_offensive_rebounds",
            "opponent_turnovers",
        ):
            if getattr(self, name) < 0:
                raise TeamStatsError(f"{self.team}: {name} cannot be negative")
        if self.opponent_field_goals_made > self.opponent_field_goal_attempts:
            raise TeamStatsError(f"{self.team}: opponent field goals made exceed attempts")


@dataclass(frozen=True)
class AdvancedRow:
    """One row of the official advanced page, as the page prints it."""

    team: str
    games_played: int
    minutes_total: float
    pace: float
    possessions_total: float
    offensive_rating: float
    defensive_rating: float
    net_rating: float
    provenance: Provenance
    effective_field_goal_pct: Optional[float] = None
    turnover_pct: Optional[float] = None
    offensive_rebound_pct: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.team:
            raise TeamStatsError("advanced row requires a team")
        if self.games_played <= 0:
            raise TeamStatsError(f"{self.team}: games played must be positive")
        if self.pace <= 0:
            raise TeamStatsError(f"{self.team}: pace must be positive")
        if self.possessions_total <= 0:
            raise TeamStatsError(f"{self.team}: printed possessions must be positive")
        if self.offensive_rating < 0 or self.defensive_rating < 0:
            raise TeamStatsError(f"{self.team}: ratings cannot be negative")


def _provenance_from_dict(payload: Mapping[str, object]) -> Provenance:
    """Build a :class:`~engine.contracts.Provenance` from a mapping.

    Every field is required: a row without a source, a source timestamp and a
    retrieval timestamp is not publishable, and this loader is the place that
    rule is enforced for the JSON files the CLI reads.
    """
    from datetime import datetime as _datetime

    def as_datetime(key: str) -> datetime:
        raw = payload.get(key)
        if not isinstance(raw, str):
            raise TeamStatsError(f"provenance requires a string {key}")
        try:
            parsed = _datetime.fromisoformat(raw)
        except ValueError as exc:
            raise TeamStatsError(f"provenance {key} is not ISO-8601: {raw!r}") from exc
        if parsed.tzinfo is None:
            raise TeamStatsError(f"provenance {key} must carry a UTC offset: {raw!r}")
        return parsed.astimezone(timezone.utc)

    return Provenance(
        source_id=str(payload["source_id"]),
        source_name=str(payload["source_name"]),
        source_url=str(payload["source_url"]),
        source_timestamp=as_datetime("source_timestamp"),
        observed_at=as_datetime("observed_at"),
        version=str(payload["version"]),
        allowed_use=bool(payload.get("allowed_use", False)),
        allowed_use_note=str(payload.get("allowed_use_note", "")),
    )


def row_from_dict(page: "StatPage | str", payload: Mapping[str, object]) -> object:
    """Build one page row from a mapping, for the JSON files the CLI reads.

    Returns the row type that belongs to the page, so a traditional row handed
    to the advanced page is rejected by :func:`recut` rather than silently
    re-interpreted.
    """
    try:
        page_enum = page if isinstance(page, StatPage) else StatPage(str(page))
    except ValueError as exc:
        raise TeamStatsError(f"unknown page {page!r}") from exc

    data = dict(payload)
    provenance_payload = data.pop("provenance", None)
    if not isinstance(provenance_payload, Mapping):
        raise TeamStatsError(f"{page_enum.value}: a row requires a provenance mapping")
    data["provenance"] = _provenance_from_dict(provenance_payload)

    builders = {
        StatPage.TRADITIONAL: TraditionalRow,
        StatPage.OPPONENT: OpponentRow,
        StatPage.ADVANCED: AdvancedRow,
    }
    builder = builders[page_enum]
    try:
        return builder(**data)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TeamStatsError(f"{page_enum.value}: row fields do not match the page: {exc}") from exc


@dataclass(frozen=True)
class PageRead:
    """One official page as it was actually retrieved, complete or not.

    ``chunks_read`` / ``chunks_total`` record how many parts of the document
    were read. The NBA team-stat pages are served in more than one chunk, which
    is exactly how the opponent and advanced pages came to be published with
    13 of 30 rows (flag AN-04): the reader stopped after the first chunk. The
    count is part of the provenance, so a partial read cannot be presented as a
    full one.
    """

    page: StatPage
    rows: Tuple[object, ...]
    source_url: str
    retrieved_at: datetime
    chunks_read: int = 1
    chunks_total: int = 1
    rows_expected: int = TEAMS_EXPECTED
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_url.startswith("https://"):
            raise TeamStatsError(f"{self.page.value}: source_url must be https")
        if self.chunks_read < 1 or self.chunks_total < 1:
            raise TeamStatsError(f"{self.page.value}: chunk counts must be positive")
        if self.chunks_read > self.chunks_total:
            raise TeamStatsError(f"{self.page.value}: read more chunks than the document has")
        _utc(self.retrieved_at, "retrieved_at")

    @property
    def rows_read(self) -> int:
        return len(self.rows)

    @property
    def chunks_complete(self) -> bool:
        return self.chunks_read >= self.chunks_total

    @property
    def complete(self) -> bool:
        """True only when every expected row and every chunk was read."""
        return self.rows_read >= self.rows_expected and self.chunks_complete

    @property
    def refusal(self) -> Optional[str]:
        why: List[str] = []
        if self.rows_read < self.rows_expected:
            why.append(f"{self.rows_read} of {self.rows_expected} rows read")
        if not self.chunks_complete:
            why.append(f"{self.chunks_read} of {self.chunks_total} chunks read")
        return "; ".join(why) if why else None


@dataclass(frozen=True)
class TeamInputs:
    """One team re-cut into possession terms, with the checks that back it."""

    team: str
    games_played: int
    minutes_per_game: float
    pace: float
    possessions_per_game: float
    offensive_ppp: float
    defensive_ppp: float
    net_ppp: float
    points_for: float
    points_against: float
    printed_offensive_rating: float
    printed_defensive_rating: float
    printed_net_rating: float
    printed_possessions_total: float
    checks: Mapping[str, Mapping[str, object]]
    sources: Tuple[str, ...]

    def as_row(self) -> Dict[str, object]:
        return {
            "team": self.team,
            "games_played": self.games_played,
            "pace": round(self.pace, 2),
            "possessions_per_game": round(self.possessions_per_game, 3),
            "offensive_ppp": round(self.offensive_ppp, 5),
            "defensive_ppp": round(self.defensive_ppp, 5),
            "net_ppp": round(self.net_ppp, 5),
            "points_for": round(self.points_for, 1),
            "points_against": round(self.points_against, 1),
            "recomputed_offensive_rating": round(self.offensive_ppp * 100.0, 1),
            "printed_offensive_rating": self.printed_offensive_rating,
            "recomputed_defensive_rating": round(self.defensive_ppp * 100.0, 1),
            "printed_defensive_rating": self.printed_defensive_rating,
            "all_checks_pass": all(bool(check["agrees"]) for check in self.checks.values()),
            "sources": list(self.sources),
        }


@dataclass(frozen=True)
class LeagueTable:
    """The re-cut league, plus the aggregates a matchup model needs."""

    teams: Tuple[TeamInputs, ...]
    league_pace: float
    league_offensive_ppp: float
    league_defensive_ppp: float
    flags: Tuple[str, ...]
    sources: Tuple[str, ...]
    retrieved_at: Tuple[str, ...]

    def by_team(self, team: str) -> Optional[TeamInputs]:
        for entry in self.teams:
            if entry.team == team:
                return entry
        return None

    def summary(self) -> Dict[str, object]:
        failing = [
            entry.team
            for entry in self.teams
            if not all(bool(check["agrees"]) for check in entry.checks.values())
        ]
        return {
            "teams": len(self.teams),
            "teams_expected": TEAMS_EXPECTED,
            "league_pace": round(self.league_pace, 3),
            "league_offensive_ppp": round(self.league_offensive_ppp, 5),
            "league_defensive_ppp": round(self.league_defensive_ppp, 5),
            "teams_failing_a_check": failing,
            "flags": list(self.flags),
            "sources": list(self.sources),
        }


@dataclass(frozen=True)
class MatchupInputs:
    """Everything :mod:`engine.totals` needs for one game, or the reason it is missing."""

    game_id: str
    home: str
    away: str
    possessions: Optional[float]
    ppp_home: Optional[float]
    ppp_away: Optional[float]
    scoring_averages: Optional[Tuple[float, float]]
    pace_rule: str
    adjustment_form: str
    status: str
    sources: Tuple[str, ...] = ()


def _join(
    traditional: Mapping[str, TraditionalRow],
    opponent: Mapping[str, OpponentRow],
    advanced: Mapping[str, AdvancedRow],
    *,
    rating_tolerance: float,
    possession_tolerance_pct: float,
) -> Tuple[Tuple[TeamInputs, ...], Tuple[str, ...]]:
    teams: List[TeamInputs] = []
    flags: List[str] = []
    for team in sorted(set(traditional) & set(opponent) & set(advanced)):
        own = traditional[team]
        opp = opponent[team]
        adv = advanced[team]
        checks: Dict[str, Mapping[str, object]] = {}

        if not (own.games_played == opp.games_played == adv.games_played):
            flags.append(
                f"{team}: games played disagree across pages "
                f"(traditional {own.games_played}, opponent {opp.games_played}, "
                f"advanced {adv.games_played}); the rows are not the same as-of state"
            )
            continue

        # The re-cut: possessions from pace, then efficiency from possessions.
        possessions_per_game = adv.pace * (own.minutes_per_game / 48.0)
        offensive_ppp = own.points / possessions_per_game
        defensive_ppp = opp.opponent_points / possessions_per_game

        def check(
            name: str,
            computed: float,
            printed: float,
            tolerance: float,
            rule: str,
        ) -> None:
            delta = computed - printed
            checks[name] = {
                "computed": round(computed, 4),
                "printed": round(printed, 4),
                "difference": round(delta, 4),
                "tolerance": tolerance,
                "agrees": abs(delta) <= tolerance,
                "rule": rule,
            }

        check(
            "offensive_rating",
            offensive_ppp * 100.0,
            adv.offensive_rating,
            rating_tolerance,
            "recomputed OffRtg = PTS / possessions x 100 vs the OffRtg the page prints",
        )
        check(
            "defensive_rating",
            defensive_ppp * 100.0,
            adv.defensive_rating,
            rating_tolerance,
            "recomputed DefRtg = Opp PTS / possessions x 100 vs the DefRtg the page prints",
        )
        check(
            "net_rating",
            (offensive_ppp - defensive_ppp) * 100.0,
            adv.net_rating,
            rating_tolerance,
            "recomputed NetRtg = (off PPP - def PPP) x 100 vs the NetRtg the page prints",
        )
        check(
            "possessions_total",
            adv.pace * (adv.minutes_total / 48.0),
            adv.possessions_total,
            max(1.0, adv.possessions_total * possession_tolerance_pct / 100.0),
            "recomputed POSS = PACE x (total minutes / 48) vs the POSS the page prints",
        )

        teams.append(
            TeamInputs(
                team=team,
                games_played=own.games_played,
                minutes_per_game=own.minutes_per_game,
                pace=adv.pace,
                possessions_per_game=possessions_per_game,
                offensive_ppp=offensive_ppp,
                defensive_ppp=defensive_ppp,
                net_ppp=offensive_ppp - defensive_ppp,
                points_for=own.points,
                points_against=opp.opponent_points,
                printed_offensive_rating=adv.offensive_rating,
                printed_defensive_rating=adv.defensive_rating,
                printed_net_rating=adv.net_rating,
                printed_possessions_total=adv.possessions_total,
                checks=checks,
                sources=(
                    StatPage.TRADITIONAL.url,
                    StatPage.OPPONENT.url,
                    StatPage.ADVANCED.url,
                ),
            )
        )

    only_in_some = sorted(
        (set(traditional) | set(opponent) | set(advanced))
        - (set(traditional) & set(opponent) & set(advanced))
    )
    if only_in_some:
        flags.append(
            "teams present on some pages but not all three: " + ", ".join(only_in_some)
        )
    return tuple(teams), tuple(flags)


def recut(
    traditional: PageRead,
    opponent: PageRead,
    advanced: PageRead,
    *,
    purpose: str = "model input / bet surface",
    rating_tolerance: float = DEFAULT_RATING_TOLERANCE,
    possession_tolerance_pct: float = DEFAULT_POSSESSION_TOLERANCE_PCT,
) -> LeagueTable:
    """Re-cut the three pages into possession terms, or refuse with a reason.

    Refuses, in this order, when: a page was not read complete (the AN-04
    rule); a page carries a row whose provenance is not cleared for
    ``purpose``; or the three pages describe different numbers of teams.

    ``rating_tolerance`` and ``possession_tolerance_pct`` only widen the
    comparison against the printed values; they never repair a value and never
    change a re-cut number. Both defaults are measured against the live pages
    (see ``docs/verification-pass-cc82e369.md`` section 4) rather than chosen
    to make a test pass.
    """
    reads = (traditional, opponent, advanced)
    expected = {
        StatPage.TRADITIONAL: TraditionalRow,
        StatPage.OPPONENT: OpponentRow,
        StatPage.ADVANCED: AdvancedRow,
    }
    for read in reads:
        if read.page not in expected:
            raise TeamStatsError(f"unknown page {read.page!r}")
        refusal = read.refusal
        if refusal:
            raise TeamStatsError(
                f"{TEAMSTATS_INCOMPLETE_READ}: {read.page.value} page refused ({refusal}); "
                "the re-cut needs all "
                f"{read.rows_expected} rows of all three pages, and no row may be inferred"
            )
        row_type = expected[read.page]
        for row in read.rows:
            if not isinstance(row, row_type):
                raise TeamStatsError(
                    f"{read.page.value}: expected {row_type.__name__} rows, got "
                    f"{type(row).__name__}"
                )

    for read in reads:
        for row in read.rows:
            require_allowed_use(row, purpose=purpose)

    def index(read: PageRead) -> Dict[str, object]:
        out: Dict[str, object] = {}
        for row in read.rows:
            team = getattr(row, "team", "")
            if not team:
                raise TeamStatsError(f"{read.page.value}: a row has no team name")
            if team in out:
                raise TeamStatsError(f"{read.page.value}: {team} appears more than once")
            out[team] = row
        return out

    teams, flags = _join(
        index(traditional),
        index(opponent),
        index(advanced),
        rating_tolerance=rating_tolerance,
        possession_tolerance_pct=possession_tolerance_pct,
    )

    if not teams:
        raise TeamStatsError(
            f"{TEAMSTATS_NO_OVERLAP}: the three pages share no team; the re-cut is refused"
        )
    declared = {read.rows_expected for read in reads}
    if len(declared) > 1:
        flags = flags + (
            "TEAMSTATS_DECLARATIONS_DISAGREE: the three pages declare different team counts "
            + ", ".join(f"{read.page.value}={read.rows_expected}" for read in reads),
        )
    expected_teams = max(declared)
    if len(teams) != expected_teams:
        flags = flags + (
            f"{TEAMSTATS_PARTIAL_LEAGUE}: {len(teams)} of {expected_teams} declared teams joined; "
            "a league average computed from a partial league is not a league average",
        )

    league_pace = sum(entry.pace for entry in teams) / len(teams)
    league_off = sum(entry.offensive_ppp for entry in teams) / len(teams)
    league_def = sum(entry.defensive_ppp for entry in teams) / len(teams)

    return LeagueTable(
        teams=teams,
        league_pace=league_pace,
        league_offensive_ppp=league_off,
        league_defensive_ppp=league_def,
        flags=flags,
        sources=tuple(page_urls().values()),
        retrieved_at=tuple(_utc(read.retrieved_at, "retrieved_at").isoformat() for read in reads),
    )


def matchup_inputs(
    table: LeagueTable,
    home: str,
    away: str,
    *,
    game_id: str = "",
    adjustment_form: str = "multiplicative",
    pace_rule: str = "pace_weighted_mean",
    pace_weights: Tuple[float, float] = (0.5, 0.5),
) -> MatchupInputs:
    """Shape one game's inputs for :func:`engine.totals.project_total`.

    The pace rule and the adjustment form are declared by the caller (they are
    unvalidated modelling choices that belong in the pre-registration file, not
    in this module). Returns a :class:`MatchupInputs` whose ``status`` explains
    the refusal when a team is missing, so the caller can publish the reason
    instead of a number.
    """
    home_row = table.by_team(home)
    away_row = table.by_team(away)
    if home_row is None or away_row is None:
        missing = [name for name, row in ((home, home_row), (away, away_row)) if row is None]
        return MatchupInputs(
            game_id=game_id,
            home=home,
            away=away,
            possessions=None,
            ppp_home=None,
            ppp_away=None,
            scoring_averages=None,
            pace_rule=pace_rule,
            adjustment_form=adjustment_form,
            status=(
                f"{TEAMSTATS_MISSING_TEAM}: "
                + ", ".join(missing)
                + " is absent from the three pages; no total is published for this game"
            ),
        )

    if pace_rule == "pace_weighted_mean":
        possessions = totals.pace_weighted_mean(home_row.pace, away_row.pace, pace_weights)
    elif pace_rule == "pace_product_over_league":
        possessions = totals.pace_product_over_league(
            home_row.pace, away_row.pace, table.league_pace
        )
    elif pace_rule == "declared-by-caller":
        raise TeamStatsError(
            "pace_rule 'declared-by-caller' requires a caller-supplied possession count; "
            "use engine.totals.project_total directly"
        )
    else:
        raise TeamStatsError(
            f"unknown pace_rule {pace_rule!r}: use 'pace_weighted_mean' or "
            "'pace_product_over_league'"
        )

    ppp_home = totals.adjusted_ppp(
        home_row.offensive_ppp,
        away_row.defensive_ppp,
        table.league_defensive_ppp,
        form=adjustment_form,
    )
    ppp_away = totals.adjusted_ppp(
        away_row.offensive_ppp,
        home_row.defensive_ppp,
        table.league_defensive_ppp,
        form=adjustment_form,
    )

    return MatchupInputs(
        game_id=game_id,
        home=home,
        away=away,
        possessions=possessions,
        ppp_home=ppp_home,
        ppp_away=ppp_away,
        # The naive baseline, published beside the pace model as the brief asks:
        # each team's own scoring average, summed. It is not the model output.
        scoring_averages=(home_row.points_for, away_row.points_for),
        pace_rule=pace_rule,
        adjustment_form=adjustment_form,
        status=(
            "OK: possessions from "
            f"{pace_rule}; efficiency adjusted {adjustment_form} against the league rate"
        ),
        sources=table.sources,
    )
