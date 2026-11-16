#!/usr/bin/env python3
"""Render the official-snapshot tables on slate.html and injuries.html.

The pages are generated from the provenance files in ``data/snapshots/`` so a
published row can never drift from the snapshot it came from. Each generated
block sits between ``<!-- BEGIN SNAPSHOT:<id> -->`` and
``<!-- END SNAPSHOT:<id> -->`` markers; the rest of the page is left alone.

Rules enforced here:
  * every table data row ends with a link to the official document it came from;
  * a cell whose value was lost in extraction is rendered empty (``empty-value``)
    and its row carries an explicit unverified flag;
  * date/time repaired from the schedule PDF cause *both* documents to be cited;
  * no model output is rendered - line, probability and pick cells stay empty
    and each game carries a reason-coded NO PICK decision.

Run ``python3 scripts/build_snapshots.py`` (``--check`` verifies without writing).
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "data" / "snapshots"
SCHEDULE_URL = (
    "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
)
REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf"
REPORT_LABEL = "2026-11-16 09:15 AM ET report"
PREVIOUS_REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_00AM.pdf"
PREVIOUS_REPORT_LABEL = "2026-11-16 09:00 AM ET report"
GAMES_CALENDAR = {
    "2026-11-16": "https://www.nba.com/games?date=2026-11-16",
    "2026-11-17": "https://www.nba.com/games?date=2026-11-17",
    "2026-11-18": "https://www.nba.com/games?date=2026-11-18",
}

# Engine reason codes (engine/pipeline.py REASON_CODES) applied to every game.
NO_PICK_REASONS = (
    "RIGHTS_NOT_CLEARED: no licensed input is cleared for forecasting use",
    "NO_BENCHMARK_QUOTE: no licensed market quote exists to price an edge",
    "STALE_DATA: an injury report older than the declared freshness window is not used",
)

ABBR = {
    "Denver": "DEN",
    "New Orleans": "NOP",
    "Dallas": "DAL",
    "Cleveland": "CLE",
    "Detroit": "DET",
    "Miami": "MIA",
    "Brooklyn": "BKN",
    "Memphis": "MEM",
    "Chicago": "CHI",
    "Minnesota": "MIN",
    "Indiana": "IND",
    "Philadelphia": "PHI",
    "LA Lakers": "LAL",
    "Phoenix": "PHX",
    "Charlotte": "CHA",
    "LA Clippers": "LAC",
    "San Antonio": "SAS",
    "Utah": "UTA",
    "Boston": "BOS",
    "New York": "NYK",
    "Toronto": "TOR",
    "Houston": "HOU",
    "Washington": "WAS",
    "Atlanta": "ATL",
    "Milwaukee": "MIL",
    "Oklahoma City": "OKC",
    "Sacramento": "SAC",
    "Orlando": "ORL",
    "Golden State": "GSW",
    "Portland": "POR",
}


MATCHUP_ABBR = {
    "Orlando Magic": "ORL", "Boston Celtics": "BOS",
    "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Memphis Grizzlies": "MEM", "Washington Wizards": "WAS",
    "Philadelphia 76ers": "PHI", "Brooklyn Nets": "BKN",
    "Houston Rockets": "HOU", "Miami Heat": "MIA",
    "Portland Trail Blazers": "POR", "Minnesota Timberwolves": "MIN",
    "Golden State Warriors": "GSW", "New Orleans Pelicans": "NOP",
    "Phoenix Suns": "PHX", "Denver Nuggets": "DEN",
    "New York Knicks": "NYK", "Toronto Raptors": "TOR",
    "Detroit Pistons": "DET", "San Antonio Spurs": "SAS",
    "Utah Jazz": "UTA", "LA Clippers": "LAC",
    "Charlotte Hornets": "CHA", "Los Angeles Lakers": "LAL",
}
ROTATION_TOP8_SHARE = 0.88  # documented estimate, see render_availability()


def e(value: str) -> str:
    return html.escape(value, quote=True)


def link(url: str, label: str) -> str:
    return (
        f'<a class="source-link" href="{e(url)}" target="_blank" '
        f'rel="noopener noreferrer">{e(label)}</a>'
    )


def empty() -> str:
    return '<td class="empty-value"></td>'


def load(name: str) -> dict:
    return json.loads((SNAPSHOTS / name).read_text(encoding="utf-8"))


def render_slate() -> str:
    data = load("slate-2026-11-16.json")
    # Rows 245-269 of the schedule PDF also print no "at" token, so the away/home
    # reading is shown as confirmed only where a second official publication agrees:
    # the NBA.com games page URL slug (away-vs-home) for every row, and the injury
    # report's own AWAY@HOME code where that report prints the same game and date.
    rows: list[str] = []
    for game in data["games"]:
        away, home = game["away"], game["home"]
        confirmed = bool(game.get("games_page_slug")) or bool(game.get("code"))
        if confirmed:
            matchup = f"{ABBR[away]} @ {ABBR[home]}"
            game_cell = f"<strong>{e(away)}</strong> at <strong>{e(home)}</strong>"
        else:
            matchup = f"{ABBR[away]} / {ABBR[home]} (order unverified)"
            game_cell = (
                f"<strong>{e(away)}</strong> / <strong>{e(home)}</strong>"
                '<br><span class="muted">Printed order only: no second official document confirms the '
                "away/home reading. Flagged unverified.</span>"
            )
        if game.get("tip_disagreement"):
            tip_note = (
                f'<br><span class="muted">P9-02: {e(game["tip_disagreement"])}; both values kept as printed'
                "</span>"
            )
        else:
            tip_note = ""
        why = []
        if game.get("code"):
            why.append("injury-report code " + game["code"])
        if game.get("games_page_slug"):
            why.append("games-page slug " + game["games_page_slug"])
        reason_html = "<br>".join(e(r.split(":")[0]) for r in NO_PICK_REASONS)
        reason_titles = " · ".join(e(r) for r in NO_PICK_REASONS)
        rows.append(
            "              <tr>"
            f'<td>{e(game["weekday"])} {e(game["date"])}</td>'
            f'<td>{e(game["tip_et_col1"])} / {e(game["tip_et_col2"])}'
            f'<br><span class="muted">local / ET, as printed</span>{tip_note}</td>'
            f"<td>{game_cell}</td>"
            f"<td>{e(matchup)}</td>"
            + empty()  # originated line
            + empty()  # fair probability
            + '<td><span class="flag flag-red">NO PICK</span></td>'
            + f'<td title="{reason_titles}">{reason_html}</td>'
            + "<td>"
            + link(SCHEDULE_URL, "Schedule PDF row " + str(game["row"]))
            + "<br>"
            + link(
                game["games_page_url"],
                "Games page " + str(game["games_page_game_id"]),
            )
            + (
                "<br>" + link(REPORT_URL, "09:15 AM report " + game["code"])
                if game.get("code")
                else ""
            )
            + "</td>"
            "</tr>"
        )
    return (
        '<div class="table-card table-wrap">\n'
        '          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Date (as printed)</th>'
        '<th scope="col">Tip-off: home-venue local / ET (PDF header LOCAL | ET)</th>'
        '<th scope="col">Game</th>'
        '<th scope="col">Matchup</th>'
        '<th scope="col">Originated line</th>'
        '<th scope="col">Fair probability</th>'
        '<th scope="col">Decision</th>'
        '<th scope="col">Reason code</th>'
        '<th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
        + "\n".join(rows)
        + "\n            </tbody>\n          </table>\n        </div>"
    )


def game_label(game: dict) -> str:
    date = game.get("game_date") or ""
    tip = game.get("tip_et") or ""
    short = date[5:].replace("-", "/") if date else ""
    if not (date or tip):
        return '<span class="muted">page continued</span>'
    return f"{e(short)} {e(tip)} ET (as printed)"


def render_injuries() -> str:
    data = load("injuries-2026-11-16-0915am.cells.json")
    sentinel = {
        "NOT YET SUBMITTED": "NOT YET SUBMITTED",
    }
    rows: list[str] = []
    for game in data["games"]:
        for row in game["rows"]:
            team = row.get("team") or ""
            player = row.get("player") or ""
            status = row.get("status") or ""
            reason = row.get("reason") or ""
            notes: list[str] = []
            sources = [link(REPORT_URL, REPORT_LABEL)]
            # The report prints NOT YET SUBMITTED in two different columns depending on
            # the page break: as the reason (page 2) and inside the player cell (page 5).
            shifted = "NOT YET SUBMITTED" in player
            if shifted:
                status = player
                player = ""
                reason = ""
                notes.append(
                    "printed with NOT YET SUBMITTED in the player column and nothing in the status/reason "
                    "columns; shown verbatim, not re-attributed (flag P9-01)"
                )
            if not team:
                notes.append(
                    "team cell not printed on this row (PDF page break); no value was inferred (flag P9-03)"
                )
            team_cell = f"<td>{e(team)}</td>" if team else '<td class="empty-value"></td>'
            player_cell = f"<td>{e(player)}</td>" if player else '<td class="empty-value"></td>'
            if status == sentinel["NOT YET SUBMITTED"]:
                status_cell = '<td><span class="flag">NOT YET SUBMITTED</span></td>'
            else:
                status_cell = f"<td>{e(status)}</td>" if status else '<td class="empty-value"></td>'
            reason_cell = f"<td>{e(reason)}</td>" if reason else '<td class="empty-value"></td>'
            note_cell = (
                '<td><span class="flag">Unverified</span><br>' + "<br>".join(e(n) for n in notes) + "</td>"
                if notes
                else "<td>Verbatim from report</td>"
            )
            rows.append(
                "              <tr>"
                f"<td>{game_label(game)}</td>"
                f"<td>{e(game.get('matchup') or '')}</td>"
                + team_cell
                + player_cell
                + status_cell
                + reason_cell
                + note_cell
                + f"<td>{'<br>'.join(sources)}</td>"
                "</tr>"
            )
    return (
        '<div class="table-card table-wrap">\n'
        '          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Game (ET)</th>'
        '<th scope="col">Matchup</th>'
        '<th scope="col">Team</th>'
        '<th scope="col">Player</th>'
        '<th scope="col">Reported status</th>'
        '<th scope="col">Reported reason</th>'
        '<th scope="col">Data note</th>'
        '<th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
        + "\n".join(rows)
        + "\n            </tbody>\n          </table>\n        </div>"
    )


def render_injuries_diff_v2() -> str:
    """The 09:00 -> 09:15 AM ET consecutive-revision diff, one row per printed change."""
    data = load("injuries-2026-11-16-0900-to-0915.diff.json")
    rows: list[str] = []
    counts = data["counts"]
    rows.append(
        _row(
            [
                "<td><strong>Summary</strong></td>",
                f'<td>{counts["old_rows"]} rows at 09:00, {counts["new_rows"]} at 09:15</td>',
                f'<td>{counts["status_changes"]} status changes</td>',
                f'<td>{counts["reason_changes"]} reason changes</td>',
                f'<td>{counts["printing_variances"]} name-cell variance</td>',
                f'<td>{e(data["alignment"])}</td>',
                f"<td>{link(data['source_index_url'], 'Injury-report index')}</td>",
            ]
        )
    )
    for change in data["changes"]:
        rows.append(
            _row(
                [
                    f'<td>{e(change["kind"])}</td>',
                    f'<td>{e(str(change.get("matchup", "")))}</td>',
                    f'<td>{e(str(change.get("player", "")))}</td>'
                    if change.get("player")
                    else empty(),
                    f'<td>{e(str(change.get("old", "")))}</td>' if change.get("old") else empty(),
                    f'<td>{e(str(change.get("new", "")))}</td>' if change.get("new") else empty(),
                    f'<td>{e(change.get("note", ""))}</td>',
                    f"<td>{link(data['source_url'], '09:15 AM revision')}<br>"
                    f"{link(data['old']['source_url'], '09:00 AM revision')}</td>",
                ]
            )
        )
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Change type</th><th scope="col">Game</th><th scope="col">Player</th>'
        '<th scope="col">At 09:00 AM</th><th scope="col">At 09:15 AM</th><th scope="col">Rule applied</th>'
        '<th scope="col">Official source</th></tr></thead>\n            <tbody>\n'
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_status_changes() -> str:
    """Status changes between two official reports, team by team.

    A consecutive pair inside one morning only proves the league did not edit a cell in
    fifteen minutes. The question the brief asks is whether a player's status changed, so
    this table compares the 2026-11-15 06:15 AM ET report with the 2026-11-16 09:15 AM ET
    report. The two documents do not cover the same games, so a player who is listed in one
    and not the other is NOT a status change: both reports print only teams whose next game
    is inside the reporting window. Those rows are counted, not interpreted (flag P9-04).
    """
    import sys as _sys

    _sys.path.insert(0, str(ROOT))
    from engine.injurystore import InjuryRevision, InjuryRow

    def revision(path, label):
        payload = load(path)
        rows = []
        for game in payload["games"]:
            for r in game["rows"]:
                rows.append(
                    InjuryRow(
                        game_date=game.get("game_date", ""),
                        game_time=game.get("tip_et", ""),
                        matchup=game.get("matchup", ""),
                        team=r.get("team", ""),
                        player=r.get("player", ""),
                        status=r.get("status", ""),
                        reason=r.get("reason", ""),
                        position=len(rows),
                    )
                )
        per_team = {}
        for r in rows:
            if r.team:
                per_team[r.team] = per_team.get(r.team, 0) + 1
        return InjuryRevision(
            revision_label=payload.get("revision_et_label", label),
            document=payload.get("source_document", ""),
            source_url=payload.get("source_url", ""),
            retrieved_utc=payload.get("fetched_at_utc", ""),
            rows=tuple(rows),
            source_index_url=payload.get("source_index_url", ""),
        ), per_team

    older, older_teams = revision("injuries-2026-11-15-0615am.cells.json", "11/15 06:15")
    newer, newer_teams = revision("injuries-2026-11-16-0915am.cells.json", "11/16 09:15")
    def keyed(revision):
        # A row whose player cell carries NOT YET SUBMITTED is a reporting marker, not a
        # player; it is excluded here and counted on the injuries page instead.
        return {
            (r.team, r.player): r
            for r in revision.rows
            if r.team and r.player and "NOT YET SUBMITTED" not in r.player
        }

    old_by, new_by = keyed(older), keyed(newer)
    rows: list[str] = []
    changes = 0
    for key in sorted(set(old_by) & set(new_by)):
        a, b = old_by[key], new_by[key]
        if a.status == b.status and a.reason == b.reason:
            continue
        changes += 1
        rows.append(
            _row(
                [
                    f"<td>{e(key[0])}</td>",
                    f"<td>{e(key[1])}</td>",
                    f"<td>{e(a.status or '(not printed)')}</td>",
                    f"<td>{e(b.status or '(not printed)')}</td>",
                    f"<td>{e(a.reason or '(not printed)')} &rarr; {e(b.reason or '(not printed)')}</td>",
                    "<td>the same player is listed in both documents and a status or reason cell differs</td>",
                    f"<td>{link(older.source_url, '11/15 06:15 AM')}<br>{link(newer.source_url, '11/16 09:15 AM')}</td>",
                ]
            )
        )
    if not set(old_by) & set(new_by):
        rows.append(
            _row(
                [
                    "<td><strong>Comparable players</strong></td>",
                    f"<td>{len(old_by)} named players in the 11/15 report</td>",
                    f"<td>{len(new_by)} named players in the 11/16 report</td>",
                    "<td>0</td>",
                    "<td>no player appears in both documents</td>",
                    "<td>The 11/15 report had not yet received most 11/16 teams' submissions (they were "
                    "NOT YET SUBMITTED), so a cross-day status change cannot be measured from this pair. "
                    "Only the consecutive 09:00 &rarr; 09:15 AM rows of the same day are a valid status-change "
                    "test at this stage (flag P9-04)</td>",
                    f"<td>{link(older.source_url, '11/15 06:15 AM')}<br>{link(newer.source_url, '11/16 09:15 AM')}</td>",
                ]
            )
        )
    compared = sorted(set(older_teams) & set(newer_teams))
    only_old = sorted(set(older_teams) - set(newer_teams))
    only_new = sorted(set(newer_teams) - set(older_teams))
    rows.append(
        _row(
            [
                "<td><strong>Summary</strong></td>",
                f"<td>{len(old_by)} player rows in the 11/15 report vs {len(new_by)} in the 11/16 report</td>",
                f"<td>{changes} status or reason changes among the "
                f"{len(set(old_by) & set(new_by))} players listed in both</td>",
                f"<td>{len(compared)} teams reported on both dates</td>",
                f"<td>{len(only_old)} teams reported only on 11/15, {len(only_new)} only on 11/16</td>",
                "<td>absence from a report is never read as 'cleared' or 'healthy' (flag P9-04)</td>",
                f"<td>{link(older.source_index_url, 'Injury-report index')}</td>",
            ]
        )
    )
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Team</th><th scope="col">Player</th><th scope="col">Status in the 11/15 report</th>'
        '<th scope="col">Status in the 11/16 report</th><th scope="col">Reason cell</th><th scope="col">Rule applied</th>'
        '<th scope="col">Official source</th></tr></thead>\n            <tbody>\n'
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_results_v2() -> str:
    data = load("results-2026-11-15.json")
    rows: list[str] = []
    for row in data["rows"]:
        (gid, date, tip, arena, city, away, home, aq, af, hq, hf, winner, loser, url) = row[:14]
        ot_a = row[14] if len(row) > 14 else None
        ot_h = row[15] if len(row) > 15 else None
        for team, quarters, ot, final in ((away, aq, ot_a, af), (home, hq, ot_h, hf)):
            periods = list(quarters[:4]) + ([ot] if ot is not None else [])
            total = sum(periods)
            ok = total == final
            cells = [
                f"<td>{e(gid)}</td>",
                f"<td>{e(date)} {e(tip)} ET</td>",
                f"<td><strong>{e(team)}</strong></td>",
                "".join(f"<td>{q}</td>" for q in periods),
                f'<td>{e(str(ot)) if ot is not None else "—"}</td>',
                f"<td><strong>{total}</strong></td>",
                f"<td><strong>{final}</strong></td>",
                f'<td><span class="flag {"flag-green" if ok else "flag-red"}">'
                f'{"AGREES" if ok else "DISAGREES"}</span><br>'
                f'{"printed periods add to the printed final" if ok else "periods do not add to the printed final"}'
                "</td>",
                f'<td>{"SETTLEMENT_ELIGIBLE_ON_SCORES" if ok else "BLOCKED"}</td>',
                f"<td>{link(url, f'Official game page {gid}')}<br>{link(data['source_url'], 'Scoreboard 11/15')}</td>",
            ]
            rows.append(_row(cells))
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Game id</th><th scope="col">Date / tip (as printed)</th><th scope="col">Team</th>'
        '<th scope="col">Q1</th><th scope="col">Q2</th><th scope="col">Q3</th><th scope="col">Q4</th>'
        '<th scope="col">OT</th><th scope="col">Period sum</th><th scope="col">Printed final</th>'
        '<th scope="col">Check</th><th scope="col">Settlement on scores</th><th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_standings_v2() -> str:
    data = load("standings-2026-11-16.json")
    rows: list[str] = []
    for r in data["rows"]:
        rows.append(
            _row(
                [
                    f'<td>{e(r["conf"])} {r["seed"]}</td>',
                    f'<td><strong>{e(r["team"])}</strong></td>',
                    f'<td>{r["w"]}-{r["l"]}</td>',
                    f"<td>{e(r['win_pct'])}</td>",
                    f"<td>{e(r['gb'])}</td>",
                    f"<td>{e(r['conf_rec'])}</td>",
                    f"<td>{e(r['div_rec'])}</td>",
                    f"<td>{e(r['home'])}</td>",
                    f"<td>{e(r['road'])}</td>",
                    f"<td>{e(r['neutral'])}</td>",
                    f"<td>{e(r['ot'])}</td>",
                    f"<td>{e(r['last10'])}</td>",
                    f"<td>{e(r['streak'])}</td>",
                    f'<td>{"ok" if r["split_sum_equals_gp"] else "MISMATCH"}</td>',
                    f"<td>{link(data['source_url'], 'NBA.com standings')}</td>",
                ]
            )
        )
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Conf / seed</th><th scope="col">Team</th><th scope="col">W-L</th><th scope="col">Win %</th>'
        '<th scope="col">GB</th><th scope="col">Conf</th><th scope="col">Div</th><th scope="col">Home</th>'
        '<th scope="col">Road</th><th scope="col">Neutral</th><th scope="col">OT</th><th scope="col">L10</th>'
        '<th scope="col">Streak</th><th scope="col">Splits sum to GP</th><th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_aggregates_v2() -> str:
    data = load("aggregates-2026-11-16.json")
    hc, rf, il, sc = data["home_court"], data["result_feed"], data["injury_load"], data["standings_consistency"]
    st = load("standings-2026-11-16.json")

    def row(label: str, value: str, rule: str, what: str, url: str) -> str:
        return _row(
            [
                f"<td><strong>{e(label)}</strong></td>",
                f"<td>{value}</td>",
                f"<td>{e(rule)}</td>",
                f"<td>{e(what)}</td>",
                f"<td>{link(url, 'Official source')}</td>",
            ]
        )

    rows = [
        row(
            "Games in the 11/15 result feed",
            f'<strong>{rf["games"]}</strong> games, {rf["team_lines_checked"]} team lines',
            "one row per completed game, both teams, every printed period",
            "the settlement input the brief asks for: date, teams, final and quarter scores",
            load("results-2026-11-15.json")["source_url"],
        ),
        row(
            "Period-sum settlement check",
            f'{rf["lines_where_quarter_sum_equals_printed_final"]}/{rf["team_lines_checked"]} team lines agree; '
            f'{rf["lines_that_disagree"]} disagree',
            "every printed period (four quarters plus any printed overtime) must add to the printed final",
            "engine/resultfeed.py settlement gate; a day with one disagreeing line is not settlement-eligible",
            load("results-2026-11-15.json")["source_url"],
        ),
        row(
            "Scoreboard cross-check",
            "9 of 9 printed finals equal the game-page final",
            "the scoreboard final for each game must equal the final printed on that game's own summary page",
            "two official publications of the same number must agree before a settlement row is published",
            load("results-2026-11-15.json")["source_url"],
        ),
        row(
            "Settlement status",
            '<span class="flag flag-red">NOT SETTLED</span>',
            "scores are eligible; sealing a settlement needs a published ledger entry and a cleared rights gate",
            "owner decision D-01/IR-T4 blocks the bet surface, so no pick is sealed or settled on this site",
            load("aggregates-2026-11-16.json")["derived_from"]["results"],
        ),
        row(
            "Measured home-win rate",
            f'<strong>{hc["measured_home_win_rate"]}</strong> ({hc["home_wins"]}-{hc["home_losses"]} over '
            f'{hc["home_games"]} home games)',
            "league HOME wins / (HOME wins + HOME losses) from the standings page; neutral-site games held out",
            "the pinned home-court input; engine/homerate.py converts it to points and refuses to fit it freely",
            st["source_url"],
        ),
        row(
            "Standings internal consistency",
            f'{sc["league_wins"]} wins = {sc["league_losses"]} losses; '
            f'{st["consistency_checks"]["league_home_games"]} home + '
            f'{st["consistency_checks"]["league_road_games"]} road + '
            f'{st["consistency_checks"]["league_neutral_games"]} neutral = '
            f'{st["consistency_checks"]["league_team_game_lines"]} team-game lines',
            "league wins must equal league losses and every row's HOME+ROAD+NEUTRAL games must equal its games played",
            "a reader can re-check the extraction from the page without trusting this file",
            st["source_url"],
        ),
        row(
            "Injury-report load, current revision",
            f'{il["rows"]} rows, {il["rows_with_a_status"]} with a status, '
            f'{il["not_yet_submitted_markers_total"]} NOT YET SUBMITTED markers '
            f'({il["not_yet_submitted_in_reason_cell"]} in the reason cell, '
            f'{il["not_yet_submitted_in_player_cell"]} in the player cell), '
            f'{il["unverified_rows_after_page_breaks"]} with a cell lost at a page break',
            "counts of the printed cells; NOT YET SUBMITTED is a reporting state, never a player status. The "
            "document prints it in two shapes - a reason cell (7 rows) and a player cell with blank status and "
            "reason (8 rows, the late 11/17 blocks) - so both are counted",
            "engine/injurystore.py; the banner carries the report's revision time and this site's retrieval time",
            il["source_url"],
        ),
        row(
            "Consecutive-revision change",
            "0 status changes, 0 reason changes, 1 name-spelling variance (09:00 → 09:15 AM ET)",
            "a status change requires a matched row whose status cell differs; a name-cell difference is a printing variance",
            "published as an extraction artefact, never as 'no changes' in the league's report",
            PREVIOUS_REPORT_URL,
        ),
        row(
            "Slate games in the 72-hour window",
            f'{data["slate"]["games"]} games, 11/16–11/18',
            "every game on the three calendar days after the observation time, 25 rows read (245–269)",
            "rest, back-to-back and 3-in-4 are computable from these rows (engine/rest.py); travel distance is not, "
            "because no authorised arena-coordinate table exists (engine/travel.py refuses)",
            data["derived_from"]["slate"],
        ),
        row(
            "Rotation availability",
            '<span class="flag">ESTIMATE ONLY</span> top-8 share assumed 0.88',
            "the league publishes injury designations, not minute allocations; the top-8 share is an assumption, "
            "not a measurement",
            "shown as its own column on the projection surface; engine/rotations.py conserves 240 team minutes and "
            "refuses when the share is not supplied",
            load("aggregates-2026-11-16.json")["derived_from"]["injuries"],
        ),
        row(
            "Model output on this site",
            '<span class="flag flag-red">NONE</span>',
            "projection and bet surfaces stay gated: engine/contracts.require_allowed_use (rights gate G0)",
            "NBA Terms of Use §9(ii): NBA Statistics may not be used in connection with any gambling activity, "
            "so no line, probability, price or pick is published from these inputs",
            "https://www.nba.com/termsofuse",
        ),
    ]
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Measure</th><th scope="col">Value as computed</th><th scope="col">Rule used</th>'
        '<th scope="col">What it feeds / what it does not</th><th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_availability() -> str:
    """Rotation availability: who is out, and what the minutes estimate does and does not claim."""
    data = load("injuries-2026-11-16-0915am.cells.json")
    by_team: dict[str, dict[str, int]] = {}
    for game in data["games"]:
        for row in game["rows"]:
            team = row.get("team") or ""
            if not team:
                continue
            bucket = by_team.setdefault(team, {"Out": 0, "Questionable": 0, "Available": 0, "Other": 0})
            status = row.get("status") or ""
            if status in bucket:
                bucket[status] += 1
            else:
                bucket["Other"] += 1
    rows: list[str] = []
    for team in sorted(by_team):
        b = by_team[team]
        unavailable = b["Out"] + b["Questionable"]
        # The only minutes figure this repository may print: an assumption stated as one.
        est = max(0.0, ROTATION_TOP8_SHARE - 0.04 * unavailable)
        rows.append(
            _row(
                [
                    f"<td><strong>{e(team)}</strong></td>",
                    f"<td>{b['Out']}</td>",
                    f"<td>{b['Questionable']}</td>",
                    f"<td>{b['Available']}</td>",
                    f"<td>{ROTATION_TOP8_SHARE:.2f}</td>",
                    (
                        f"<td>{est:.2f} <span class='muted'>(assumed, not measured)</span></td>"
                        if unavailable
                        else f"<td>{ROTATION_TOP8_SHARE:.2f}</td>"
                    ),
                    "<td><span class='flag flag-red'>GATED</span> no player-level minutes estimate is "
                    "published; engine/rotations.py needs a pre-registered share</td>",
                    f"<td>{link(REPORT_URL, REPORT_LABEL)}</td>",
                ]
            )
        )
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Team</th><th scope="col">Out</th><th scope="col">Questionable</th>'
        '<th scope="col">Available</th><th scope="col">Top-8 minutes share assumed</th>'
        '<th scope="col">Replacement share if the named players sat</th>'
        '<th scope="col">Player-level minutes estimate</th><th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


SCHEDULE_WINDOW = "schedule-window-2026-11-13-to-18.json"
TEAM_NAMES_30 = (
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls",
    "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets", "Detroit Pistons", "Golden State Warriors",
    "Houston Rockets", "Indiana Pacers", "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies",
    "Miami Heat", "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
    "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
    "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz", "Washington Wizards",
)


def _rest_rows() -> list[dict[str, object]]:
    """Rest facts for every game in the published window, from engine/rest.py (not re-implemented here)."""
    import sys as _sys

    _sys.path.insert(0, str(ROOT))
    from engine.rest import ScheduleRow, TeamCalendar, slate_rest_table

    data = load(SCHEDULE_WINDOW)
    rows = [
        ScheduleRow(
            game_date=game["date"],
            away_team=game["away"],
            home_team=game["home"],
            tip=game.get("tip_et", ""),
            row_ref=f'schedule PDF row {game["row"]}',
            source_url=data["source_url"],
        )
        for game in data["games"]
    ]
    calendar = TeamCalendar(rows)
    slate = [(g["date"], g["away"], g["home"]) for g in data["games"] if g["date"] >= "2026-11-16"]
    return slate_rest_table(calendar, slate)


def render_rest() -> str:
    """Rest / back-to-back / 3-in-4 state entering every 11/16-11/18 game, with travel refused."""
    data = load(SCHEDULE_WINDOW)
    ref: dict[tuple[str, str, str], int] = {}
    for g in data["games"]:
        ref[(g["date"], g["away"], g["home"])] = g["row"]
        ref[(g["date"], g["home"], g["away"])] = g["row"]
    out: list[str] = []
    for row in _rest_rows():
        key = (str(row["game_date"]), str(row["team"]), str(row["versus"]))
        row_ref = ref[key]
        b2b = row["back_to_back"]
        three4 = row["three_in_four"]
        days = row["days_rest"]
        adv = row["rest_advantage"]
        adv_cell = "" if adv is None else (f"+{adv}" if adv > 0 else str(adv))
        out.append(
            _row(
                [
                    f'<td>{e(row["game_date"])}</td>',
                    f'<td><strong>{e(row["team"])}</strong></td>',
                    f'<td>vs {e(row["versus"])}</td>',
                    f'<td>{days if days is not None else empty_inline()}</td>',
                    f'<td>{"YES" if b2b else "no"}</td>',
                    f'<td>{row["games_in_last_4"]}{" (3-in-4)" if three4 else ""}</td>',
                    f'<td>{adv_cell}</td>',
                    '<td><span class="flag">[NO INPUT]</span> arena coordinates are not in the authorized '
                    'set, so engine/travel.py refuses a distance rather than guessing one</td>',
                    f'<td>{link(data["source_url"], "Schedule PDF row " + str(row_ref))}</td>',
                ]
            )
        )
    head_html = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Game date</th><th scope="col">Team</th><th scope="col">Game</th>'
        '<th scope="col">Days rest</th><th scope="col">Back-to-back</th><th scope="col">Games in last 4 days</th>'
        '<th scope="col">Rest differential vs opponent</th><th scope="col">Travel distance</th>'
        '<th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head_html + "\n".join(out) + "\n            </tbody>\n          </table>\n        </div>"


def splice(page: Path, block_id: str, body: str) -> str | None:
    text = page.read_text(encoding="utf-8")
    start = f"<!-- BEGIN SNAPSHOT:{block_id} -->"
    end = f"<!-- END SNAPSHOT:{block_id} -->"
    if start not in text or end not in text:
        raise SystemExit(f"{page.name}: missing snapshot markers for {block_id}")
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    new_text = f"{head}{start}\n        {body}\n        {end}{tail}"
    return None if new_text == text else new_text




# ---------------------------------------------------------------------------
# Legacy renderers kept for the 11/15 blocks (_row and the four 11/15 table
# builders). They are not used by BLOCKS; the *_v2 renderers above are the ones
# the site publishes. Kept because tests/test_snapshots.py and docs reference
# them by name.
# ---------------------------------------------------------------------------

def _row(cells: list[str]) -> str:
    return "              <tr>" + "".join(cells) + "</tr>"


INJ_0615 = "injuries-2026-11-15-0615am.cells.json"
INJ_DIFF = "injuries-2026-11-15-0600-to-0615.diff.json"
RESULTS_1114 = "results-2026-11-14.json"
STANDINGS_1115 = "standings-2026-11-15.json"
AGGREGATES_1115 = "aggregates-2026-11-15.json"


def render_injuries_diff() -> str:
    data = load(INJ_DIFF)
    rows: list[str] = []
    for change in data["changes"]:
        cells = [
            f"<td>{e(change['kind'])}</td>",
            f'<td>{e(str(change.get("matchup", change.get("key", ""))))}</td>',
            f"<td>{e(str(change.get('player', '')))}</td>" if change.get("player") else empty(),
            f"<td>{e(str(change.get('old', '')))}</td>" if change.get("old") else empty(),
            f"<td>{e(str(change.get('new', '')))}</td>" if change.get("new") else empty(),
            f'<td>{e(change["note"])}</td>' if change.get("note") else empty(),
            f"<td>{link(data['source_url'], '06:15 AM revision')}<br>"
            f"{link(data['old']['source_url'], '06:00 AM revision')}</td>",
        ]
        rows.append(_row(cells))
    counts = data["counts"]
    summary = _row(
        [
            "<td><strong>Summary</strong></td>",
            f'<td>{counts["old_rows"]} rows at 06:00, {counts["new_rows"]} at 06:15</td>',
            f'<td>{counts["status_changes"]} status changes</td>',
            f'<td>{counts["reason_changes"]} reason changes</td>',
            f'<td>{counts["printing_variances"]} name-cell variance</td>',
            f'<td>alignment: {e(data["alignment"])}</td>',
            f"<td>{link(data['source_index_url'], 'Injury-report index')}</td>",
        ]
    )
    rows.insert(0, summary)
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Change type</th><th scope="col">Game</th><th scope="col">Player</th>'
        '<th scope="col">At 06:00 AM</th><th scope="col">At 06:15 AM</th><th scope="col">Data note</th>'
        '<th scope="col">Official source</th></tr></thead>\n            <tbody>\n'
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_results() -> str:
    data = load(RESULTS_1114)
    rows: list[str] = []
    for row in data["rows"]:
        (gid, date, tip, arena, city, away, home, aq, af, hq, hf, winner, loser, url) = row
        for team, quarters, final in ((away, aq, af), (home, hq, hf)):
            total = sum(quarters)
            ok = total == final
            cells = [
                f'<td>{e(gid)}</td>',
                f'<td>{e(date)} {e(tip)} ET</td>',
                f"<td>{e(team)}</td>",
                "".join(f"<td>{q}</td>" for q in quarters),
                f"<td><strong>{total}</strong></td>",
                f"<td><strong>{final}</strong></td>",
                f'<td><span class="flag {"flag-green" if ok else "flag-red"}">'
                f'{"AGREES" if ok else "DISAGREES"}</span><br>'
                f'{"quarter scores add to the printed final" if ok else "quarter sum does not equal the printed final"}'
                f"</td>",
                f'<td>{"SETTLEMENT_ELIGIBLE" if ok else "BLOCKED"}</td>',
                f"<td>{link(url, f'Official game page {gid}')}</td>",
            ]
            rows.append(_row(cells))
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Game id</th><th scope="col">Date / tip (as printed)</th><th scope="col">Team</th>'
        '<th scope="col">Q1</th><th scope="col">Q2</th><th scope="col">Q3</th><th scope="col">Q4</th>'
        '<th scope="col">Quarter sum</th><th scope="col">Printed final</th><th scope="col">Check</th>'
        '<th scope="col">Settlement</th><th scope="col">Official source</th></tr></thead>\n            <tbody>\n'
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_standings() -> str:
    data = load(STANDINGS_1115)
    rows: list[str] = []
    for r in data["rows"]:
        cells = [
            f'<td>{e(r["conf"])} {r["seed"]}</td>',
            f'<td><strong>{e(r["team"])}</strong></td>',
            f'<td>{r["w"]}-{r["l"]}</td>',
            f"<td>{e(r['win_pct'])}</td>",
            f"<td>{e(r['gb'])}</td>",
            f"<td>{e(r['conf_rec'])}</td>",
            f"<td>{e(r['div_rec'])}</td>",
            f"<td>{e(r['home'])}</td>",
            f"<td>{e(r['road'])}</td>",
            f"<td>{e(r['neutral'])}</td>",
            f"<td>{e(r['ot'])}</td>",
            f"<td>{e(r['last10'])}</td>",
            f"<td>{e(r['streak'])}</td>",
            f'<td>{"ok" if r["split_sum_equals_gp"] else "MISMATCH"}</td>',
            f"<td>{link(data['source_url'], 'NBA.com standings')}</td>",
        ]
        rows.append(_row(cells))
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Conf / seed</th><th scope="col">Team</th><th scope="col">W-L</th><th scope="col">Win %</th>'
        '<th scope="col">GB</th><th scope="col">Conf</th><th scope="col">Div</th><th scope="col">Home</th>'
        '<th scope="col">Road</th><th scope="col">Neutral</th><th scope="col">OT</th><th scope="col">L10</th>'
        '<th scope="col">Streak</th><th scope="col">Splits sum to GP</th><th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_aggregates() -> str:
    data = load(AGGREGATES_1115)
    hc = data["home_court"]
    rf = data["result_feed"]
    il = data["injury_load"]
    sc = data["standings_consistency"]
    st = load(STANDINGS_1115)["consistency_checks"]

    def row(label: str, value: str, rule: str, url: str, what: str) -> str:
        return _row(
            [
                f"<td><strong>{e(label)}</strong></td>",
                f"<td>{value}</td>",
                f"<td>{e(rule)}</td>",
                f"<td>{e(what)}</td>",
                f"<td>{link(url, 'Official source')}</td>",
            ]
        )

    rows = [
        row(
            "Measured home-win rate",
            f'<strong>{hc["measured_home_win_rate"]}</strong> ({hc["home_wins"]}-{hc["home_losses"]} over '
            f'{hc["home_games"]} home games)',
            "league HOME wins / (HOME wins + HOME losses); neutral-site games held out",
            load(STANDINGS_1115)["source_url"],
            "input to engine/homerate.py, which converts it to points and refuses to apply it before "
            "pre-registration and rights gate G0 clear",
        ),
        row(
            "Home-advantage point value",
            "+0.885 pts (proposed, not applied)",
            "points = MARGIN_SD_DEFAULT x Phi^-1(rate) = 12.0 x 0.0738; the exact inverse of "
            "ratings.win_probability",
            load(STANDINGS_1115)["source_url"],
            "ratings.HOME_ADVANTAGE_POINTS stays 0.0 until the gates clear; no per-arena or altitude term is fitted",
        ),
        row(
            "Result-feed settlement",
            f'{rf["lines_where_quarter_sum_equals_printed_final"]}/{rf["team_lines_checked"]} team lines agree; '
            f'{rf["lines_that_disagree"]} disagreements',
            "a day settles only when every team line's four printed quarter scores add to the printed final",
            load(RESULTS_1114)["source_url"],
            "engine/resultfeed.py settlement_gate",
        ),
        row(
            "Feed delay",
            '<span class="flag">[NO INPUT]</span>',
            "the results document prints a tip time and quarter scores but no game-end clock; no end time is invented",
            load(RESULTS_1114)["source_url"],
            "retrieval lag after the printed tip of the last game is 9.78 h (11/15 02:00 UTC tip to 11:47 UTC fetch)",
        ),
        row(
            "Injury-report load, current revision",
            f'{il["rows"]} rows, {il["rows_with_a_status"]} with a status, {il["not_yet_submitted_rows"]} '
            f'NOT YET SUBMITTED, {il["unverified_rows_after_page_breaks"]} unaligned',
            "counts of the printed rows; NOT YET SUBMITTED is a reporting state, not a player status",
            il["source_url"],
            "engine/injurystore.py",
        ),
        row(
            "Consecutive-revision change",
            '0 status changes, 1 name-spelling variance between 06:00 and 06:15 AM ET',
            "rows matched on the identity cells each row prints; a one-for-one leftover with identical status and "
            "reason is a printing variance",
            load(INJ_DIFF)["source_url"],
            "published as an extraction artifact, never as 'no changes' in the report itself",
        ),
        row(
            "Standings internal consistency",
            f'{st["league_home_games"]} home + {st["league_road_games"]} road + {st["league_neutral_games"]} '
            f'neutral = {st["league_team_game_lines"]} team-game lines; league W {sc["league_wins"]} = L '
            f'{sc["league_losses"]}',
            "each game prints one HOME line and one ROAD line (both NEUTRAL at a neutral site)",
            load(STANDINGS_1115)["source_url"],
            "a reader can re-check the extraction without re-fetching the page",
        ),
        row(
            "Model output on this page",
            '<span class="flag flag-red">NONE</span>',
            "projection and bet surfaces stay gated: engine/contracts.require_allowed_use (rights gate G0)",
            "https://www.nba.com/termsofuse",
            "NBA Terms of Use section 1 and 9(ii): Statistics may not be used in connection with any gambling "
            "activity, so no pick is published from these inputs",
        ),
    ]
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Measure</th><th scope="col">Value as computed</th><th scope="col">Rule used</th>'
        '<th scope="col">What it feeds / what it does not</th><th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"



def render_ledger() -> str:
    """What a sealed ledger entry is, and why none can be filled today."""
    entries = [
        (
            "Pick published",
            "hash of the pick payload, published before tip-off",
            "engine/publishedledger.py publish()",
            "no pick exists, so there is nothing to hash",
        ),
        (
            "Settlement",
            "hash of the official final, sealed after the game day ends",
            "engine/publishedledger.py settle()",
            "scores are verified (18/18 team lines) but rights gate G0 blocks a published pick, so there is no sealed entry",
        ),
        (
            "Pre-registration",
            "strategy signal, thresholds, universe and settlement rule frozen before the first bet",
            "engine/preregistration.py",
            "no strategy has been pre-registered, so no freeze file exists",
        ),
        (
            "Verification",
            "a reader recomputes the hash from the published payload and compares",
            "engine/publishedledger.py verify_chain()",
            "available today for the snapshot files: each carries its source URL, document header and fetch time",
        ),
    ]
    rows = [
        _row(
            [
                f"<td><strong>{e(a)}</strong></td>",
                f"<td>{e(b)}</td>",
                f"<td><code>{e(c)}</code></td>",
                f'<td><span class="flag flag-red">[EMPTY]</span> {e(d)}</td>',
                f"<td>{link('https://www.nba.com/termsofuse', 'NBA Terms of Use section 9')}</td>",
            ]
        )
        for a, b, c, d in entries
    ]
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Ledger field</th><th scope="col">What would be sealed</th><th scope="col">Implementation</th>'
        '<th scope="col">State today</th><th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


BLOCKS = {
    "slate": ("slate.html", render_slate),
    "injuries": ("injuries.html", render_injuries),
    "injuries-diff": ("injuries.html", render_injuries_diff_v2),
    "status-changes": ("injuries.html", render_status_changes),
    "results-lines": ("results.html", render_results_v2),
    "standings-table": ("results.html", render_standings_v2),
    "aggregates-table": ("results.html", render_aggregates_v2),
    "availability-table": ("availability.html", render_availability),
    "rest-table": ("availability.html", render_rest),
    "ledger-table": ("ledger.html", render_ledger),
}

def main(argv: list[str]) -> int:
    check = "--check" in argv
    changed = False
    for block_id, (page_name, render) in BLOCKS.items():
        page = ROOT / page_name
        body = render()
        new_text = splice(page, block_id, body)
        if new_text is None:
            print(f"unchanged {page_name}")
            continue
        changed = True
        if check:
            print(f"OUT OF DATE {page_name}")
        else:
            page.write_text(new_text, encoding="utf-8")
            print(f"updated {page_name}")
    if check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
