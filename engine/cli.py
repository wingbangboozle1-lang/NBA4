"""Command line interface for the NBA4 engine.

    python3 -m engine.cli status
    python3 -m engine.cli validate
    python3 -m engine.cli generate --days 3 [--ledger DIR] [--out picks.jsonl]
    python3 -m engine.cli refresh [--observations FILE] [--now ISO8601]
    python3 -m engine.cli teamstats --pages FILE [--json]
    python3 -m engine.cli playerlogs --logs FILE [--roster p1,p2] [--json]
    python3 -m engine.cli modules
    python3 -m engine.cli surfaces
    python3 -m engine.cli selftest

`status` and `generate` read the authorized-inputs ledger (default
data/ledger, which ships empty). With the current repository state the
honest output is "no authorized inputs -> NO PICK", which is exactly what
the site's slate page shows. `selftest` runs the engine end-to-end on
clearly labelled SYNTHETIC fixtures and prints to stdout only - it never
writes into the site or the picks ledger.

Exit codes are part of the contract: **every subcommand that evaluates a gate
exits non-zero when the gate blocks.** A scheduled job must not be able to
mistake a refusal for an empty result, so a blocked refresh, an incomplete
team-stat read, a missing player log and an un-importable module each produce
exit code 1 with the reason printed last.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone

from . import ENGINE_VERSION, MODEL_VERSION
from .ledger import integrity_report, load_ledger
from .picks import generate_slate_picks
from .gates import run_gates

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_USAGE = 2


def _iso(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"error: {field_name} is not ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise SystemExit(f"error: {field_name} must carry a UTC offset: {value!r}")
    return parsed.astimezone(timezone.utc)


def cmd_status(args: argparse.Namespace) -> int:
    ledger = load_ledger(args.ledger)
    report = integrity_report(ledger, args.ledger)
    print(f"NBA4 engine {ENGINE_VERSION} (model {MODEL_VERSION})")
    print(f"ledger directory : {args.ledger}")
    print(f"records loaded   : {report.loaded}")
    print(f"records rejected : {report.rejected}")
    print(f"missing files    : {', '.join(report.missing_files) or 'none'}")
    for note in report.notes:
        print(f"note             : {note}")
    if ledger.is_empty:
        print("state            : NO AUTHORIZED INPUTS -> no lines, no picks")
        print("next step        : clear data rights (Q1/F-01), then load an")
        print("                   authorized ledger (docs/engine.md 'Inputs')")
    return EXIT_OK


def cmd_validate(args: argparse.Namespace) -> int:
    ledger = load_ledger(args.ledger)
    report = integrity_report(ledger, args.ledger)
    states = run_gates(report, has_market_spec=bool(ledger.quotes), n_settled_forecasts=0)
    print(f"NBA4 gate report ({datetime.now(timezone.utc).isoformat()})")
    for s in states:
        print(f"{s.gate:<28} {s.state:<8} {s.detail}")
    return EXIT_OK


def cmd_generate(args: argparse.Namespace) -> int:
    ledger = load_ledger(args.ledger)
    issued = datetime.now(timezone.utc)
    decisions, run_report = generate_slate_picks(
        ledger, issued_at=issued, horizon_hours=args.days * 24
    )
    lines = []
    for decision in decisions:
        for rec in decision.records:
            lines.append(json.dumps(rec.to_dict(), sort_keys=True))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + ("\n" if lines else ""))
    print(json.dumps(run_report, indent=2, sort_keys=True))
    print(f"forecast records : {len(lines)} (all statuses shown in --out file)")
    if not lines:
        print("no slate games within the horizon on an authorized feed -> "
              "nothing to forecast (NO PICK state)")
    return EXIT_OK


def cmd_selftest(args: argparse.Namespace) -> int:
    """End-to-end run on labelled SYNTHETIC fixtures (stdout only)."""
    from .selftest import run_selftest

    return run_selftest()


# --------------------------------------------------------------------------
# refresh: the scheduled-job gate. Refresh first, rebuild second.
# --------------------------------------------------------------------------

def cmd_refresh(args: argparse.Namespace) -> int:
    """Evaluate the declared feeds for one rolling slate.

    With no ``--observations`` file the answer is a refusal: the job is asked
    to refresh these feeds, so "nothing was retrieved" is a failed refresh and
    not a neutral state.
    """
    from . import refresh as refresh_mod

    now = _iso(args.now, "--now") if args.now else datetime.now(timezone.utc)
    specs = refresh_mod.default_feed_specs()
    observations: dict[str, object] = {}
    if args.observations:
        payload = json.loads(_read(args.observations))
        rows = payload.get("observations", payload if isinstance(payload, list) else [])
        for row in rows:
            observations[row["feed_id"]] = refresh_mod.FeedObservation(
                feed_id=row["feed_id"],
                url=row["url"],
                retrieved_at=_iso(row["retrieved_at"], f"{row['feed_id']}.retrieved_at"),
                document_timestamp=(
                    _iso(row["document_timestamp"], f"{row['feed_id']}.document_timestamp")
                    if row.get("document_timestamp")
                    else None
                ),
                rows_read=row.get("rows_read"),
                chunks_read=row.get("chunks_read"),
                allowed_use=bool(row.get("allowed_use", False)),
                note=row.get("note", ""),
            )

    decision = refresh_mod.refresh_decision(specs, observations, now, args.horizon)
    window = decision.window
    print(f"rolling window   : {window.start.isoformat()} .. {window.end.isoformat()} "
          f"({window.horizon_hours}h)")
    print(f"{'feed':<24} {'state':<26} {'age':>10}  basis / detail")
    for verdict in decision.verdicts:
        age = "-" if verdict.age_minutes is None else f"{verdict.age_minutes:.1f}m"
        print(f"{verdict.feed_id:<24} {verdict.state.value:<26} {age:>10}  {verdict.detail}")
    for warning in decision.warnings:
        print(f"warning          : {warning}")
    if decision.may_rebuild:
        print("decision         : REBUILD - every required feed passed its gate")
        return EXIT_OK
    print("decision         : NO REBUILD - the slate is not rebuilt on a failed refresh")
    for reason in decision.blocking_reasons:
        print(f"blocked by       : {reason}")
    return EXIT_BLOCKED


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


# --------------------------------------------------------------------------
# teamstats: the three official team-stat pages, read complete, then re-cut.
# --------------------------------------------------------------------------

def cmd_teamstats(args: argparse.Namespace) -> int:
    from . import teamstats as ts

    payload = json.loads(_read(args.pages))
    retrieved = _iso(payload.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                     "retrieved_at")

    def read(name: str, rows: list[dict]) -> "object":
        page = ts.StatPage(name)
        return ts.PageRead(
            page=page,
            rows=tuple(ts.row_from_dict(page, row) for row in rows),
            source_url=payload.get(f"{name}_url", page.url),
            retrieved_at=retrieved,
            chunks_read=int(payload.get(f"{name}_chunks_read", 1)),
            chunks_total=int(payload.get(f"{name}_chunks_total", 1)),
            rows_expected=int(payload.get(f"{name}_rows_expected", ts.TEAMS_EXPECTED)),
        )

    try:
        table = ts.recut(
            read("traditional", payload["traditional"]),
            read("opponent", payload["opponent"]),
            read("advanced", payload["advanced"]),
        )
    except ts.TeamStatsError as exc:
        print(f"REFUSED          : {exc}")
        return EXIT_BLOCKED
    except Exception as exc:  # RightsError and contract failures are refusals too
        print(f"REFUSED          : {exc}")
        return EXIT_BLOCKED

    if args.json:
        print(json.dumps(table.summary(), indent=2, sort_keys=True))
    else:
        summary = table.summary()
        print(f"teams joined     : {summary['teams']} of {summary['teams_expected']}")
        print(f"league pace      : {summary['league_pace']}")
        print(f"league off PPP   : {summary['league_offensive_ppp']}")
        print(f"league def PPP   : {summary['league_defensive_ppp']}")
        for flag in summary["flags"]:
            print(f"flag             : {flag}")
        print(f"{'team':<26} {'pace':>7} {'poss':>8} {'offPPP':>8} {'defPPP':>8} checks")
        for entry in table.teams:
            ok = all(bool(check["agrees"]) for check in entry.checks.values())
            print(f"{entry.team:<26} {entry.pace:>7.2f} {entry.possessions_per_game:>8.2f} "
                  f"{entry.offensive_ppp:>8.4f} {entry.defensive_ppp:>8.4f} "
                  f"{'ok' if ok else 'DISAGREES'}")
    if table.flags:
        return EXIT_BLOCKED
    return EXIT_OK


# --------------------------------------------------------------------------
# playerlogs: capture, coverage and the tamper-evident hash.
# --------------------------------------------------------------------------

def cmd_playerlogs(args: argparse.Namespace) -> int:
    from . import playerlogs as pl
    from .contracts import Provenance

    payload = json.loads(_read(args.logs))
    book = pl.PlayerLogBook()
    for row in payload.get("logs", []):
        prov_raw = row["provenance"]
        book.add(
            pl.PlayerGameLog(
                player_id=row["player_id"],
                player_name=row.get("player_name", row["player_id"]),
                team_id=row["team_id"],
                opponent_team_id=row["opponent_team_id"],
                event_id=row["event_id"],
                game_date=row.get("game_date", ""),
                minutes=float(row["minutes"]),
                points=float(row["points"]),
                rebounds=float(row["rebounds"]),
                assists=float(row["assists"]),
                provenance=Provenance(
                    source_id=prov_raw["source_id"],
                    source_name=prov_raw["source_name"],
                    source_url=prov_raw["source_url"],
                    source_timestamp=_iso(prov_raw["source_timestamp"], "source_timestamp"),
                    observed_at=_iso(prov_raw["observed_at"], "observed_at"),
                    version=prov_raw["version"],
                    allowed_use=bool(prov_raw.get("allowed_use", False)),
                    allowed_use_note=prov_raw.get("allowed_use_note", ""),
                ),
                overtime_periods=int(row.get("overtime_periods", 0)),
            )
        )

    roster = [item.strip() for item in args.roster.split(",") if item.strip()] if args.roster \
        else list(payload.get("roster", []))
    summary = book.summary()
    if args.json:
        print(json.dumps({"summary": summary, "coverage": book.coverage(roster).as_dict()},
                         indent=2, sort_keys=True))
    else:
        print(f"log rows         : {summary['log_rows']}")
        print(f"distinct players : {summary['distinct_players']}")
        print(f"distinct games   : {summary['distinct_games']}")
        print(f"corroborated     : {summary['corroborated_rows']}")
        print(f"uncleared rows   : {summary['uncleared_rows']}")
        print(f"canonical hash   : {summary['canonical_hash']}")
        if roster:
            report = book.coverage(roster)
            print(f"roster           : {report.as_dict()['coverage_fraction']} covered "
                  f"({len(report.captured)} of {len(report.roster)})")
            for player in report.missing:
                print(f"missing          : {player} ({pl.LOG_MISSING}: not inferred, not zero)")
            for player in report.uncleared:
                print(f"uncleared        : {player}")
    if roster:
        report = book.coverage(roster)
        if report.missing or report.uncleared:
            return EXIT_BLOCKED
    return EXIT_OK


# --------------------------------------------------------------------------
# modules: import-audit of every engine module and the refusal codes it declares.
# --------------------------------------------------------------------------

def cmd_modules(args: argparse.Namespace) -> int:
    """Import every engine module and print the refusal constants it declares.

    A module that cannot be imported is a broken gate, so the subcommand exits
    non-zero. The refusal constants are the module-level names that look like
    refusals; they are printed so an operator can see, without reading code,
    what each module refuses to invent.
    """
    from . import __all__ as module_names

    # Names, not values: a module declares a refusal by naming a state it will
    # not invent a value for (for example venues.TRAVEL_NO_SOURCE).
    tokens = ("_NO_", "NO_SOURCE", "REFUS", "MISSING", "UNVERIFIED", "BLOCKED",
              "UNCLEARED", "NOT_", "INCOMPLETE", "STALE")

    def scan(namespace: dict, prefix: str = "") -> list[str]:
        found = []
        for attr, value in namespace.items():
            if not attr.isupper() or not isinstance(value, str):
                continue
            if any(token in attr for token in tokens):
                found.append(f"{prefix}{attr}={getattr(value, 'value', value)}")
        return found

    def refusals_of(module: object) -> list[str]:
        found = scan(vars(module))
        # State enums and constant classes hold their refusals one level down
        # (for example refresh.FeedState.NOT_RETRIEVED), so scan those too.
        for attr, value in vars(module).items():
            if attr.startswith("_") or not isinstance(value, type):
                continue
            if value.__module__ != module.__name__:
                continue
            found.extend(scan(vars(value), prefix=f"{attr}."))
        return sorted(set(found))

    failures: list[str] = []
    collected: list[dict[str, object]] = []
    if not args.json:
        print(f"{'module':<22} {'refusals':<9}  detail")
    for name in module_names:
        try:
            module = importlib.import_module(f"engine.{name}")
        except Exception as exc:  # noqa: BLE001 - the point is to report the failure
            failures.append(f"{name}: {exc}")
            if not args.json:
                print(f"{name:<22} {'IMPORT FAILED':<9}  {exc}")
            continue
        refusals = refusals_of(module)
        collected.append({"module": name, "refusals": refusals})
        if args.json:
            continue
        preview = ", ".join(refusals[:3]) + (" ..." if len(refusals) > 3 else "")
        print(f"{name:<22} {len(refusals):<9}  {preview}")
    if args.json:
        print(json.dumps(collected, indent=2, sort_keys=True))
    if failures:
        print(f"\n{len(failures)} module(s) failed to import:")
        for failure in failures:
            print(f"- {failure}")
        return EXIT_BLOCKED
    print(f"\n{len(module_names)} modules imported cleanly.")
    return EXIT_OK


def cmd_surfaces(args: argparse.Namespace) -> int:
    """Print the projection/bet surface split and what is gated today."""
    from . import surfaces

    summary = surfaces.surface_summary()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m engine.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="ledger and pipeline state")
    p.add_argument("--ledger", default="data/ledger")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("validate", help="run the machine-checkable gates")
    p.add_argument("--ledger", default="data/ledger")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("generate", help="generate slate forecast records")
    p.add_argument("--ledger", default="data/ledger")
    p.add_argument("--days", type=int, default=3, choices=(1, 2, 3))
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser(
        "refresh",
        help="gate the rolling slate's official feeds before a rebuild (exit 1 when blocked)",
    )
    p.add_argument(
        "--observations",
        default=None,
        help="JSON file of feed observations (see docs/engine.md for the schema)",
    )
    p.add_argument("--now", default=None, help="run timestamp (ISO 8601, timezone aware)")
    p.add_argument("--horizon", type=int, default=72, help="slate horizon in hours (1..72)")
    p.set_defaults(func=cmd_refresh)

    p = sub.add_parser(
        "teamstats",
        help="re-cut the three official team-stat pages (exit 1 when a read is incomplete)",
    )
    p.add_argument("--pages", required=True, help="JSON file of the three page reads")
    p.add_argument("--json", action="store_true", help="print the summary as JSON")
    p.set_defaults(func=cmd_teamstats)

    p = sub.add_parser(
        "playerlogs",
        help="capture per-player game logs and report coverage (exit 1 on a gap)",
    )
    p.add_argument("--logs", required=True, help="JSON file of player game logs")
    p.add_argument("--roster", default=None, help="comma-separated roster to check coverage for")
    p.add_argument("--json", action="store_true", help="print the report as JSON")
    p.set_defaults(func=cmd_playerlogs)

    p = sub.add_parser("modules", help="import-audit of every engine module")
    p.add_argument("--json", action="store_true", help="print one JSON object per module")
    p.set_defaults(func=cmd_modules)

    p = sub.add_parser("surfaces", help="the projection/bet surface split")
    p.set_defaults(func=cmd_surfaces)

    p = sub.add_parser("selftest", help="synthetic-fixture mechanics demo")
    p.set_defaults(func=cmd_selftest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
