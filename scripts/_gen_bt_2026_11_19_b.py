#!/usr/bin/env python3
"""Build the 11/17-11/19 consecutive-revision diff, the independent cells
extraction of the 01:45 AM ET report, and the 2026-11-19 aggregates
(task BT).

The diff is produced through engine/injurystore.diff_revisions (the same
function every prior cycle used); nothing in it is hand-written. The cells
file is the independent second read of the 01:45 AM PDF (fetch_page, single
chunk, read 2026-11-19 07:35 UTC) and carries the row-for-row cross_check
against the file of record built by PR #84.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from engine.injurystore import diff_revisions, load_revision  # noqa: E402
from build_brief_data import build_aggregates  # noqa: E402

SNAP = ROOT / "data" / "snapshots"
F = "2026-11-19T07:35:00Z"
REPORT_URL = ("https://ak-static.cms.nba.com/referee/injury/"
              "Injury-Report_2026-11-19_01_45AM.pdf")
REPORT_INDEX = "https://official.nba.com/nba-injury-report-2026-27-season/"


def load(name: str) -> dict:
    return json.loads((SNAP / name).read_text(encoding="utf-8"))


def write(name: str, payload: dict) -> None:
    (SNAP / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {name}")


# ---------------------------------------------------------------------------
# Independent cells extraction of the 01:45 AM ET report (second read)
# ---------------------------------------------------------------------------

# Printed rows, in printed order: (date, time, matchup, team, player, status,
# reason, unverified, flag). Blank cells are cells the printed row lost at the
# PDF's page breaks; they stay blank and are flagged, never filled.
PRINTED = [
    ("11/19/2026", "08:00 (ET)", "GSW@MEM", "Golden State Warriors", "", "", "NOT YET SUBMITTED", False, ""),
    ("11/19/2026", "08:00 (ET)", "GSW@MEM", "Memphis Grizzlies", "", "", "NOT YET SUBMITTED", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "LA Clippers", "Beal, Bradley", "Out", "Injury/Illness - Right Knee Injury Management", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "LA Clippers", "Ingram, Brandon", "Out", "Injury/Illness - Right Heel Surgery", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "LA Clippers", "Martinelli, Nick", "Out", "G League - Two-Way", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "LA Clippers", "Miller, Jordan", "Out", "Injury/Illness - Left Rotator Cuff Surgery", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "San Antonio Spurs", "Brown, Maliq", "Out", "G League - Two-Way", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "San Antonio Spurs", "Gillespie, Ja'Kobi", "Out", "G League - Two-Way", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "San Antonio Spurs", "Harper, Dylan", "Out", "Injury/Illness - Left Hip Soreness", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "San Antonio Spurs", "Harris, Tobias", "Out", "Injury/Illness - Left Calf Strain", False, ""),
    ("11/19/2026", "08:00 (ET)", "LAC@SAS", "San Antonio Spurs", "Quaintance, Jayden", "Out", "Injury/Illness - Right Knee Surgery", False, ""),
    ("11/19/2026", "08:00 (ET)", "NYK@MIN", "Minnesota Timberwolves", "Beringer, Joan", "Available", "Injury/Illness - Face Mask", False, ""),
    ("11/19/2026", "08:00 (ET)", "NYK@MIN", "Minnesota Timberwolves", "Clark, Jaylen", "Out", "Injury/Illness - Right Hamstring Strain", False, ""),
    ("11/19/2026", "08:00 (ET)", "NYK@MIN", "Minnesota Timberwolves", "DiVincenzo, Donte", "Out", "Injury/Illness - Right Achilles Tendon Repair / Surgery", False, ""),
    ("11/19/2026", "08:00 (ET)", "NYK@MIN", "Minnesota Timberwolves", "Edwards, Anthony", "Out", "Injury/Illness - Right Knee Arthroscopy", False, ""),
    # page break: these two rows print no date, time, matchup or team cell
    ("", "", "", "", "Kuminga, Jonathan", "Questionable", "Injury/Illness - Right Shoulder Contusion", True,
     "orphan fragment on a continuation page: no date, time, matchup or team cell printed; kept as printed, not assigned to a game or a team, no reason inferred"),
    ("", "", "", "", "Pullin, Zyon", "Questionable", "Injury/Illness - Right Quadriceps Contusion", True,
     "orphan fragment on a continuation page: no date, time, matchup or team cell printed; kept as printed, not assigned to a game or a team, no reason inferred"),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Avdija, Deni", "Questionable", "Injury/Illness - Left Foot Inflammation / Soreness", False, ""),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Camara, Toumani", "Questionable", "Injury/Illness - Abdominal Soreness", False, ""),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Carlson, Branden", "Available", "Injury/Illness - Face Mask", False, ""),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Krejci, Vit", "Out", "Injury/Illness - Left Ankle Fracture", False, ""),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Morant, Ja", "Out", "Injury/Illness - Left Hamstring Strain", False, ""),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Sharpe, Shaedon", "Out", "Injury/Illness - Right Meniscus Surgery", False, ""),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Williams III, Robert", "Out", "Rest", False, ""),
    ("", "", "POR@MIL", "Portland Trail Blazers", "Youngblood, Chris", "Out", "Injury/Illness - Right Heel Contusion / Bone Bruise", False, ""),
    ("", "", "POR@MIL", "Milwaukee Bucks", "", "", "NOT YET SUBMITTED", False, ""),
    ("11/20/2026", "07:00 (ET)", "CHA@ATL", "Charlotte Hornets", "", "", "NOT YET SUBMITTED", False, ""),
    ("11/20/2026", "07:00 (ET)", "CHA@ATL", "Atlanta Hawks", "", "", "NOT YET SUBMITTED", False, ""),
    ("11/20/2026", "07:30 (ET)", "IND@CLE", "Indiana Pacers", "", "", "NOT YET SUBMITTED", False, ""),
    ("11/20/2026", "07:30 (ET)", "IND@CLE", "Cleveland Cavaliers", "", "", "NOT YET SUBMITTED", False, ""),
    ("11/20/2026", "07:30 (ET)", "ORL@BKN", "Orlando Magic", "", "", "NOT YET SUBMITTED", False, ""),
    # page break: date/time/matchup cells lost from here to the end of the page
    ("", "", "ORL@BKN", "Brooklyn Nets", "", "", "NOT YET SUBMITTED", True,
     "date, time and matchup cells lost at the PDF page break; the team and reason cells are printed and kept; matchup attached by block position"),
    ("", "", "TOR@DET", "Toronto Raptors", "", "", "", True,
     "date and time cells lost at the PDF page break; player, status and reason cells also lost - the row prints only matchup and team"),
    ("", "", "TOR@DET", "Detroit Pistons", "", "", "NOT YET SUBMITTED", True,
     "date and time cells lost at the PDF page break; team and reason cells are printed and kept; matchup attached by block position"),
    ("08:00 (ET)", "NOP@OKC", "New Orleans Pelicans", "", "", "", True, ""),
    ("", "", "NOP@OKC", "Oklahoma City Thunder", "", "", "NOT YET SUBMITTED", True,
     "date and time cells lost at the PDF page break; team and reason cells are printed and kept; matchup attached by block position"),
    ("", "", "WAS@CHI", "Washington Wizards", "", "", "", True,
     "date and time cells lost at the PDF page break; player, status and reason cells also lost"),
    ("", "", "WAS@CHI", "Chicago Bulls", "", "", "NOT YET SUBMITTED", True,
     "date and time cells lost at the PDF page break; team and reason cells are printed and kept; matchup attached by block position"),
    ("09:30 (ET)", "PHX@UTA", "Phoenix Suns", "", "", "", True, ""),
    ("", "", "PHX@UTA", "Utah Jazz", "", "", "NOT YET SUBMITTED", True,
     "date and time cells lost at the PDF page break; team and reason cells are printed and kept; matchup attached by block position"),
    ("10:00 (ET)", "HOU@DEN", "Houston Rockets", "", "", "", True, ""),
    ("", "", "HOU@DEN", "Denver Nuggets", "", "", "NOT YET SUBMITTED", True,
     "date and time cells lost at the PDF page break; team and reason cells are printed and kept; matchup attached by block position"),
    ("", "", "SAC@LAL", "Sacramento Kings", "", "", "", True,
     "date and time cells lost at the PDF page break; player, status and reason cells also lost"),
    ("", "", "SAC@LAL", "Los Angeles Lakers", "", "", "NOT YET SUBMITTED", True,
     "date and time cells lost at the PDF page break; team and reason cells are printed and kept; matchup attached by block position"),
]


def fix_orphans_shape() -> None:
    """Rows 35/38/40/42 above lost their leading date cell to a 3-cell layout.

    On the printed page the continuation rows after the second break render with
    fewer columns (e.g. ``08:00 (ET) | NOP@OKC | New Orleans Pelicans``), so the
    first cell holds the TIME, not the date. The rows are normalised here to
    (date, time, matchup, ...) with the date blank - the printed values stay
    exactly as read, only their column assignment is made explicit.
    """
    for i, row in enumerate(PRINTED):
        if row[0].endswith("(ET)") and row[1] in ("NOP@OKC", "PHX@UTA", "HOU@DEN"):
            PRINTED[i] = ("", row[0], row[1], row[2], row[3], row[4], row[5],
                          True, "date cell lost at the PDF page break; the printed "
                                "time, matchup and team cells are kept")


def build_cells() -> None:
    fix_orphans_shape()
    record = load("injuries-2026-11-19-0145am.json")
    # group printed rows into blocks by matchup, preserving printed order
    blocks: dict[str, dict] = {}
    orphan_rows = []
    for (date, time, matchup, team, player, status, reason, unver, flag) in PRINTED:
        row = {
            "team": team, "team_printed": bool(team), "player": player,
            "status": status, "reason": reason, "unverified": unver,
            "flag": flag,
        }
        if matchup:
            b = blocks.setdefault(matchup, {"game_date": date, "tip_et": time,
                                           "matchup": matchup, "rows": []})
            b["rows"].append(row)
        else:
            orphan_rows.append(row)
    games = list(blocks.values())
    # row-for-row comparison against the file of record (games blocks + orphans)
    def flat(payload: dict) -> list[tuple]:
        out = []
        for g in payload["games"]:
            for r in g["rows"]:
                out.append((g["matchup"], r["team"], r["player"], r["status"],
                            r["reason"], bool(r.get("unverified"))))
        for r in payload.get("unattributed_rows", []):
            out.append(("", r["team"], r["player"], r["status"], r["reason"],
                        bool(r.get("unverified"))))
        return out

    mine = [(g["matchup"], r["team"], r["player"], r["status"], r["reason"],
             bool(r.get("unverified"))) for g in games for r in g["rows"]]
    mine += [("", r["team"], r["player"], r["status"], r["reason"],
              bool(r.get("unverified"))) for r in orphan_rows]
    theirs = flat(record)
    only_mine = [r for r in mine if r not in theirs]
    only_theirs = [r for r in theirs if r not in mine]
    matched = sum(1 for a, b in zip(mine, theirs) if a == b) if not only_mine and not only_theirs else 0
    payload = {
        "snapshot_id": "injuries-2026-11-19-0145am",
        "kind": "official_injury_report_rows",
        "source_url": REPORT_URL,
        "source_document": record["source_document"],
        "source_document_header": record["source_document_header"],
        "source_index_url": REPORT_INDEX,
        "revision_et_label": "11/19/26 01:45 AM",
        "revision_utc": "2026-11-19T06:45:00Z",
        "fetched_at_utc": F,
        "extraction_tool": ("fetch_page (PDF text extraction to markdown tables, "
                            "single chunk, hasMore=false) - independent second "
                            "read, 2026-11-19"),
        "row_count": len(mine),
        "extraction_notes": [
            "Independent second read of the report named in source_url, produced "
            "for the row-for-row cross_check against the file of record "
            "(injuries-2026-11-19-0145am.json). Blank cells are cells the "
            "printed row lost at a PDF page break; they stay blank and flagged.",
            "The two orphan fragments (Kuminga, Pullin) print no date, time, "
            "matchup or team cell and are kept unattributed, exactly as the "
            "file of record keeps them.",
        ],
        "games": games,
        "unattributed_rows": orphan_rows,
        "cross_check": {
            "counterpart_file": "injuries-2026-11-19-0145am.json",
            "counterpart_source_document": record["source_document"],
            "rows_in_this_extraction": len(mine),
            "rows_in_the_counterpart": len(theirs),
            "rows_matching_row_for_row": matched,
            "only_in_this_extraction": [list(r) for r in only_mine],
            "only_in_the_counterpart": [list(r) for r in only_theirs],
            "rule": ("a one-sided row is reported, never deleted from either "
                     "file; the document is re-read and whichever extraction "
                     "the document contradicts is corrected"),
        },
    }
    write("injuries-2026-11-19-0145am.cells.json", payload)
    print("cross_check:", matched, "/", len(mine), "only_mine:", len(only_mine),
          "only_theirs:", len(only_theirs))


# ---------------------------------------------------------------------------
# Consecutive-revision diff: 11/17 10:30 AM -> 11/19 01:45 AM
# ---------------------------------------------------------------------------

def revision_with_label(path: Path, label: str):
    """load_revision, for files whose schema predates ``revision_et_label``."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "revision_et_label" not in payload:
        payload["revision_et_label"] = label
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", dir="/tmp",
                                         delete=False, encoding="utf-8") as fh:
            json.dump(payload, fh)
            tmp = fh.name
        try:
            return load_revision(tmp)
        finally:
            Path(tmp).unlink(missing_ok=True)
    return load_revision(path)


