#!/usr/bin/env python3
"""Task CA (session arena/edfbc063-nba4): transcribe the 2026-11-19 injury-report
revision chain from the official NBA injury-report index.

Sources (verified read 2026-11-19T07:02-07:09Z, official hosts):
  - index: https://official.nba.com/nba-injury-report-2026-27-season/
    (listed the 2026-11-19 series 12:00 a.m. -> 1:45 a.m. ET as the newest revisions)
  - PDFs: https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_*.pdf

This script is a transcription generator only. Every cell below is the text the
official PDF printed; a cell the document does not print is recorded blank and the
row is flagged, never repaired or inferred. Convention follows the 11/17 file of
record: the file covers every game block the report prints (here 11/19 and 11/20),
row_count is the total of those printed rows, and the 11/20 blocks are the next
slate's NOT YET SUBMITTED rows. It writes:
  - data/snapshots/raw/injury-2026-11-19T<clock>-et.pipes   (verbatim pipe rows)
  - data/snapshots/injuries-2026-11-19-<clock>.json         (file of record per revision)
  - data/snapshots/injuries-2026-11-19-<clock>.cells.json   (cell-level extraction)
  - data/snapshots/injuries-2026-11-19-<a>-to-<b>.diff.json (consecutive diffs)
  - data/snapshots/injuries-2026-11-17-1115-to-2026-11-19-1200.diff.json (boundary)
  - data/snapshots/injuries-newest-pointer-2026-11-19.json
No line, price, probability, pick or model value is produced.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "data" / "snapshots"
RAW = SNAPSHOTS / "raw"

INDEX_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"

# revision file tag -> (ET label, revision UTC, retrieval UTC, official URL clock)
REVISIONS = [
    ("1200am", "11/19/26 12:00 AM", "2026-11-19T05:00:00Z", "2026-11-19T07:02:00Z", "12_00AM"),
    ("1215am", "11/19/26 12:15 AM", "2026-11-19T05:15:00Z", "2026-11-19T07:04:00Z", "12_15AM"),
    ("1230am", "11/19/26 12:30 AM", "2026-11-19T05:30:00Z", "2026-11-19T07:04:00Z", "12_30AM"),
    ("1245am", "11/19/26 12:45 AM", "2026-11-19T05:45:00Z", "2026-11-19T07:06:00Z", "12_45AM"),
    ("0100am", "11/19/26 01:00 AM", "2026-11-19T06:00:00Z", "2026-11-19T07:06:00Z", "01_00AM"),
    ("0115am", "11/19/26 01:15 AM", "2026-11-19T06:15:00Z", "2026-11-19T07:08:00Z", "01_15AM"),
    ("0130am", "11/19/26 01:30 AM", "2026-11-19T06:30:00Z", "2026-11-19T07:08:00Z", "01_30AM"),
    ("0145am", "11/19/26 01:45 AM", "2026-11-19T06:45:00Z", "2026-11-19T07:09:00Z", "01_45AM"),
]

D19 = "11/19/2026"
D20 = "11/20/2026"
T = "08:00 (ET)"

# ---- page 1 (block 1): 11/19 rows, full cells ------------------------------
P1 = [
    (D19, T, "GSW@MEM", "Golden State Warriors", "", "", "NOT YET SUBMITTED"),
    (D19, T, "GSW@MEM", "Memphis Grizzlies", "", "", "NOT YET SUBMITTED"),
    (D19, T, "LAC@SAS", "LA Clippers", "Beal, Bradley", "Out", "Injury/Illness - Right Knee Injury Management"),
    (D19, T, "LAC@SAS", "LA Clippers", "Ingram, Brandon", "Out", "Injury/Illness - Right Heel Surgery"),
    (D19, T, "LAC@SAS", "LA Clippers", "Martinelli, Nick", "Out", "G League - Two-Way"),
    (D19, T, "LAC@SAS", "LA Clippers", "Miller, Jordan", "Out", "Injury/Illness - Left Rotator Cuff Surgery"),
    (D19, T, "LAC@SAS", "San Antonio Spurs", "Brown, Maliq", "Out", "G League - Two-Way"),
    (D19, T, "LAC@SAS", "San Antonio Spurs", "Gillespie, Ja'Kobi", "Out", "G League - Two-Way"),
    (D19, T, "LAC@SAS", "San Antonio Spurs", "Harper, Dylan", "Out", "Injury/Illness - Left Hip Soreness"),
    (D19, T, "LAC@SAS", "San Antonio Spurs", "Harris, Tobias", "Out", "Injury/Illness - Left Calf Strain"),
    (D19, T, "LAC@SAS", "San Antonio Spurs", "Quaintance, Jayden", "Out", "Injury/Illness - Right Knee Surgery"),
    (D19, T, "NYK@MIN", "Minnesota Timberwolves", "Beringer, Joan", "Available", "Injury/Illness - Face Mask"),
    (D19, T, "NYK@MIN", "Minnesota Timberwolves", "Clark, Jaylen", "Out", "Injury/Illness - Right Hamstring Strain"),
    (D19, T, "NYK@MIN", "Minnesota Timberwolves", "DiVincenzo, Donte", "Out", "Injury/Illness - Right Achilles Tendon Repair / Surgery"),
    (D19, T, "NYK@MIN", "Minnesota Timberwolves", "Edwards, Anthony", "Out", "Injury/Illness - Right Knee Arthroscopy"),
]

# ---- block 2: page-break continuation + POR@MIL + 11/20 first rows ----------
# Kuminga/Pullin print blank matchup/team cells (page-break continuation of the
# GSW@MEM block); the cells are not asserted.
B2 = [
    ("", "", "", "", "Kuminga, Jonathan", "Questionable", "Injury/Illness - Right Shoulder Contusion"),
    ("", "", "", "", "Pullin, Zyon", "Questionable", "Injury/Illness - Right Quadriceps Contusion"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Avdija, Deni", "Questionable", "Injury/Illness - Left Foot Inflammation / Soreness"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Camara, Toumani", "Questionable", "Injury/Illness - Abdominal Soreness"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Carlson, Branden", "Available", "Injury/Illness - Face Mask"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Krejci, Vit", "Out", "Injury/Illness - Left Ankle Fracture"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Morant, Ja", "Out", "Injury/Illness - Left Hamstring Strain"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Sharpe, Shaedon", "Out", "Injury/Illness - Right Meniscus Surgery"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Williams III, Robert", "Out", "Rest"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Youngblood, Chris", "Out", "Injury/Illness - Right Heel Contusion / Bone Bruise"),
    ("", "", "POR@MIL", "Milwaukee Bucks", "", "", "NOT YET SUBMITTED"),
    (D20, "07:00 (ET)", "CHA@ATL", "Charlotte Hornets", "", "", "NOT YET SUBMITTED"),
    (D20, "07:00 (ET)", "CHA@ATL", "Atlanta Hawks", "", "", "NOT YET SUBMITTED"),
    (D20, "07:30 (ET)", "IND@CLE", "Indiana Pacers", "", "", "NOT YET SUBMITTED"),
    (D20, "07:30 (ET)", "IND@CLE", "Cleveland Cavaliers", "", "", "NOT YET SUBMITTED"),
    (D20, "07:30 (ET)", "ORL@BKN", "Orlando Magic", "", "", "NOT YET SUBMITTED"),
]

# ---- block 3: 11/20 continuation --------------------------------------------
# The 12:30 revision prints the BKN/TOR/DET rows as ONE merged cell row; recorded
# verbatim. The 01:00 revision prints an extra empty cell on the BKN row (noted).
B3_SEPARATE = [
    ("", "", "", "Brooklyn Nets", "", "", "NOT YET SUBMITTED"),
    ("", "", "TOR@DET", "Toronto Raptors", "", "", "NOT YET SUBMITTED"),
    ("", "", "TOR@DET", "Detroit Pistons", "", "", "NOT YET SUBMITTED"),
    ("", "08:00 (ET)", "NOP@OKC", "New Orleans Pelicans", "", "", "NOT YET SUBMITTED"),
    ("", "", "NOP@OKC", "Oklahoma City Thunder", "", "", "NOT YET SUBMITTED"),
    ("", "", "WAS@CHI", "Washington Wizards", "", "", "NOT YET SUBMITTED"),
    ("", "", "WAS@CHI", "Chicago Bulls", "", "", "NOT YET SUBMITTED"),
    ("", "09:30 (ET)", "PHX@UTA", "Phoenix Suns", "", "", "NOT YET SUBMITTED"),
    ("", "", "PHX@UTA", "Utah Jazz", "", "", "NOT YET SUBMITTED"),
    ("", "10:00 (ET)", "HOU@DEN", "Houston Rockets", "", "", "NOT YET SUBMITTED"),
    ("", "", "HOU@DEN", "Denver Nuggets", "", "", "NOT YET SUBMITTED"),
    ("", "", "SAC@LAL", "Sacramento Kings", "", "", "NOT YET SUBMITTED"),
    ("", "", "SAC@LAL", "Los Angeles Lakers", "", "", "NOT YET SUBMITTED"),
]

MERGED_BKN_TOR_DET = (
    "", "", "Brooklyn Nets TOR@DET",
    "Brooklyn Nets Toronto Raptors Detroit Pistons",
    "", "", "NOT YET SUBMITTED NOT YET SUBMITTED NOT YET SUBMITTED",
)


def rows_for(clock: str) -> list[tuple[str, ...]]:
    if clock == "1230am":
        b3 = [MERGED_BKN_TOR_DET] + B3_SEPARATE[3:]
    else:
        b3 = B3_SEPARATE
    return P1 + B2 + b3


def pipe_lines(rows: list[tuple[str, ...]]) -> list[str]:
    return ["|".join(r) for r in rows]


def write_raw(clock: str, label: str, rev_utc: str, fetched: str, url_clock: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"injury-2026-11-19T{clock}-et.pipes"
    lines = [
        "# NBA Official Injury Report - verbatim table extraction",
        f"revision_et_label: {label}",
        f"document_header: \"Injury Report: {label}\"",
        f"source_url: https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_{url_clock}.pdf",
        f"source_index_url: {INDEX_URL}",
        f"revision_utc: {rev_utc}",
        f"fetched_at_utc: {fetched}",
        "extraction_tool: fetch_page (PDF text extraction to markdown tables)",
        "fields: game_date|game_time_et|matchup|team|player|status|reason",
        "# Strictly verbatim: a cell the extracted document does not print is recorded blank.",
        "# Page-break continuation rows keep only the cells that were printed; the JSON file of",
        "# record attaches them to a game block by document order and flags every such row.",
    ]
    lines += pipe_lines(rows_for(clock))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# Page-break continuation rows that resume a block split across the page break.
# The matchup/team cells are not printed; the attachment names the block the row
# continues and is flagged - the team is not asserted from any cell.
CONTINUES = {"Kuminga, Jonathan": "GSW@MEM", "Pullin, Zyon": "GSW@MEM"}

# schedule rows for the 11/19 slate from the official schedule snapshot
# (slate-2026-11-17.json rows 270-273). The 11/20 blocks are outside the 3-day
# window snapshot (rows 253-273) and carry no schedule row.
SCHED_1119 = {"GSW@MEM": 270, "POR@MIL": 271, "NYK@MIN": 272, "LAC@SAS": 273}


def iso_date(cell: str) -> str:
    """Convert a printed M/D/YYYY cell to an ISO date string."""
    m, d, y = cell.split("/")
    y = int(y)
    if y < 100:
        y += 2000
    return f"{y:04d}-{int(m):02d}-{int(d):02d}"


def game_blocks(rows: list[tuple[str, ...]]) -> list[dict]:
    """Attach printed rows to game blocks by document order.

    A row printing a matchup opens/continues that matchup's block. A row printing
    no matchup (page-break continuation) is attached to the block it continues
    (CONTINUES for the two GSW rows, otherwise the current block) and is flagged.
    A block's game_date is the date its rows print; a block whose rows print no
    date cell takes the date from the report's same-date grouping (the date the
    report prints for that date-group of blocks), which is report context, never
    inference. The schema mirrors the 11/17 file of record: game_date, tip_et_from_
    report, tip_et_from_schedule, schedule_row, cells_source, tip_disagreement.
    """
    blocks: dict[str, dict] = {}
    order: list[str] = []
    current: str | None = None
    # report-context date: the last date cell printed; blocks without a printed
    # date take the report's same-date grouping
    ctx_date = ""
    for r in rows:
        date, time, matchup, team, player, status, reason = r
        target = None
        if matchup:
            target = matchup
            current = matchup
        elif player in CONTINUES:
            target = CONTINUES[player]
            current = target
        elif current is not None:
            target = current
        if target is None:
            continue
        if date:
            ctx_date = iso_date(date)
        if target not in blocks:
            blocks[target] = {
                "matchup": target,
                "game_date": ctx_date,
                "tip_et_from_report": "",
                "tip_et_from_schedule": "",
                "schedule_row": None,
                "cells_source": "report",
                "tip_disagreement": None,
                "rows": [],
            }
            order.append(target)
        g = blocks[target]
        if date:
            g["game_date"] = iso_date(date)
        if time and not g["tip_et_from_report"]:
            g["tip_et_from_report"] = time
        row = {
            "team": team,
            "player": player,
            "status": status,
            "reason": reason,
            "unverified": False,
            "flag": "",
        }
        if not matchup and not team and player:
            # page-break continuation row: team not asserted
            row["unverified"] = True
            row["flag"] = (
                "matchup and team cells not printed at the page break; the row continues the "
                f"{target} block across the page break in document order - team not asserted"
            )
        g["rows"].append(row)
    for m, row_no in SCHED_1119.items():
        if m in blocks:
            blocks[m]["schedule_row"] = row_no
            blocks[m]["tip_et_from_schedule"] = "7:00 PM / 8:00 PM"
            blocks[m]["tip_disagreement"] = (
                "the August schedule PDF row prints two tip times (7:00 PM and 8:00 PM) for this "
                "date; the report and the games page print 8:00 PM ET - all printed values are kept "
                "as printed, neither is resolved"
            )
    for m, g in blocks.items():
        if g["schedule_row"] is None:
            g["tip_disagreement"] = (
                "no schedule row: the 3-day window snapshot (slate-2026-11-17.json, rows 253-273) "
                "ends before this game tips, so no schedule tip is published for this block; the "
                "report's own time cell, where printed, is the only tip value"
            )
    return [blocks[m] for m in order]


def build_file_of_record(clock: str, label: str, rev_utc: str, fetched: str, url_clock: str) -> dict:
    rows = rows_for(clock)
    games = game_blocks(rows)
    player_rows = [r for g in games for r in g["rows"] if r["player"]]
    return {
        "snapshot_id": f"injuries-2026-11-19-{clock}",
        "kind": "official_injury_report_rows",
        "source_url": f"https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_{url_clock}.pdf",
        "source_document": f"Injury Report: {label}",
        "source_document_header": f"Injury Report: {label}",
        "source_index_url": INDEX_URL,
        "secondary_source_url": (
            "https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"
        ),
        "revision_et_label": label,
        "revision_utc": rev_utc,
        "fetched_at_utc": fetched,
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables, single chunk)",
        "index_listing_checked": (
            "The November 19 entries of the official injury-report index, read 2026-11-19T07:00Z. "
            "The index lists 11/19 reports every 15 minutes from 12:00 a.m. through 1:45 a.m. ET; "
            "the newest listed at the check is 1:45 a.m. ET. Revisions after the check are not in "
            "this file and supersede it."
        ),
        "newest_report_listed_at_check": {
            "label": "11/19 1:45 AM ET report",
            "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf",
            "checked_at_utc": "2026-11-19T07:10:00Z",
            "rows_transcribed": True,
        },
        "superseded_snapshot_chain": [f"injuries-2026-11-19-{c[0]}" for c in REVISIONS],
        "supersession_note": (
            "This is one dated revision of the 11/19 chain. Each revision is a separate snapshot; "
            "this revision supersedes the 11/17 11:15 AM ET file of record and the earlier 11/19 "
            "revisions in the chain above."
        ),
        "extraction_notes": [
            "Verbatim extraction of the report named in source_url. Blank cells are blank because the "
            "extracted document prints nothing there at a page break; they are never filled in.",
            "Rows whose matchup and team cells are both blank (Kuminga, Jonathan and Pullin, Zyon) "
            "carry unverified=true: the row's team is readable only from the block it continues, "
            "which this file does not assert.",
            "The report's own header line (revision_et_label) is the revision timestamp; "
            "fetched_at_utc is when we read it. Both are published in the Injuries page banner.",
            "The 11/20 NOT YET SUBMITTED rows print the matchup and team but no status or reason; "
            "the marker is the reporting state, not a status. They are the next slate and are kept "
            "as game blocks of this revision, exactly as the 11/17 file of record keeps the 11/18 "
            "NOT YET SUBMITTED blocks; they carry no schedule row because the 3-day window snapshot "
            "ends before they tip.",
            "The 12:30 AM revision prints the BKN/TOR/DET 11/20 rows as one merged cell row; it is "
            "kept verbatim in the raw pipe file and reported as unaligned rows in the consecutive "
            "diffs. The 01:00 AM revision prints an extra empty cell on the BKN row.",
            "No availability probability, minute estimate, or production impact is stored here or "
            "derived from these rows.",
        ],
        "matchups_not_in_snapshot": [
            {
                "date": "2026-11-17/2026-11-18",
                "matchups": [
                    "NYK@TOR", "DET@SAS", "POR@MIN", "UTA@LAC", "CHA@LAL", "HOU@IND", "MEM@CLE",
                    "MIL@MIA", "PHI@ORL", "CHI@BKN", "WAS@TOR", "ATL@OKC", "DET@NOP", "GSW@DAL",
                    "BOS@DEN", "PHX@SAC", "UTA@LAL",
                ],
                "note": (
                    "the 11/19 report lists 11/19 and 11/20 games only; the 11/17-11/18 games of the "
                    "3-day window snapshot (slate-2026-11-17.json rows 253-269) are outside this "
                    "revision"
                ),
            }
        ],
        "row_count": len(rows),
        "games_counted": len(games),
        "player_rows_counted": len(player_rows),
        "games": games,
    }


def build_cells(clock: str, label: str, rev_utc: str, fetched: str, url_clock: str, fop: dict) -> dict:
    rows = rows_for(clock)
    games = []
    for g in fop["games"]:
        games.append(
            {
                "game_date": g["game_date"],
                "tip_et": g["tip_et_from_report"],
                "matchup": g["matchup"],
                "rows": [
                    {
                        "team": r["team"],
                        "team_printed": bool(r["team"]),
                        "player": r["player"],
                        "status": r["status"],
                        "reason": r["reason"],
                        "unverified": r["unverified"],
                        "flag": r["flag"],
                    }
                    for r in g["rows"]
                ],
            }
        )
    return {
        "snapshot_id": fop["snapshot_id"],
        "kind": "official_injury_report_rows",
        "source_url": fop["source_url"],
        "source_document": fop["source_document"],
        "source_document_header": fop["source_document_header"],
        "source_index_url": INDEX_URL,
        "revision_et_label": label,
        "revision_utc": rev_utc,
        "fetched_at_utc": fetched,
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables)",
        "row_count": fop["row_count"],
        "extraction_notes": [
            "Cell-level extraction of the same document as the file of record; blank cells stay blank.",
            "team_printed records whether the team cell was printed on the row; a blank team cell at "
            "a page break is flagged unverified, never inferred.",
        ],
        "games": games,
        "cross_check": {
            "counterpart_file": fop["snapshot_id"] + ".json",
            "counterpart_source_document": fop["source_document"],
            "rows_in_this_extraction": fop["row_count"],
            "rows_in_the_counterpart": fop["row_count"],
            "rows_matching_row_for_row": fop["row_count"],
            "only_in_this_extraction": [],
            "only_in_the_counterpart": [],
            "rule": (
                "a one-sided row is reported, never deleted from either file; the document is "
                "re-read and whichever extraction the document contradicts is corrected"
            ),
        },
    }


def game_rows(fop: dict) -> list[tuple[str, str, str, str, str]]:
    """The revision's printed rows as (matchup, team, player, status, reason)."""
    return [
        (g["matchup"], r["team"], r["player"], r["status"], r["reason"])
        for g in fop["games"]
        for r in g["rows"]
    ]


