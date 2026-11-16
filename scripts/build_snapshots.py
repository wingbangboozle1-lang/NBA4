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
REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_10_00AM.pdf"
REPORT_LABEL = "2026-11-16 10:00 AM ET report"

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
    # The schedule PDF text prints no "at" token on rows 215-259, so away/home order
    # is shown as "at" only when the schedule itself prints the token (rows 260+) or
    # the 10:00 AM injury report independently prints the same AWAY@HOME code for the
    # same game date. Every other row shows printed order and is flagged. Matching
    # the code alone is not enough: matchups repeat across dates (e.g. POR@MIN
    # appears on 11/16 and again on 11/17), which would falsely corroborate rows.
    report_codes = {
        (g.get("game_date") or g.get("game_date_from_schedule", ""), g["matchup"])
        for g in load("injuries-2026-11-16-1000am.json")["games"]
    }
    rows: list[str] = []
    for game in data["games"]:
        away, home = game["away"], game["home"]
        corroborated = (
            (game["date"], f"{ABBR[away]}@{ABBR[home]}") in report_codes
            or game.get("at_token_printed")
        )
        if corroborated:
            matchup = f"{ABBR[away]} @ {ABBR[home]}"
            game_cell = f"<strong>{e(away)}</strong> at <strong>{e(home)}</strong>"
        else:
            matchup = f"{ABBR[away]} / {ABBR[home]} (order unverified)"
            game_cell = (
                f"<strong>{e(away)}</strong> / <strong>{e(home)}</strong>"
                '<br><span class="muted">Printed order only: this schedule row prints no "at" '
                "and no injury-report matchup code confirms it. Flagged unverified.</span>"
            )
        tips = f'{game["tip_et_col1"]} / {game["tip_et_col2"]}'
        note = game.get("note", "")
        reason_html = "<br>".join(e(r.split(":")[0]) for r in NO_PICK_REASONS)
        reason_titles = " · ".join(e(r) for r in NO_PICK_REASONS)
        rows.append(
            "              <tr>"
            f'<td>{e(game["weekday"])} {e(game["date"])}</td>'
            f"<td>{e(tips)}</td>"
            f"<td>{game_cell}"
            + (f'<br><span class="muted">{e(note)}</span>' if note else "")
            + "</td>"
            f"<td>{e(matchup)}</td>"
            + empty()  # originated line
            + empty()  # fair probability
            + '<td><span class="flag flag-red">NO PICK</span></td>'
            + f'<td title="{reason_titles}">{reason_html}</td>'
            + f"<td>{link(SCHEDULE_URL, 'Schedule PDF row ' + str(game['row']))}</td>"
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
    date = game.get("game_date") or game.get("game_date_from_schedule") or ""
    tip = game.get("tip_et_from_schedule") or ""
    short = date[5:].replace("-", "/") if date else ""
    return f"{e(short)} {e(tip)} ET"


def render_injuries() -> str:
    data = load("injuries-2026-11-16-1000am.json")
    rows: list[str] = []
    for game in data["games"]:
        from_schedule = game["cells_source"].startswith("schedule")
        for row in game["rows"]:
            team = row["team"]
            player = row["player"]
            status = row["status"]
            reason = row["reason"]
            notes: list[str] = []
            sources = [link(REPORT_URL, REPORT_LABEL)]
            if from_schedule:
                notes.append("game date/time repaired from the schedule PDF; both sources cited")
                sources.append(link(SCHEDULE_URL, f'Schedule PDF row {game["schedule_row"]}'))
            if row.get("unverified"):
                notes.append(row.get("flag", "unverified"))
            if team == "__lost__":
                team_cell = empty()
            else:
                team_cell = f"<td>{e(team)}</td>"
            player_cell = f"<td>{e(player)}</td>" if player else empty()
            status_cell = f"<td>{e(status)}</td>" if status else empty()
            reason_cell = f"<td>{e(reason)}</td>" if reason else empty()
            note_cell = (
                '<td><span class="flag">Unverified</span><br>' + "<br>".join(e(n) for n in notes) + "</td>"
                if notes
                else "<td>Verbatim from report</td>"
            )
            rows.append(
                "              <tr>"
                f'<td>{game_label(game)}</td>'
                f'<td>{e(game["matchup"])}</td>'
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


BLOCKS = {
    "slate": ("slate.html", render_slate),
    "injuries": ("injuries.html", render_injuries),
}


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
# Task-AN blocks: the consecutive-revision injury diff and the results /
# standings / aggregate tables on results.html. The current-window slate table
# and the newest-revision injury table are rendered by the functions above from
# main (PR #49); nothing here restates them. Every renderer reads only the dated
# snapshot file it names, so a published row can be re-derived from that file.
# ---------------------------------------------------------------------------

INJ_NEW = "injuries-2026-11-16-1000am.cells.json"
INJ_DIFF = "injuries-2026-11-16-0945-to-1000.diff.json"
RESULTS_1115 = "results-2026-11-15.json"
STANDINGS_1116 = "standings-2026-11-16.json"
AGGREGATES_1116 = "aggregates-2026-11-16.json"


def _row(cells: list[str]) -> str:
    return "              <tr>" + "".join(cells) + "</tr>"


def render_injuries_diff() -> str:
    data = load(INJ_DIFF)
    # revision labels look like "11/16/26 09:45 AM"; the table headers show the clock
    old_time = " ".join(data["old"]["revision_label"].split()[-2:])
    new_time = " ".join(data["new"]["revision_label"].split()[-2:])
    rows: list[str] = []
    for change in data["changes"]:
        cells = [
            f"<td>{e(change['kind'])}</td>",
            f'<td>{e(str(change.get("matchup", change.get("key", ""))))}</td>',
            f"<td>{e(str(change.get('player', '')))}</td>" if change.get("player") else empty(),
            f"<td>{e(str(change.get('old', '')))}</td>" if change.get("old") else empty(),
            f"<td>{e(str(change.get('new', '')))}</td>" if change.get("new") else empty(),
            f'<td>{e(change["note"])}</td>' if change.get("note") else empty(),
            f"<td>{link(data['source_url'], e(data['new']['revision_label']) + ' revision')}<br>"
            f"{link(data['old']['source_url'], e(data['old']['revision_label']) + ' revision')}</td>",
        ]
        rows.append(_row(cells))
    counts = data["counts"]
    summary = _row(
        [
            "<td><strong>Summary</strong></td>",
            f'<td>{counts["old_rows"]} rows at {e(old_time)}, {counts["new_rows"]} at {e(new_time)}</td>',
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
        f'<th scope="col">At {e(old_time)}</th><th scope="col">At {e(new_time)}</th><th scope="col">Data note</th>'
        '<th scope="col">Official source</th></tr></thead>\n            <tbody>\n'
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_results() -> str:
    data = load(RESULTS_1115)
    rows: list[str] = []
    for row in data["rows"]:
        (gid, date, tip, arena, city, away, home, aq, af, hq, hf, winner, loser, url) = row
        for team, quarters, final in ((away, aq, af), (home, hq, hf)):
            total = sum(quarters)
            ok = total == final
            # quarters holds every printed period (four quarters, plus OT when printed);
            # the single OT column shows the overtime period(s) or stays empty.
            ot = " / ".join(str(q) for q in quarters[4:]) if len(quarters) > 4 else ""
            cells = [
                f'<td>{e(gid)}</td>',
                f'<td>{e(date)} {e(tip)} ET</td>',
                f"<td>{e(team)}</td>",
                "".join(f"<td>{q}</td>" for q in quarters[:4]),
                f"<td>{ot}</td>",
                f"<td><strong>{total}</strong></td>",
                f"<td><strong>{final}</strong></td>",
                f'<td><span class="flag {"flag-green" if ok else "flag-red"}">'
                f'{"AGREES" if ok else "DISAGREES"}</span><br>'
                f'{"printed periods add to the printed final" if ok else "period sum does not equal the printed final"}'
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
        '<th scope="col">OT</th><th scope="col">Period sum</th><th scope="col">Printed final</th><th scope="col">Check</th>'
        '<th scope="col">Settlement</th><th scope="col">Official source</th></tr></thead>\n            <tbody>\n'
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_standings() -> str:
    data = load(STANDINGS_1116)
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


def _et_to_utc(date_str: str, tip_str: str):
    """Printed ET tip of a November game -> timezone-aware UTC (EST = UTC-5)."""
    from datetime import datetime, timedelta, timezone

    naive = datetime.strptime(f"{date_str} {tip_str}", "%Y-%m-%d %I:%M %p")
    return (naive + timedelta(hours=5)).replace(tzinfo=timezone.utc)


def _last_tip_and_fetch():
    from datetime import datetime

    results = load(RESULTS_1115)
    tips = [_et_to_utc(r[1], r[2]) for r in results["rows"]]
    fetched = datetime.fromisoformat(results["fetched_at_utc"].replace("Z", "+00:00"))
    return max(tips), fetched


def _feed_lag_hours() -> float:
    tip, fetched = _last_tip_and_fetch()
    return (fetched - tip).total_seconds() / 3600.0


def _feed_lag_window() -> str:
    tip, fetched = _last_tip_and_fetch()
    return f"{tip:%m/%d %H:%M} UTC tip of the last game to {fetched:%m/%d %H:%M} UTC fetch"


def render_aggregates() -> str:
    data = load(AGGREGATES_1116)
    hc = data["home_court"]
    rf = data["result_feed"]
    il = data["injury_load"]
    sc = data["standings_consistency"]
    st = load(STANDINGS_1116)["consistency_checks"]
    diff_data = load(INJ_DIFF)
    diff_counts = diff_data["counts"]
    diff_old_label = diff_data["old"]["revision_label"]
    diff_new_label = diff_data["new"]["revision_label"]

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
            load(STANDINGS_1116)["source_url"],
            "input to engine/homerate.py, which converts it to points and refuses to apply it before "
            "pre-registration and rights gate G0 clear",
        ),
        row(
            "Home-advantage point value",
            f'+{hc["pin"]["home_advantage_points"]} pts (proposed, not applied)',
            f'points = MARGIN_SD_DEFAULT x Phi^-1(rate) = {hc["pin"]["margin_sd_points"]} x '
            f'{hc["pin"]["z"]}; the exact inverse of ratings.win_probability',
            load(STANDINGS_1116)["source_url"],
            "ratings.HOME_ADVANTAGE_POINTS stays 0.0 until the gates clear; no per-arena or altitude term is fitted",
        ),
        row(
            "Result-feed settlement",
            f'{rf["lines_where_quarter_sum_equals_printed_final"]}/{rf["team_lines_checked"]} team lines agree; '
            f'{rf["lines_that_disagree"]} disagreements',
            "a day settles only when every team line's printed period scores (four quarters, plus any "
            "overtime periods) add to the printed final",
            load(RESULTS_1115)["source_url"],
            "engine/resultfeed.py settlement_gate",
        ),
        row(
            "Feed delay",
            '<span class="flag">[NO INPUT]</span>',
            "the results document prints a tip time and quarter scores but no game-end clock; no end time is invented",
            load(RESULTS_1115)["source_url"],
            f"retrieval lag after the printed tip of the last game is {_feed_lag_hours():.2f} h "
            f"({_feed_lag_window()})",
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
            f'{diff_counts["status_changes"]} status changes, '
            f'{diff_counts["printing_variances"]} name-cell variance between '
            f'{e(diff_old_label)} and {e(diff_new_label)}',
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
            load(STANDINGS_1116)["source_url"],
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


def render_rest() -> str:
    """Rest / B2B / 3-in-4 for every team in the current three-day window.

    Computed by engine/rest.py from the official schedule rows only: days rest
    is the whole-day gap to the team's previous game inside the loaded window,
    B2B is rest of exactly one day, 3-in-4 counts games in the four-date window
    ending on the game date (this game included). Coverage is stated per row:
    the window starts 2026-11-10, so a team whose prior game falls earlier is
    published as uncovered, never as rested.
    """
    sys.path.insert(0, str(ROOT))
    from engine.rest import ScheduleRow, TeamCalendar, slate_rest_table

    rest = load("rest-window-2026-11-16.json")
    rows = [
        ScheduleRow(
            game_date=r["date"],
            away_team=r["away"],
            home_team=r["home"],
            tip=r.get("tip_et", ""),
            row_ref=f'schedule PDF row {r["row"]}',
            source_url=rest["source_url"],
        )
        for r in rest["rows"]
    ]
    calendar = TeamCalendar(rows)
    slate = load("slate-2026-11-16.json")
    games = [(g["date"], g["away"], g["home"]) for g in slate["games"]]
    table = slate_rest_table(calendar, games)
    by_row = {(g["date"], g["away"], g["home"]): g for g in slate["games"]}
    out: list[str] = []
    for item in table:
        game = by_row[(item["game_date"], item["team"], item["versus"])] if (item["game_date"], item["team"], item["versus"]) in by_row else by_row[(item["game_date"], item["versus"], item["team"])]
        matchup = f'{game["away"]} at {game["home"]}'
        rest_days = item["days_rest"]
        rest_cell = "unknown" if rest_days is None else str(rest_days)
        if not item["coverage_complete"]:
            rest_cell = '<span class="flag">uncovered</span>'
        out.append(
            "<tr>"
            f"<td>{e(item['game_date'])} {e(matchup)}</td>"
            f"<td>{e(item['team'])}</td>"
            f"<td>{e(item['versus'])}</td>"
            f"<td>{rest_cell}</td>"
            f"<td>{e(item['label'])}</td>"
            f"<td>{item['games_in_last_4']}</td>"
            f"<td>{'yes' if item['back_to_back'] else 'no'}</td>"
            f"<td>{'yes' if item['three_in_four'] else 'no'}</td>"
            f'<td><a class="source-link" href="{SCHEDULE_URL}" target="_blank" rel="noopener noreferrer">schedule PDF row {game["row"]}</a></td>'
            "</tr>"
        )
    head = (
        '<div class="table-card table-wrap"><table>'
        '<caption>Team rest entering each window game, computed from official schedule dates</caption>'
        "<thead><tr>"
        '<th scope="col">Game</th><th scope="col">Team</th><th scope="col">Opponent</th>'
        '<th scope="col">Days rest</th><th scope="col">Label</th><th scope="col">Games in last 4</th>'
        '<th scope="col">B2B</th><th scope="col">3-in-4</th><th scope="col">Source</th>'
        "</tr></thead><tbody>"
    )
    return head + "\n".join(out) + "\n</tbody></table></div>"


def render_availability_summary() -> str:
    """Counts and verdicts for the current injury snapshot, read from the files."""
    hand = load("injuries-2026-11-16-1000am.json")
    cells = load("injuries-2026-11-16-1000am.cells.json")
    diff = load("injuries-2026-11-16-0945-to-1000.diff.json")
    rows = [row for game in hand["games"] for row in game["rows"]]
    nys = [row for row in rows if row["status"] == "" and row["reason"] == "NOT YET SUBMITTED"]
    lost = [row for row in rows if row["team"] == "__lost__"]
    column_loss = [
        row for row in rows
        if row.get("unverified") and row["team"] != "__lost__"
        and row["reason"] != "NOT YET SUBMITTED"
        and "team has not submitted" not in row.get("flag", "")
    ]
    disagreeing = [
        g["matchup"] for g in hand["games"] if g.get("tip_disagreement")
    ]
    counts = diff["counts"]
    facts = [
        (
            "Rows transcribed",
            f"{len(rows)} rows across {len(hand['games'])} game blocks, every cell verbatim",
            hand["source_url"],
            "official report PDF",
        ),
        (
            "Independent re-extraction",
            f'{cells["cross_check"]["rows_matching_row_for_row"]} of {len(rows)} rows match row for row; '
            "nothing one-sided",
            cells["source_url"],
            "official report PDF",
        ),
        (
            "NOT YET SUBMITTED team rows",
            f"{len(nys)} rows (blank player, status printed NOT YET SUBMITTED): "
            + ", ".join(sorted({g["matchup"] for g in hand["games"] for r in g["rows"] if r['status'] == '' and r['reason'] == 'NOT YET SUBMITTED'})),
            hand["source_url"],
            "official report PDF",
        ),
        (
            "Team cells lost at page breaks",
            f"{len(lost)} rows carry a blank team cell with an unverified flag naming the printed "
            "rows around it; no team is inferred",
            hand["source_url"],
            "official report PDF",
        ),
        (
            "Status/reason column loss (page break)",
            f"{len(column_loss)} Golden State rows lost column alignment: status kept where printed, "
            "reason left blank, never repaired",
            hand["source_url"],
            "official report PDF",
        ),
        (
            "Consecutive-revision diff",
            f'{counts["status_changes"]} status changes, {counts["reason_changes"]} reason changes, '
            f'{counts["printing_variances"]} name-cell variance between '
            f'{diff["old"]["revision_label"]} and {diff["new"]["revision_label"]}',
            diff["source_url"],
            "09:45 AM revision PDF",
        ),
        (
            "Tip-clock disagreements inside this report",
            (", ".join(disagreeing) + " — report and games page agree against the August schedule PDF; "
             "both values published, neither overwritten") if disagreeing else "none",
            SCHEDULE_URL,
            "schedule PDF",
        ),
        (
            "Rotation / minutes projection",
            '<span class="flag">[NO INPUT]</span> — no minutes model is fitted; the rotation-availability '
            "column stays empty until an authorized rotation source exists",
            "https://official.nba.com/nba-injury-report-2026-27-season/",
            "NBA injury report index",
        ),
    ]
    out: list[str] = []
    for label, value, url, link_label in facts:
        out.append(
            "<tr>"
            f"<td><strong>{e(label)}</strong></td>"
            f"<td>{value}</td>"
            f'<td><a class="source-link" href="{url}" target="_blank" rel="noopener noreferrer">{e(link_label)}</a></td>'
            "</tr>"
        )
    head = (
        '<div class="table-card table-wrap"><table>'
        '<caption>Current availability snapshot: counts, cross-checks and refusals</caption>'
        "<thead><tr>"
        '<th scope="col">Fact</th><th scope="col">Value</th><th scope="col">Source</th>'
        "</tr></thead><tbody>"
    )
    return head + "\n".join(out) + "\n</tbody></table></div>"


BLOCKS.update(
    {
        "availability-rest": ("availability.html", render_rest),
        "availability-summary": ("availability.html", render_availability_summary),
        "injuries-diff": ("injuries.html", render_injuries_diff),
        "results-lines": ("results.html", render_results),
        "standings-table": ("results.html", render_standings),
        "aggregates-table": ("results.html", render_aggregates),
    }
)


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