def build_diff() -> None:
    old = revision_with_label(SNAP / "injuries-2026-11-17-1030am.json",
                              "11/17/26 10:30 AM")
    new = load_revision(SNAP / "injuries-2026-11-19-0145am.json")
    diff = asdict(diff_revisions(old, new, source_url=new.source_url))
    diff["diff_id"] = "injuries-2026-11-17-1030-to-1119-0145.diff"
    diff["kind"] = "official_injury_report_consecutive_diff"
    diff["source_document_header"] = new.document
    diff["fetched_at_utc"] = F
    diff["extraction_tool"] = (
        "engine/injurystore.diff_revisions over the two file-of-record "
        "snapshots (no fetching)")
    diff["source_index_url"] = REPORT_INDEX
    diff["rule"] = (
        "A status change requires a matched row whose status cell differs. "
        "Rows are matched on the identity cells the row itself prints "
        "(matchup, team, player); a one-for-one leftover with identical "
        "status and reason is a printing variance, not a status change. "
        "Between 11/17 and 11/19 the printed matchups themselves change with "
        "the slate, so unmatched keys are reported as realignments "
        "(REMOVED_OR_REALIGNED / ADDED_OR_REALIGNED), never as status changes.")
    write("injuries-2026-11-17-1030-to-1119-0145.diff.json", diff)
    print("diff counts:", diff["counts"], "changes:", len(diff["changes"]))


# ---------------------------------------------------------------------------
# Aggregates-2026-11-19 (derived; no fetching)
# ---------------------------------------------------------------------------

def build_agg() -> None:
    results = load("results-2026-11-18.json")
    standings = load("standings-2026-11-19.json")
    injuries = load("injuries-2026-11-19-0145am.json")
    slate = load("slate-2026-11-19.json")
    agg = build_aggregates(
        results, standings, injuries, slate,
        agg_id="aggregates-2026-11-19",
        derived_at="2026-11-19T07:40:00Z",
        input_names={
            "results": "results-2026-11-18.json",
            "standings": "standings-2026-11-19.json",
            "injuries": injuries["snapshot_id"],
            "slate": slate["snapshot_id"],
        },
    )
    write("aggregates-2026-11-19.json", agg)


def main() -> None:
    build_cells()
    build_diff()
    build_agg()


if __name__ == "__main__":
    main()