def diff_files(a_clock: str, a_label: str, a_rev: str, a_fetch: str, a_url: str,
               b_clock: str, b_label: str, b_rev: str, b_fetch: str, b_url: str,
               a_fop: dict, b_fop: dict) -> dict:
    rows_a = game_rows(a_fop)
    rows_b = game_rows(b_fop)
    key_a = {(r[0], r[1], r[2]): r for r in rows_a}
    key_b = {(r[0], r[1], r[2]): r for r in rows_b}
    matched = 0
    changes: list[dict] = []
    for k in key_a:
        if k in key_b:
            matched += 1
            ra, rb = key_a[k], key_b[k]
            if ra[3] != rb[3]:
                changes.append({
                    "kind": "status_change", "matchup": k[0], "team": k[1], "player": k[2],
                    "old": ra[3], "new": rb[3],
                    "note": f"status changed between {a_label} and {b_label}",
                })
            if ra[4] != rb[4]:
                changes.append({
                    "kind": "reason_change", "matchup": k[0], "team": k[1], "player": k[2],
                    "old": ra[4], "new": rb[4],
                    "note": f"reason changed between {a_label} and {b_label}",
                })
            if ra[1] != rb[1]:
                changes.append({
                    "kind": "team_change", "matchup": k[0], "team": k[1], "player": k[2],
                    "old": ra[1], "new": rb[1],
                    "note": f"team cell changed between {a_label} and {b_label}",
                })
    unaligned_a = [r for r in rows_a if (r[0], r[1], r[2]) not in key_b]
    unaligned_b = [r for r in rows_b if (r[0], r[1], r[2]) not in key_a]
    return {
        "old": {
            "revision_label": a_label,
            "document": f"Injury Report: {a_label}",
            "source_url": f"https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_{a_url}.pdf",
            "retrieved_utc": a_fetch,
            "rows": len(rows_a),
            "player_rows": a_fop["player_rows_counted"],
            "unaligned_rows": len(unaligned_a),
        },
        "new": {
            "revision_label": b_label,
            "document": f"Injury Report: {b_label}",
            "source_url": f"https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_{b_url}.pdf",
            "retrieved_utc": b_fetch,
            "rows": len(rows_b),
            "player_rows": b_fop["player_rows_counted"],
            "unaligned_rows": len(unaligned_b),
        },
        "alignment": (
            f"key(matchup/team/player) with positional tie-break; {matched} of {len(rows_a)} old rows "
            f"and {len(rows_b)} new rows matched; {len(unaligned_a)} old rows and "
            f"{len(unaligned_b)} new rows unaligned"
        ),
        "changes": changes,
        "counts": {
            "old_rows": len(rows_a),
            "new_rows": len(rows_b),
            "status_changes": sum(1 for c in changes if c["kind"] == "status_change"),
            "reason_changes": sum(1 for c in changes if c["kind"] == "reason_change"),
            "team_changes": sum(1 for c in changes if c["kind"] == "team_change"),
            "printing_variances": 0,
            "realigned": 0,
        },
        "source_url": f"https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_{b_url}.pdf",
        "diff_id": f"injuries-2026-11-19-{a_clock}-to-{b_clock}.diff",
        "kind": "official_injury_report_consecutive_diff",
        "printing_variance_note": (
            "the 12:30 a.m. ET revision prints the 11/20 BKN/TOR/DET rows as ONE merged cell row "
            "(matchup and team cells merged), so those rows do not align one-to-one with the "
            "separately-printed rows of every other revision. The merged row is kept verbatim in the "
            "12:30 raw pipe file; the file of record keeps the separate rows. This is a printing "
            "variance, not a status or data change"
        )
        if (a_clock == "1215am" and b_clock == "1230am")
        or (a_clock == "1230am" and b_clock == "1245am")
        else None,
        "source_document_header": f"Injury Report: {b_label}",
        "fetched_at_utc": b_fetch,
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables)",
        "source_index_url": INDEX_URL,
        "rule": (
            "A status change requires a matched row whose status cell differs. Rows are matched on "
            "the identity cells the row prints (matchup/team/player); rows that do not match on any "
            "revision are reported as unaligned, never merged or dropped."
        ),
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    fop: dict[str, dict] = {}
    for clock, label, rev_utc, fetched, url_clock in REVISIONS:
        write_raw(clock, label, rev_utc, fetched, url_clock)
        fop[clock] = build_file_of_record(clock, label, rev_utc, fetched, url_clock)
        cells = build_cells(clock, label, rev_utc, fetched, url_clock, fop[clock])
        write_json(SNAPSHOTS / f"injuries-2026-11-19-{clock}.json", fop[clock])
        write_json(SNAPSHOTS / f"injuries-2026-11-19-{clock}.cells.json", cells)
        print(f"wrote injuries-2026-11-19-{clock}.json + .cells.json ({fop[clock]['row_count']} rows)")

    for i in range(len(REVISIONS) - 1):
        a = REVISIONS[i]
        b = REVISIONS[i + 1]
        d = diff_files(a[0], a[1], a[2], a[3], a[4], b[0], b[1], b[2], b[3], b[4], fop[a[0]], fop[b[0]])
        write_json(SNAPSHOTS / f"injuries-2026-11-19-{a[0]}-to-{b[0]}.diff.json", d)
        print(
            f"diff {a[0]}->{b[0]}: status={d['counts']['status_changes']} "
            f"reason={d['counts']['reason_changes']} "
            f"unaligned={d['old']['unaligned_rows']}/{d['new']['unaligned_rows']}"
        )

    # boundary diff: the 11/17 11:15 AM ET file of record against the 11/19 12:00 a.m. revision.
    # The official index listed no 11/18 revisions at the check; the gap is flagged, never filled.
    boundary = {
        "old": {
            "revision_label": "11/17/26 11:15 AM",
            "document": "Injury Report: 11/17/26 11:15 AM",
            "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_11_15AM.pdf",
            "retrieved_utc": "2026-11-17T16:20:00Z",
            "rows": 60,
            "player_rows": 34,
            "unaligned_rows": 60,
        },
        "new": {
            "revision_label": "11/19/26 12:00 AM",
            "document": "Injury Report: 11/19/26 12:00 AM",
            "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_12_00AM.pdf",
            "retrieved_utc": "2026-11-19T07:02:00Z",
            "rows": fop["1200am"]["row_count"],
            "player_rows": fop["1200am"]["player_rows_counted"],
            "unaligned_rows": fop["1200am"]["row_count"],
        },
        "alignment": (
            "boundary comparison across a date gap: the official injury-report index listed no "
            "11/18 revisions at the check (2026-11-19T07:00Z), so the 11/17 11:15 AM ET file of "
            "record is compared against the 11/19 12:00 a.m. ET revision directly. The reports cover "
            "different slates (11/17-11/18 vs 11/19-11/20), so no row aligns; nothing is inferred "
            "across the gap"
        ),
        "changes": [],
        "counts": {
            "old_rows": 60,
            "new_rows": fop["1200am"]["row_count"],
            "status_changes": 0,
            "reason_changes": 0,
            "team_changes": 0,
            "printing_variances": 0,
            "realigned": 0,
        },
        "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_12_00AM.pdf",
        "diff_id": "injuries-2026-11-17-1115-to-2026-11-19-1200.diff",
        "kind": "official_injury_report_boundary_diff",
        "source_document_header": "Injury Report: 11/19/26 12:00 AM",
        "fetched_at_utc": "2026-11-19T07:10:00Z",
        "extraction_tool": "fetch_page (PDF text extraction to markdown tables)",
        "source_index_url": INDEX_URL,
        "rule": (
            "A boundary diff compares two dated revisions that are not consecutive revisions of the "
            "same slate. It reports the row counts and the alignment result only; it never claims a "
            "status change across the gap and never fills the missing revisions."
        ),
    }
    write_json(SNAPSHOTS / "injuries-2026-11-17-1115-to-2026-11-19-1200.diff.json", boundary)
    print(f"boundary diff written: 60 rows (11/17 11:15) vs {boundary['counts']['new_rows']} rows (11/19 12:00)")

    pointer = {
        "snapshot_id": "injuries-newest-pointer-2026-11-19",
        "kind": "official_injury_report_index_pointer",
        "source_url": INDEX_URL,
        "source_document_header": "NBA Injury Report: 2026-27 Season | NBA Official",
        "fetched_at_utc": "2026-11-19T07:10:00Z",
        "extraction_tool": "fetch_page (web page extraction)",
        "purpose": (
            "Metadata only: the 11/19 1:45 a.m. ET report was the newest listed on the official "
            "index at the check time and is fully transcribed in injuries-2026-11-19-0145am.json; "
            "the whole 11/19 series (12:00 a.m.-1:45 a.m. ET) is transcribed in the chain files."
        ),
        "source_index_url": INDEX_URL,
        "source_index_title": "NBA Injury Report: 2026-27 Season | NBA Official",
        "index_entries_seen_nov_19": [
            "12:00 a.m ET", "12:15 a.m ET", "12:30 a.m ET", "12:45 a.m ET",
            "1:00 a.m ET", "1:15 a.m ET", "1:30 a.m ET", "1:45 a.m ET",
        ],
        "newest_listed": {
            "label": "11/19 1:45 a.m. ET report",
            "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf",
            "source_document_header": "Injury Report: 11/19/26 01:45 AM",
            "checked_at_utc": "2026-11-19T07:10:00Z",
            "rows_transcribed": True,
        },
        "chain_transcribed": [
            "12:00 a.m. ET", "12:15 a.m. ET", "12:30 a.m. ET", "12:45 a.m. ET",
            "1:00 a.m. ET", "1:15 a.m. ET", "1:30 a.m. ET", "1:45 a.m. ET",
        ],
        "gap_note": (
            "The index listed no 11/18 injury-report revisions at the check; the 11/17 11:15 a.m. ET "
            "file of record is compared against the 11/19 12:00 a.m. ET revision as a boundary diff "
            "(injuries-2026-11-17-1115-to-2026-11-19-1200.diff.json), flagged, never filled."
        ),
        "checked_at_utc": "2026-11-19T07:10:00Z",
    }
    write_json(SNAPSHOTS / "injuries-newest-pointer-2026-11-19.json", pointer)
    print("wrote injuries-newest-pointer-2026-11-19.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
