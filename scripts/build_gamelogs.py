#!/usr/bin/env python3
"""Build the per-player game-log block on results.html from the dated snapshot.

Task BI (arena/dab321e7-nba4). The snapshot file is a hand-captured, verified
transcription of the official gamebooks (see its extraction_notes); this script
only re-derives the published table from that file and refuses to render if any
mirrored injury-report cell disagrees with data/snapshots/injuries-2026-11-16-0915am.json.

Usage:
    python3 scripts/build_gamelogs.py          # splice the block into results.html
    python3 scripts/build_gamelogs.py --check  # exit 1 if results.html is out of date

The rows are dated attributed observations with row-level official links, NOT
betting inputs (rights gate G0; stances D-01/IR-T4 stand)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_snapshots  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "data" / "snapshots"
GAMELOGS = "player-gamelogs-2026-11-14_to_2026-11-15.json"
INJURY_FILE = "injuries-2026-11-16-0915am.json"

REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf"
REPORT_LABEL = "2026-11-16 09:15 AM ET report"
SCHEDULE_URL = build_snapshots.SCHEDULE_URL
SCHEDULE_LABEL = "Schedule PDF"


def load(name: str) -> dict:
    return json.loads((SNAPSHOTS / name).read_text(encoding="utf-8"))


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def verify_against_injury_report(data: dict) -> None:
    """Every mirrored report cell must equal the file of record, row for row."""
    injury = load(INJURY_FILE)
    rows = {
        (game["matchup"], row["player"]): row
        for game in injury["games"]
        for row in game["rows"]
        if row["player"]
    }
    problems: list[str] = []
    for entry in data["players"]:
        key = (entry["report_block"], entry["report_name"])
        row = rows.get(key)
        if row is None:
            problems.append(f"{key}: not on the injury report")
            continue
        if row["status"] != entry["report_status"] or row["reason"] != entry["report_reason"]:
            problems.append(f"{key}: mirrored status/reason differs from the file of record")
        if (row["team"] == "__lost__") != (entry["report_team_cell"] == "__lost__"):
            problems.append(f"{key}: team-lost marker differs from the file of record")
    covered = {(p["report_block"], p["report_name"]) for p in data["players"]}
    missing = sorted(set(rows) - covered)
    if missing:
        problems.append(f"players missing from the capture: {missing}")
    if problems:
        raise SystemExit("game-log snapshot failed verification:\n" + "\n".join(problems))


def render_gamelogs() -> str:
    data = load(GAMELOGS)
    verify_against_injury_report(data)

    rows: list[str] = []
    for entry in data["players"]:
        name = esc(entry["report_name"])
        status = esc(entry["report_status"]) or '<span class="flag">Unverified</span><br>status cell not printed'
        reason = esc(entry["report_reason"]) or '<span class="flag">Unverified</span><br>reason cell not printed'
        report_cell = f"{status}<br>{reason}"
        team_cell = (
            esc(entry["report_team"])
            if entry["report_team"]
            else '<span class="flag">Unverified</span><br>team cell lost at a PDF page break; left blank in the report snapshot'
        )
        if entry["games"]:
            for g in entry["games"]:
                link = (
                    f'<a class="source-link" href="{g["source_url"]}" target="_blank" '
                    f'rel="noopener noreferrer">{esc(g["source_label"])}</a>'
                )
                if g["designation"] == "played":
                    line = (
                        f'MIN <strong>{esc(g["min_printed"])}</strong> &middot; '
                        f'PTS <strong>{esc(g["pts_printed"])}</strong> &middot; '
                        f'REB <strong>{esc(g["reb_printed"])}</strong> &middot; '
                        f'AST <strong>{esc(g["ast_printed"])}</strong>'
                    )
                    note = f'Verbatim box-score line: <code>{esc(g["line_printed"])}</code>'
                else:
                    line = f'<em>{esc(g["designation"])}</em> &mdash; no stat line printed'
                    note = f'Verbatim designation: <code>{esc(g["designation_printed"])}</code>'
                if g.get("attribution_note"):
                    note += f'<br><span class="flag">Unverified</span><br>{esc(g["attribution_note"])}'
                rows.append(
                    "<tr>"
                    f"<td><strong>{name}</strong></td>"
                    f"<td>{team_cell}</td>"
                    f"<td>{report_cell}</td>"
                    f"<td>{esc(g['date'])}<br>{esc(g['team_printed_in_book'])} vs {esc(g['opponent'])}</td>"
                    f"<td>{line}</td>"
                    f"<td>{note}</td>"
                    f"<td>{link}<br>"
                    f'<a class="source-link" href="{REPORT_URL}" target="_blank" '
                    f'rel="noopener noreferrer">{REPORT_LABEL}</a></td>'
                    "</tr>"
                )
        else:
            rows.append(
                "<tr>"
                f"<td><strong>{name}</strong></td>"
                f"<td>{team_cell}</td>"
                f"<td>{report_cell}</td>"
                f"<td><span class=\"empty-value\"></span></td>"
                f"<td><em>no game in window</em></td>"
                f"<td>{esc(entry['gap'])}</td>"
                f"<td>"
                f'<a class="source-link" href="{REPORT_URL}" target="_blank" '
                f'rel="noopener noreferrer">{REPORT_LABEL}</a><br>'
                f'<a class="source-link" href="{SCHEDULE_URL}" target="_blank" '
                f'rel="noopener noreferrer">{SCHEDULE_LABEL}</a></td>'
                "</tr>"
            )

    counts = data["counts"]
    summary = (
        f'<tr><td colspan="6"><strong>Capture summary</strong> &mdash; '
        f'{counts["players"]} injury-report players; '
        f'{counts["game_rows"]} game rows from {counts["games_read"]} official gamebooks '
        f'({counts["played"]} played lines, {counts["inactive"]} inactive-list entries, '
        f'{counts["dnp"]} DNP, {counts["dnd"]} DND designations); '
        f'{counts["window_gap_players"]} players whose teams were idle on both window days.</td>'
        f'<td><a class="source-link" href="{REPORT_URL}" target="_blank" '
        f'rel="noopener noreferrer">{REPORT_LABEL}</a></td></tr>'
    )

    return (
        '<div class="table-card table-wrap">\n'
        '          <table class="data-table">\n'
        '            <thead><tr>'
        '<th scope="col">Player (report)</th>'
        '<th scope="col">Team</th>'
        '<th scope="col">Reported status / reason</th>'
        '<th scope="col">Game</th>'
        '<th scope="col">MIN / PTS / REB / AST (verbatim)</th>'
        '<th scope="col">Data note</th>'
        '<th scope="col">Official source</th>'
        "</tr></thead>\n            <tbody>\n"
        + summary
        + "\n"
        + "\n".join(rows)
        + "\n            </tbody>\n          </table>\n        </div>"
    )


BLOCK_ID = "player-gamelogs"
PAGE = "results.html"


def main(argv: list[str]) -> int:
    check = "--check" in argv
    page = ROOT / PAGE
    body = render_gamelogs()
    new_text = build_snapshots.splice(page, BLOCK_ID, body)
    if new_text is None:
        print(f"unchanged {PAGE} ({BLOCK_ID})")
        return 0
    if check:
        print(f"OUT OF DATE {PAGE} ({BLOCK_ID})")
        return 1
    page.write_text(new_text, encoding="utf-8")
    print(f"updated {PAGE} ({BLOCK_ID})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
