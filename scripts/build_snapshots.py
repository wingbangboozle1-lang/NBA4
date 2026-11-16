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

TEAM_ABBR = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM", "Miami Heat": "MIA", "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NOP", "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX", "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR", "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
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
    # is shown as "at" only when it is independently corroborated: the schedule's own
    # printed "at" token (rows 260+), the 09:15 AM injury report's AWAY@HOME code for
    # the same game date, or the nba.com games-page slug ('away-vs-home'). Matching a
    # code alone is not enough: matchups repeat across dates (POR@MIN plays 11/16 and
    # 11/17), which would falsely corroborate the wrong row; (date, code) is the key.
    report_codes = {
        (g.get("game_date") or g.get("game_date_from_schedule", ""), g["matchup"])
        for g in load("injuries-2026-11-16-0915am.json")["games"]
    }
    # Rotation availability per game: counts of rows whose printed status cell is
    # exactly "Out", per team, from the same dated report. Arithmetic on printed
    # cells only; NOT YET SUBMITTED rows are excluded because that is a reporting
    # state, not a status.
    availability: dict[str, str] = {}
    for g in load("injuries-2026-11-16-0915am.json")["games"]:
        per_team: dict[str, int] = {}
        for r in g["rows"]:
            if r.get("status") == "Out" and r.get("team") and r["team"] != "__lost__":
                per_team[r["team"]] = per_team.get(r["team"], 0) + 1
        lost = sum(1 for r in g["rows"] if r.get("team") == "__lost__")
        parts = [f"{TEAM_ABBR.get(t, t)} {n} Out" for t, n in per_team.items()]
        if lost:
            parts.append(f"{lost} rows team cell lost")
        availability[g["game_date"] + g["matchup"]] = "; ".join(parts) if parts else "0 rows printing Out"
    rows: list[str] = []
    for game in data["games"]:
        away, home = game["away"], game["home"]
        code = f"{ABBR[away]}@{ABBR[home]}"
        corroborated = (
            (game["date"], code) in report_codes
            or game.get("at_token_printed_in_schedule")
            or game.get("code_source", "").find("games page") >= 0
        )
        if corroborated:
            matchup = f"{ABBR[away]} @ {ABBR[home]}"
            game_cell = f"<strong>{e(away)}</strong> at <strong>{e(home)}</strong>"
        else:
            matchup = f"{ABBR[away]} / {ABBR[home]} (order unverified)"
            game_cell = (
                f"<strong>{e(away)}</strong> / <strong>{e(home)}</strong>"
                '<br><span class="muted">Printed order only: this schedule row prints no "at" '
                "and no independent source confirms it. Flagged unverified.</span>"
            )
        tips = f'{game["tip_et_col1"]} / {game["tip_et_col2"]}'
        tips_extra = ""
        if game.get("games_page_tip_et") and game.get("tip_disagreement"):
            tips_extra = f'<br><span class="muted">games page: {e(game["games_page_tip_et"])}</span>'
        note = game.get("tip_disagreement") or game.get("note", "")
        reason_html = "<br>".join(e(r.split(":")[0]) for r in NO_PICK_REASONS)
        reason_titles = " · ".join(e(r) for r in NO_PICK_REASONS)
        sources = [
            link(SCHEDULE_URL, "Schedule PDF row " + str(game["row"])),
            link(game["games_page_url"], "Games page " + game["games_page_game_id"]),
            link(REPORT_URL, "Availability: " + REPORT_LABEL),
        ]
        rows.append(
            "              <tr>"
            f'<td>{e(game["weekday"])} {e(game["date"])}</td>'
            f"<td>{e(tips)}{tips_extra}</td>"
            f"<td>{game_cell}"
            + (f'<br><span class="muted">{e(note)}</span>' if note else "")
            + "</td>"
            f"<td>{e(matchup)}</td>"
            f'<td>{e(availability.get(game["date"] + game.get("code", ""), "no report rows"))}</td>'
            + empty()  # originated line
            + empty()  # fair probability
            + '<td><span class="flag flag-red">NO PICK</span></td>'
            + f'<td title="{reason_titles}">{reason_html}</td>'
            + f"<td>{'<br>'.join(sources)}</td>"
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
        '<th scope="col">Rotation availability (09:15 AM report)</th>'
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
    data = load("injuries-2026-11-16-0915am.json")
    rows: list[str] = []
    for game in data["games"]:
        from_schedule = game["cells_source"].startswith("schedule")
        context_cells = game["cells_source"] == "report-context"
        for row in game["rows"]:
            team = row["team"]
            player = row["player"]
            status = row["status"]
            reason = row["reason"]
            notes: list[str] = []
            sources = [link(REPORT_URL, REPORT_LABEL)]
            if from_schedule or context_cells:
                notes.append(
                    "game date/time from page-break block context; schedule PDF row cited as corroboration"
                )
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

INJ_0615 = "injuries-2026-11-16-0915am.cells.json"
INJ_DIFF = "injuries-2026-11-16-0900-to-0915.diff.json"
RESULTS_1114 = "results-2026-11-15.json"
STANDINGS_1115 = "standings-2026-11-16.json"
AGGREGATES_1115 = "aggregates-2026-11-16.json"
TEAM_STATS_1116 = "team-stats-2026-11-16.json"


def _row(cells: list[str]) -> str:
    return "              <tr>" + "".join(cells) + "</tr>"


def render_injuries_diff() -> str:
    data = load(INJ_DIFF)
    old_label = data["old"]["revision_label"]
    new_label = data["new"]["revision_label"]
    rows: list[str] = []
    for change in data["changes"]:
        old_val = change.get("old") or change.get("old_status", "")
        new_val = change.get("new") or change.get("new_status", "")
        cells = [
            f"<td>{e(change['kind'])}</td>",
            f'<td>{e(str(change.get("matchup", change.get("key", ""))))}</td>',
            f"<td>{e(str(change.get('player', '')))}</td>" if change.get("player") else empty(),
            f"<td>{e(str(old_val))}</td>" if old_val else empty(),
            f"<td>{e(str(new_val))}</td>" if new_val else empty(),
            f'<td>{e(change["note"])}</td>' if change.get("note") else empty(),
            f"<td>{link(data['source_url'], new_label + ' revision')}<br>"
            f"{link(data['old']['source_url'], old_label + ' revision')}</td>",
        ]
        rows.append(_row(cells))
    counts = data["counts"]
    summary = _row(
        [
            "<td><strong>Summary</strong></td>",
            f'<td>{counts["old_rows"]} rows at {e(old_label)}, {counts["new_rows"]} at {e(new_label)}</td>',
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
        f'<th scope="col">At {e(old_label)}</th><th scope="col">At {e(new_label)}</th>'
        '<th scope="col">Data note</th>'
        '<th scope="col">Official source</th></tr></thead>\n            <tbody>\n'
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


def render_results() -> str:
    data = load(RESULTS_1114)
    rows: list[str] = []
    for row in data["rows"]:
        (gid, date, tip, arena, away, home, aq, af, hq, hf, winner, loser, url) = row
        for team, quarters, final in ((away, aq, af), (home, hq, hf)):
            if quarters:
                total = sum(quarters)
                ok = total == final
                q_cells = "".join(f"<td>{q}</td>" for q in quarters)
                sum_cell = f"<td><strong>{total}</strong></td>"
                check_cell = (
                    f'<td><span class=\"flag {"flag-green" if ok else "flag-red"}\">'
                    f'{"AGREES" if ok else "DISAGREES"}</span><br>'
                    f'{"quarter scores add to the printed final" if ok else "quarter sum does not equal the printed final"}'
                    f"</td>"
                )
                settle_cell = f'<td>{"SETTLEMENT_ELIGIBLE" if ok else "BLOCKED"}</td>'
            else:
                q_cells = empty() + empty() + empty() + empty()
                sum_cell = empty()
                check_cell = (
                    '<td><span class="flag">NOT CHECKED</span><br>'
                    "quarter scores not transcribed in this snapshot (flag P9-05); "
                    "cells left blank, never reconstructed</td>"
                )
                settle_cell = (
                    '<td><span class="flag flag-red">BLOCKED</span><br>'
                    "D-01/IR-T4 rights decision + quarter-score gap</td>"
                )
            cells = [
                f'<td>{e(gid)}</td>',
                f'<td>{e(date)} {e(tip)} ET</td>',
                f"<td>{e(team)}</td>",
                q_cells,
                sum_cell,
                f"<td><strong>{final}</strong></td>",
                check_cell,
                settle_cell,
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
    cr = data["consecutive_revision"]
    fd = data["feed_delay"]
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
            "league HOME wins / (HOME wins + HOME losses); neutral-site lines held out",
            load(STANDINGS_1115)["source_url"],
            "input to engine/homerate.py, which converts it to points and refuses to apply it before "
            "pre-registration and rights gate G0 clear",
        ),
        row(
            "Home-advantage point value",
            f'<strong>+{hc["point_value_proposed"]} pts</strong> (proposed, not applied)',
            hc["point_value_note"],
            load(STANDINGS_1115)["source_url"],
            "ratings.HOME_ADVANTAGE_POINTS stays 0.0 until the gates clear; no per-arena or altitude term is fitted",
        ),
        row(
            "Result-feed settlement",
            f'{rf["finals_recorded"]} finals recorded; quarter-sum check ran on '
            f'{rf["team_lines_checked"]} team lines ({rf["lines_where_quarter_sum_equals_printed_final"]} agree)',
            "a day settles only when every team line's four printed quarter scores add to the printed final",
            load(RESULTS_1114)["source_url"],
            "; ".join(rf["settlement_blocked_reasons"]),
        ),
        row(
            "Feed delay",
            f'<span class="flag">[NO INPUT]</span> (retrieval lag {fd["retrieval_lag_hours_after_last_printed_tip"]} h '
            "after the last printed tip)",
            "the results document prints no game-end clock; no end time is invented",
            load(RESULTS_1114)["source_url"],
            fd["note"],
        ),
        row(
            "Injury-report load, current revision",
            f'{il["rows"]} rows, {il["rows_with_a_status"]} with a status, {il["not_yet_submitted_rows"]} '
            f'NOT YET SUBMITTED, {il["unaligned_rows_after_page_breaks"]} unaligned',
            "counts of the printed rows; NOT YET SUBMITTED is a reporting state, not a player status",
            il["source_url"],
            "engine/injurystore.py",
        ),
        row(
            "Consecutive-revision change",
            e(cr["summary"]),
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


def render_team_stats() -> str:
    data = load(TEAM_STATS_1116)
    adv = {r["team"]: r for r in data["advanced_rows"]}
    opp = {r["team"]: r for r in data["opponent_rows"]}
    src = data["sources"]
    rows: list[str] = []
    for team, a in adv.items():
        o = opp[team]
        cells = [
            f"<td><strong>{e(team)}</strong></td>",
            f"<td>{a['gp']}</td>",
            f"<td>{a['w']}-{a['l']}</td>",
            f"<td>{e(a['off_rtg'])}</td>",
            f"<td>{e(a['def_rtg'])}</td>",
            f"<td>{e(a['net_rtg'])}</td>",
            f"<td>{e(a['pace'])}</td>",
            f"<td>{a['poss']}</td>",
            f"<td>{e(a['efg_pct'])}</td>",
            f"<td>{e(a['ts_pct'])}</td>",
            f"<td>{e(a['tov_pct'])}</td>",
            f"<td>{e(o['opp_fg_pct'])}</td>",
            f"<td>{e(o['opp_3p_pct'])}</td>",
            f"<td>{e(o['opp_reb'])}</td>",
            f"<td>{e(o['opp_ast'])}</td>",
            f"<td>{e(o['opp_pts'])}</td>",
            f"<td>{e(o['plus_minus'])}</td>",
            f"<td>{link(src['advanced'], 'Advanced')}<br>{link(src['opponent'], 'Opponent')}<br>"
            f"{link(src['traditional'], 'Traditional (re-read, not transcribed)')}</td>",
        ]
        rows.append(_row(cells))
    head = (
        '<div class="table-card table-wrap">\n          <table class="data-table">\n'
        "            <thead><tr>"
        '<th scope="col">Team</th><th scope="col">GP</th><th scope="col">W-L</th>'
        '<th scope="col">OffRtg</th><th scope="col">DefRtg</th><th scope="col">NetRtg</th>'
        '<th scope="col">PACE</th><th scope="col">POSS</th><th scope="col">eFG%</th>'
        '<th scope="col">TS%</th><th scope="col">TOV%</th>'
        '<th scope="col">Opp FG%</th><th scope="col">Opp 3P%</th><th scope="col">Opp REB</th>'
        '<th scope="col">Opp AST</th><th scope="col">Opp PTS</th><th scope="col">+/-</th>'
        '<th scope="col">Official sources</th>'
        "</tr></thead>\n            <tbody>\n"
    )
    return head + "\n".join(rows) + "\n            </tbody>\n          </table>\n        </div>"


BLOCKS.update(
    {
        "injuries-diff": ("injuries.html", render_injuries_diff),
        "results-lines": ("results.html", render_results),
        "standings-table": ("results.html", render_standings),
        "aggregates-table": ("results.html", render_aggregates),
        "team-stats-table": ("team-stats.html", render_team_stats),
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
