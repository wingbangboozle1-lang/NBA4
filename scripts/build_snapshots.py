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
REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-14_04_30AM.pdf"
REPORT_LABEL = "2026-11-14 04:30 AM ET report"

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
    data = load("slate-2026-11-14.json")
    rows: list[str] = []
    for game in data["games"]:
        away, home = game["away"], game["home"]
        matchup = f"{ABBR[away]} @ {ABBR[home]}"
        tips = f'{game["tip_et_col1"]} / {game["tip_et_col2"]}'
        note = game.get("note", "")
        reason_html = "<br>".join(e(r.split(":")[0]) for r in NO_PICK_REASONS)
        reason_titles = " · ".join(e(r) for r in NO_PICK_REASONS)
        rows.append(
            "              <tr>"
            f'<td>{e(game["weekday"])} {e(game["date"])}</td>'
            f"<td>{e(tips)}</td>"
            f"<td><strong>{e(away)}</strong> at <strong>{e(home)}</strong>"
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
        '<th scope="col">Date (ET)</th>'
        '<th scope="col">Tip-off, schedule columns 1 / 2</th>'
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
    data = load("injuries-2026-11-14-0430am.json")
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
