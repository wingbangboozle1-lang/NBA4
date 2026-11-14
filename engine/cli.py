"""Command line interface for the NBA4 engine.

    python3 -m engine.cli status
    python3 -m engine.cli validate
    python3 -m engine.cli generate --days 3 [--ledger DIR] [--out picks.jsonl]
    python3 -m engine.cli selftest

`status` and `generate` read the authorized-inputs ledger (default
data/ledger, which ships empty). With the current repository state the
honest output is "no authorized inputs -> NO PICK", which is exactly what
the site's slate page shows. `selftest` runs the engine end-to-end on
clearly labelled SYNTHETIC fixtures and prints to stdout only - it never
writes into the site or the picks ledger.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from . import ENGINE_VERSION, MODEL_VERSION
from .ledger import integrity_report, load_ledger
from .picks import generate_slate_picks
from .gates import run_gates


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
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    ledger = load_ledger(args.ledger)
    report = integrity_report(ledger, args.ledger)
    states = run_gates(report, has_market_spec=bool(ledger.quotes), n_settled_forecasts=0)
    print(f"NBA4 gate report ({datetime.now(timezone.utc).isoformat()})")
    for s in states:
        print(f"{s.gate:<28} {s.state:<8} {s.detail}")
    return 0


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
    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    """End-to-end run on labelled SYNTHETIC fixtures (stdout only)."""
    from .selftest import run_selftest

    return run_selftest()


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

    p = sub.add_parser("selftest", help="synthetic-fixture mechanics demo")
    p.set_defaults(func=cmd_selftest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
