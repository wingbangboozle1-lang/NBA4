# Example input directory (synthetic)

`schedule.json`, `injuries.json` and `quotes.json` in this folder are **synthetic
examples**. They exist so the pipeline can be smoke-tested:

```sh
python3 scripts/run_pipeline.py --inputs data/inbox-example --out data/out-example --now 2026-11-14T12:00:00Z
```

The example records deliberately carry `"allowed_use": false`, so the run is
suppressed by the rights gate and writes **no** forecast and **no** pick. That is
the expected behaviour, and it is the same behaviour the pipeline shows when a
real feed has not been cleared for the intended use.

Do not replace these files with NBA schedule, injury, statistics or market data
without the written permission described in `docs/decision-register.md` (Q1-Q2)
and `docs/source-verification.md`.
