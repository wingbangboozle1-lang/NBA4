#!/usr/bin/env python3
"""Generate data/snapshots/player-gamelogs-2026-11-14_to_2026-11-15-anchor-2026-11-17.json.

BM (arena/0fec89b5-nba4) refresh: per-player game logs for every named player
of the current injury file of record (injuries-2026-11-17-1030am.json, 33
players), each observed in her/his team's most recent completed game:

  * Detroit's latest game is 2026-11-14 DET@MIA; the other six teams last
    played on 2026-11-15. None of the 33 players' teams played on 2026-11-16
    (the eight 11/16 finals carry no current-report team), so the observation
    window 2026-11-14 to 2026-11-15 holds for the whole roster.
  * Every value is read verbatim from chunk 0 of the official gamebook PDF
    (full-game box score + inactive list) or is the report cell mirrored from
    the file of record. Nothing is computed, reconciled or inferred.
  * The earlier capture in player-gamelogs-2026-11-14_to_2026-11-15.json
    (anchored to the 2026-11-16 09:15 AM report, task BI) is kept unchanged
    as a dated historical snapshot.

Run: python3 scripts/_gen_gamelogs_0fec89b5.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "data" / "snapshots"
OUT = SNAPSHOTS / "player-gamelogs-2026-11-14_to_2026-11-15-anchor-2026-11-17.json"
INJURY = "injuries-2026-11-17-1030am.json"

REPORT_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-17_10_30AM.pdf"
REPORT_HEADER = "Injury Report: 11/17/26 10:30 AM"

GAMES = {
    "DET@MIA": {
        "date": "2026-11-14",
        "game_id": "0022600233",
        "url": "https://statsdmz.nba.com/pdfs/20261114/20261114_DETMIA_book.pdf",
        "label": "Official NBA gamebook, DET@MIA 2026-11-14 (box score + inactive list)",
    },
    "LAL@PHX": {
        "date": "2026-11-15",
        "game_id": "0022600237",
        "url": "https://statsdmz.nba.com/pdfs/20261115/20261115_LALPHX_book.pdf",
        "label": "Official NBA gamebook, LAL@PHX 2026-11-15 (box score + inactive list)",
    },
    "CHA@LAC": {
        "date": "2026-11-15",
        "game_id": "0022600238",
        "url": "https://statsdmz.nba.com/pdfs/20261115/20261115_CHALAC_book.pdf",
        "label": "Official NBA gamebook, CHA@LAC 2026-11-15 (box score + inactive list)",
    },
    "SAS@UTA": {
        "date": "2026-11-15",
        "game_id": "0022600239",
        "url": "https://statsdmz.nba.com/pdfs/20261115/20261115_SASUTA_book.pdf",
        "label": "Official NBA gamebook, SAS@UTA 2026-11-15 (box score + inactive list)",
    },
    "NYK@TOR": {
        "date": "2026-11-15",
        "game_id": "0022600241",
        "url": "https://statsdmz.nba.com/pdfs/20261115/20261115_NYKTOR_book.pdf",
        "label": "Official NBA gamebook, NYK@TOR 2026-11-15 (box score + inactive list)",
    },
}

# (report_block, report_name) -> observation read from the named gamebook.
# designation "played" carries the printed box line; anything else carries the
# printed designation and null stat cells (never a computed value).
OBS: dict[tuple[str, str], dict] = {
    # --- Detroit at Miami, 2026-11-14 (players in the DET@SAS report block) ---
    ("DET@SAS", "Duren, Jalen"): {
        "game": "DET@MIA", "team": "Detroit Pistons", "opp": "MIAMI HEAT",
        "designation": "inactive",
        "printed": "Inactive: Pistons - Duren (Injury/Illness - Right Hamstring Strain)",
    },
    ("DET@SAS", "Holland II, Ronald"): {
        "game": "DET@MIA", "team": "Detroit Pistons", "opp": "MIAMI HEAT",
        "designation": "played",
        "min": "21:33", "pts": "5", "reb": "7", "ast": "3",
        "line": "5 Ronald Holland II |  | 21:33 | 2-6 FG | 1-1 3P | 0-0 FT | 5 OR | 2 DR | 7 TOT | 3 A | 5 PTS",
    },
    ("DET@SAS", "Joe, Isaiah"): {
        "game": "DET@MIA", "team": "Detroit Pistons", "opp": "MIAMI HEAT",
        "designation": "inactive",
        "printed": "Inactive: Pistons - Joe (Injury/Illness - Right Hip Contusion)",
    },
    ("DET@SAS", "Okorie, Ebuka"): {
        "game": "DET@MIA", "team": "Detroit Pistons", "opp": "MIAMI HEAT",
        "designation": "inactive",
        "printed": "Inactive: Pistons - Okorie (G League - On Assignment)",
    },
    ("DET@SAS", "Onyenso, Ugonna"): {
        "game": "DET@MIA", "team": "Detroit Pistons", "opp": "MIAMI HEAT",
        "designation": "inactive",
        "printed": "Inactive: Pistons - Onyenso (G League - Two-Way)",
    },
    ("DET@SAS", "Prince, Taurean"): {
        "game": "DET@MIA", "team": "Detroit Pistons", "opp": "MIAMI HEAT",
        "designation": "played",
        "min": "08:16", "pts": "2", "reb": "1", "ast": "1",
        "line": "12 Taurean Prince |  | 08:16 | 1-3 FG | 0-1 3P | 0-0 FT | 0 OR | 0 DR | 1 TOT | 1 A | 2 PTS",
    },
    ("DET@SAS", "Robinson, Duncan"): {
        "game": "DET@MIA", "team": "Detroit Pistons", "opp": "MIAMI HEAT",
        "designation": "played",
        "min": "16:55", "pts": "10", "reb": "1", "ast": "1",
        "line": "55 Duncan Robinson | F | 16:55 | 3-8 FG | 2-6 3P | 2-2 FT | 0 OR | 1 DR | 1 TOT | 1 A | 10 PTS",
    },
    # --- New York at Toronto, 2026-11-15 (TOR report block) ---
    ("NYK@TOR", "Bittle, Nate"): {
        "game": "NYK@TOR", "team": "TORONTO RAPTORS", "opp": "New York Knicks",
        "designation": "inactive",
        "printed": "Inactive: Raptors - Bittle (Injury/Illness - Right Foot Avulsion Fracture)",
    },
    ("NYK@TOR", "Leonard, Kawhi"): {
        "game": "NYK@TOR", "team": "TORONTO RAPTORS", "opp": "New York Knicks",
        "designation": "inactive",
        "printed": "Inactive: Raptors - Leonard (Injury/Illness - Left Knee Injury Management)",
    },
    ("NYK@TOR", "McCullar Jr., Kevin"): {
        "game": "NYK@TOR", "team": "TORONTO RAPTORS", "opp": "New York Knicks",
        "designation": "inactive",
        "printed": "Inactive: Raptors - McCullar Jr. (G League - Two-Way)",
    },
    ("NYK@TOR", "Smith, Malachi"): {
        "game": "NYK@TOR", "team": "TORONTO RAPTORS", "opp": "New York Knicks",
        "designation": "inactive",
        "printed": "Inactive: Raptors - Smith (G League - Two-Way)",
    },
    # --- San Antonio at Utah, 2026-11-15 (SAS report block, DET@SAS) ---
    ("DET@SAS", "Brown, Maliq"): {
        "game": "SAS@UTA", "team": "San Antonio Spurs", "opp": "UTAH JAZZ",
        "designation": "inactive",
        "printed": "Inactive: Spurs - Brown (G League - Two-Way)",
    },
    ("DET@SAS", "Gillespie, Ja'Kobi"): {
        "game": "SAS@UTA", "team": "San Antonio Spurs", "opp": "UTAH JAZZ",
        "designation": "inactive",
        "printed": "Inactive: Spurs - Gillespie (G League - Two-Way)",
    },
    ("DET@SAS", "Harris, Tobias"): {
        "game": "SAS@UTA", "team": "San Antonio Spurs", "opp": "UTAH JAZZ",
        "designation": "inactive",
        "printed": "Inactive: Spurs - Harris (Injury/Illness - Left Calf Strain)",
    },
    ("DET@SAS", "Quaintance, Jayden"): {
        "game": "SAS@UTA", "team": "San Antonio Spurs", "opp": "UTAH JAZZ",
        "designation": "inactive",
        "printed": "Inactive: Spurs - Quaintance (Injury/Illness - Right Knee Surgery)",
    },
    # --- Utah players (UTA@LAC report block), observed in SAS@UTA ---
    ("UTA@LAC", "Bufkin, Kobe"): {
        "game": "SAS@UTA", "team": "UTAH JAZZ", "opp": "San Antonio Spurs",
        "designation": "inactive",
        "printed": "Inactive: Jazz - Bufkin (G League - Two-Way)",
    },
    ("UTA@LAC", "Hayes, Jaxson"): {
        "game": "SAS@UTA", "team": "UTAH JAZZ", "opp": "San Antonio Spurs",
        "designation": "dnd",
        "printed": "11 Jaxson Hayes | DND - Injury/Illness - Left Knee Strain",
    },
    ("UTA@LAC", "Ingram, Harrison"): {
        "game": "SAS@UTA", "team": "UTAH JAZZ", "opp": "San Antonio Spurs",
        "designation": "inactive",
        "printed": "Inactive: Jazz - Ingram (G League - Two-Way)",
    },
    ("UTA@LAC", "Jackson Jr., Jaren"): {
        "game": "SAS@UTA", "team": "UTAH JAZZ", "opp": "San Antonio Spurs",
        "designation": "inactive",
        "printed": "Inactive: Jazz - Jackson Jr. (Injury/Illness - Right MCL Tear)",
    },
    ("UTA@LAC", "Markkanen, Lauri"): {
        "game": "SAS@UTA", "team": "UTAH JAZZ", "opp": "San Antonio Spurs",
        "designation": "inactive",
        "printed": "Inactive: Jazz - Markkanen (Injury/Illness - Right Hand Fracture)",
    },
    ("UTA@LAC", "Nurkic, Jusuf"): {
        "game": "SAS@UTA", "team": "UTAH JAZZ", "opp": "San Antonio Spurs",
        "designation": "inactive",
        "printed": "Inactive: Jazz - Nurkić (Injury/Illness - Right 2nd Plantar Plate Tear)",
    },
    # --- LA Clippers players (UTA@LAC report block), observed in CHA@LAC ---
    ("UTA@LAC", "Beal, Bradley"): {
        "game": "CHA@LAC", "team": "LA CLIPPERS", "opp": "Charlotte Hornets",
        "designation": "inactive",
        "printed": "Inactive: Clippers - Beal (Injury/Illness - Right Knee Injury Management)",
    },
    ("UTA@LAC", "Ingram, Brandon"): {
        "game": "CHA@LAC", "team": "LA CLIPPERS", "opp": "Charlotte Hornets",
        "designation": "inactive",
        "printed": "Inactive: Clippers - Ingram (Injury/Illness - Right Heel Surgery )",
    },
    ("UTA@LAC", "Miller, Jordan"): {
        "game": "CHA@LAC", "team": "LA CLIPPERS", "opp": "Charlotte Hornets",
        "designation": "inactive",
        "printed": "Inactive: Clippers - Miller (Injury/Illness - Left Rotator Cuff Surgery )",
    },
    ("UTA@LAC", "Niederhauser, Yanic Konan"): {
        "game": "CHA@LAC", "team": "LA CLIPPERS", "opp": "Charlotte Hornets",
        "designation": "inactive",
        "printed": "Inactive: Clippers - Niederhäuser (Injury/Illness - Right Lisfranc Surgery )",
    },
    # --- Charlotte players (CHA@LAL report block), observed in CHA@LAC ---
    ("CHA@LAL", "Ajayi, Michael"): {
        "game": "CHA@LAC", "team": "Charlotte Hornets", "opp": "LA CLIPPERS",
        "designation": "inactive",
        "printed": "Inactive: Hornets - Ajayi (G League - Two-Way)",
    },
    ("CHA@LAL", "Boswell, Kylan"): {
        "game": "CHA@LAC", "team": "Charlotte Hornets", "opp": "LA CLIPPERS",
        "designation": "inactive",
        "printed": "Inactive: Hornets - Boswell (G League - Two-Way)",
    },
    ("CHA@LAL", "Knueppel, Kon"): {
        "game": "CHA@LAC", "team": "Charlotte Hornets", "opp": "LA CLIPPERS",
        "designation": "inactive",
        "printed": "Inactive: Hornets - Knueppel (Injury/Illness - Left Hamstring Strain)",
    },
    ("CHA@LAL", "Schroder, Dennis"): {
        "game": "CHA@LAC", "team": "Charlotte Hornets", "opp": "LA CLIPPERS",
        "designation": "inactive",
        "printed": "Inactive: Hornets - Schröder (Injury/Illness - Left Hamstring Strain)",
    },
    ("CHA@LAL", "Steinbach, Hannes"): {
        "game": "CHA@LAC", "team": "Charlotte Hornets", "opp": "LA CLIPPERS",
        "designation": "inactive",
        "printed": "Inactive: Hornets - Steinbach (G League - On Assignment)",
    },
    # --- Los Angeles Lakers players (CHA@LAL report block), observed in LAL@PHX ---
    ("CHA@LAL", "Grimes, Quentin"): {
        "game": "LAL@PHX", "team": "Los Angeles Lakers", "opp": "PHOENIX SUNS",
        "designation": "played",
        "min": "37:26", "pts": "22", "reb": "6", "ast": "1",
        "line": "5 Quentin Grimes | G | 37:26 | 7-10 FG | 5-6 3P | 3-4 FT | 2 OR | 4 DR | 6 TOT | 1 A | 22 PTS",
    },
    ("CHA@LAL", "Kessler, Walker"): {
        "game": "LAL@PHX", "team": "Los Angeles Lakers", "opp": "PHOENIX SUNS",
        "designation": "played",
        "min": "32:26", "pts": "14", "reb": "12", "ast": "3",
        "line": "14 Walker Kessler | C | 32:26 | 4-5 FG | 0-0 3P | 6-6 FT | 6 OR | 6 DR | 12 TOT | 3 A | 14 PTS",
    },
    ("CHA@LAL", "Reaves, Austin"): {
        "game": "LAL@PHX", "team": "Los Angeles Lakers", "opp": "PHOENIX SUNS",
        "designation": "inactive",
        "printed": "Inactive: Lakers - Reaves (Injury/Illness - Left Heel Contusion / Bone Bruise)",
        "attribution": (
            "the injury report row lost its team cell at a PDF page break and stays "
            "blank there; this game-log row's team comes from the gamebook's own team "
            "header, which prints the player on the Lakers inactive list"
        ),
    },
}


def main() -> int:
    injury = json.loads((SNAPSHOTS / INJURY).read_text(encoding="utf-8"))
    players: list[dict] = []
    counts = {"played": 0, "inactive": 0, "dnp": 0, "dnd": 0}
    game_rows = 0

    for game in injury["games"]:
        matchup = game["matchup"]
        for row in game["rows"]:
            name = row.get("player")
            if not name:
                continue
            key = (matchup, name)
            obs = OBS.get(key)
            if obs is None:
                raise SystemExit(f"no gamebook observation transcribed for {key}")
            g = GAMES[obs["game"]]
            entry: dict = {
                "report_name": name,
                "report_team_cell": row["team"],
                "report_team": None if row["team"] == "__lost__" else row["team"],
                "report_status": row["status"],
                "report_reason": row["reason"],
                "report_block": matchup,
                "games": [
                    {
                        "date": g["date"],
                        "game_id": g["game_id"],
                        "team_printed_in_book": obs["team"],
                        "opponent": obs["opp"],
                        "designation": obs["designation"],
                        "source_url": g["url"],
                        "source_label": g["label"],
                        "min_printed": obs.get("min"),
                        "pts_printed": obs.get("pts"),
                        "reb_printed": obs.get("reb"),
                        "ast_printed": obs.get("ast"),
                        **(
                            {"line_printed": obs["line"]}
                            if obs["designation"] == "played"
                            else {"designation_printed": obs["printed"]}
                        ),
                        **(
                            {"attribution_note": obs["attribution"]}
                            if obs.get("attribution")
                            else {}
                        ),
                    }
                ],
            }
            if row["team"] == "__lost__":
                entry["report_team_flag"] = (
                    "team cell not printed on this row (PDF page break); "
                    "no value was inferred"
                )
            players.append(entry)
            counts[obs["designation"]] += 1
            game_rows += 1

    covered = {(p["report_block"], p["report_name"]) for p in players}
    if len(covered) != len(players):
        raise SystemExit("duplicate (block, name) in capture")
    if set(OBS) != covered:
        raise SystemExit(f"OBS/roster mismatch: {set(OBS) ^ covered}")
    if len(players) != 33:
        raise SystemExit(f"expected 33 named report players, got {len(players)}")
    if counts != {"played": 5, "inactive": 27, "dnp": 0, "dnd": 1}:
        raise SystemExit(f"unexpected counts: {counts}")

    data = {
        "schema": "player-gamelogs-1",
        "snapshot_id": "player-gamelogs-2026-11-14_to_2026-11-15-anchor-2026-11-17",
        "kind": "per-player game log capture (dated attributed observations)",
        "source_url": REPORT_URL,
        "source_document_header": (
            f"{REPORT_HEADER} (roster anchor) + five official NBA gamebooks: "
            "2026-11-14 DET@MIA and 2026-11-15 LAL@PHX, CHA@LAC, SAS@UTA, NYK@TOR "
            "- each game-log row cites its own gamebook in source_url/source_label"
        ),
        "source_index_url": "https://official.nba.com/nba-injury-report-2026-27-season/",
        "fetched_at_utc": "2026-11-17T16:40:00Z",
        "extraction_tool": (
            "manual verbatim transcription from gamebook PDF chunk text; verified by "
            "scripts/build_gamelogs.py (mirror check against the injury file of record)"
        ),
        "observation_window": {"from_date": "2026-11-14", "to_date": "2026-11-15"},
        "generated_at_utc": "2026-11-17T16:45:00Z",
        "purpose": (
            "One dated, attributed observation row per player per game in the window, "
            "captured verbatim from the official gamebooks (played lines or the printed "
            "inactive/DND designation), covering every named player on the current injury "
            "file of record. These rows are evidence observations with row-level official "
            "links, NOT betting inputs: no projection, availability probability, minutes "
            "model or pick is derived from them (rights gate G0 and stances D-01/IR-T4 "
            "stand)."
        ),
        "injury_report": {
            "file": INJURY,
            "revision_label": f"{REPORT_HEADER} ET",
            "source_url": REPORT_URL,
            "players_listed": len(players),
        },
        "games_read": [
            {
                "date": GAMES[k]["date"],
                "matchup": k,
                "game_id": GAMES[k]["game_id"],
                "source_url": GAMES[k]["url"],
                "source_label": GAMES[k]["label"],
            }
            for k in ("DET@MIA", "LAL@PHX", "CHA@LAC", "SAS@UTA", "NYK@TOR")
        ],
        "games_read_note": (
            "chunk 0 of each gamebook prints both teams' full-game box score and the "
            "inactive lists; every captured value comes from that chunk read on "
            "2026-11-17. Window choice: Detroit's most recent game is 2026-11-14; the "
            "other six report teams last played on 2026-11-15; none of the 33 players' "
            "teams played on 2026-11-16 (the eight 11/16 finals carry no current-report "
            "team), so no 11/16 gamebook is needed."
        ),
        "counts": {
            "players": len(players),
            "game_rows": game_rows,
            **counts,
            "window_gap_players": 0,
            "games_read": len(GAMES),
            "players_with_a_game_in_window": len(players),
        },
        "refusals": [],
        "extraction_notes": [
            "report_status/report_reason/report_team are mirrored from "
            "data/snapshots/injuries-2026-11-17-1030am.json by (report_block, "
            "report_name) join at build time and were re-verified against it row for "
            "row (33/33); they are the report's printed cells, not this file's "
            "observations.",
            "Verbatim rule: a player with a game in the window appears either with a "
            "printed stat line (MIN/PTS/REB/AST as printed strings; REB is the printed "
            "TOT column, AST the printed A column) or with the printed designation "
            "(Inactive list entry, DNP - Coach's Decision, DND - ...). No value was "
            "computed or inferred.",
            "Every row cites its own gamebook URL in source_url; game_id values were "
            "verified on the official nba.com games pages (lal-vs-phx-0022600237, "
            "cha-vs-lac-0022600238, sas-vs-uta-0022600239, nyk-vs-tor-0022600241 read "
            "2026-11-17) and det-vs-mia-0022600233 from results-2026-11-14.json "
            "(official game page recorded there on 2026-11-15).",
            "Name matching between the report's 'Last, First' print and the gamebook's "
            "'First Last' print is by exact name tokens; suffixes (Jr., II) and "
            "diacritics are kept as printed on both sides. Designation spellings that "
            "differ from the report are kept as printed in designation_printed and are "
            "never merged into the mirrored report cells: the gamebook prints "
            "'Schröder', 'Nurkić' and 'Niederhäuser' where the report prints 'Schroder', "
            "'Nurkic' and 'Niederhauser', and the gamebook's Nurkić entry reads 'Right "
            "2nd Plantar Plate Tear' where the report row reads 'Right Right Foot; 2nd "
            "Plantar Plate Tear'.",
            "The Lakers inactive-list entry for Reaves wraps across a line break in the "
            "PDF text ('... Left Heel Contusion / Bone' / 'Bruise)'); the two fragments "
            "are joined with one space to reproduce the single printed entry. No other "
            "cell is altered.",
            "One report row (Reaves, Austin, CHA@LAL) lost its team cell at a PDF page "
            "break; it keeps a blank team in the injury snapshot and here "
            "(report_team null + report_team_flag), with the observed team attributed "
            "from the gamebook's own team header (attribution_note). This does not "
            "repair the injury row.",
            "No availability probability, minute estimate or production impact is "
            "stored here or derived from these rows.",
        ],
        "players": players,
    }

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}: {len(players)} players, {game_rows} game rows, {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
