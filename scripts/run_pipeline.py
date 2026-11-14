#!/usr/bin/env python3
"""Run one NBA4 pipeline cycle and write an auditable report.

Usage:

    python3 scripts/run_pipeline.py --inputs data/inbox --out data/out --now 2026-11-14T12:00:00Z

The inputs directory may contain:

* ``schedule.json`` - list of game events
* ``injuries.json``  - list of injury status records
* ``quotes.json``    - list of licensed market quotes

Every record must carry the provenance fields required by
``engine.contracts``. Records whose ``allowed_use`` flag is not set are
refused: the run then produces a report with no forecasts and no picks, which
is the correct behaviour until the data rights are cleared.

The script never contacts the network and never writes to the published site.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.contracts import (  # noqa: E402
    ContractError,
    GameEvent,
    InjuryRecord,
    MarketQuote,
    Provenance,
    Status,
)
from engine.pipeline import RunConfig, append_ledger, run_pipeline, write_ledger  # noqa: E402

LEDGER_NAME = "ledger.jsonl"
REPORT_NAME = "run-report.json"


def _provenance(payload: dict) -> Provenance:
    return Provenance(
        source_id=payload["source_id"],
        source_name=payload["source_name"],
        source_url=payload["source_url"],
        source_timestamp=datetime.fromisoformat(payload["source_timestamp"]),
        observed_at=datetime.fromisoformat(payload["observed_at"]),
        version=payload["version"],
        allowed_use=bool(payload.get("allowed_use", False)),
        allowed_use_note=payload.get("allowed_use_note", ""),
    )


def _load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("records", [])
    if not isinstance(data, list):
        raise ContractError(f"{path} must contain a JSON list of records")
    return data


def _events(records: list[dict]) -> list[GameEvent]:
    return [
        GameEvent(
            event_id=record["event_id"],
            tipoff_utc=datetime.fromisoformat(record["tipoff_utc"]),
            home_team_id=record["home_team_id"],
            away_team_id=record["away_team_id"],
            provenance=_provenance(record["provenance"]),
        )
        for record in records
    ]


def _injuries(records: list[dict]) -> list[InjuryRecord]:
    return [
        InjuryRecord(
            event_id=record["event_id"],
            player_id=record["player_id"],
            status=Status(record["status"]),
            reason=record.get("reason", ""),
            provenance=_provenance(record["provenance"]),
        )
        for record in records
    ]


def _quotes(records: list[dict]) -> list[MarketQuote]:
    return [
        MarketQuote(
            market_id=record["market_id"],
            event_id=record["event_id"],
            market_type=record["market_type"],
            side=record["side"],
            line=record.get("line"),
            price_decimal=record["price_decimal"],
            quote_timestamp=datetime.fromisoformat(record["quote_timestamp"]),
            provider_id=record["provider_id"],
            provenance=_provenance(record["provenance"]),
        )
        for record in records
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one NBA4 pipeline cycle.")
    parser.add_argument("--inputs", default="data/inbox", help="directory with input JSON files")
    parser.add_argument("--out", default="data/out", help="directory for the run artefacts")
    parser.add_argument(
        "--now",
        default=datetime.now(timezone.utc).isoformat(),
        help="run timestamp (ISO 8601, timezone aware)",
    )
    parser.add_argument("--run-id", default="run", help="identifier for this run")
    parser.add_argument(
        "--market-specified",
        action="store_true",
        help="declare that the market and settlement rules are written down",
    )
    parser.add_argument(
        "--model-version",
        default="",
        help="identifier of the frozen model version used for this run",
    )
    args = parser.parse_args(argv)

    now = datetime.fromisoformat(args.now)
    if now.tzinfo is None:
        print("error: --now must include a timezone offset", file=sys.stderr)
        return 2

    inputs = Path(args.inputs)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    config = RunConfig(
        run_id=args.run_id,
        now_utc=now,
        market_specified=args.market_specified,
        model_version=args.model_version,
    )

    report = run_pipeline(
        config=config,
        events=_events(_load(inputs / "schedule.json")),
        injuries=_injuries(_load(inputs / "injuries.json")),
        quotes=_quotes(_load(inputs / "quotes.json")),
    )

    write_ledger(str(out / REPORT_NAME), report.as_dict())
    append_ledger(str(out / LEDGER_NAME), report.as_dict())

    print(f"run id           : {report.run_id}")
    print(f"horizon          : {report.horizon_start.isoformat()} .. {report.horizon_end.isoformat()}")
    print(f"slate events     : {len(report.slate_event_ids)}")
    print(f"rights cleared   : {report.rights_cleared}")
    print(f"stale inputs     : {len(report.stale_inputs)}")
    print(f"forecasts        : {len(report.forecasts)}")
    print(f"picks (bet)      : {sum(1 for p in report.picks if p['decision'] == 'bet')}")
    print(f"picks (no bet)   : {sum(1 for p in report.picks if p['decision'] == 'no_bet')}")
    print(f"report written   : {out / REPORT_NAME}")
    print(f"ledger appended  : {out / LEDGER_NAME} (append-only JSON Lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
