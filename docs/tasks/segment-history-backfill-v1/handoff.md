# segment-history-backfill-v1 Handoff

## Status

- in progress: contract, plan, parser history mode, CLI, weekly profile changes, segment history backfill runner, focused tests, CLI help check, and compileall are complete. Roadmap/AWH verification, commit, EC2 deploy, and EC2 smoke are pending.

## Current Findings

- `reported-segment-footnote-parser-run` currently selects one period per instrument by default, so historical raw SEC filings are not parsed even when source linkage can find them.
- `segment-sotp-driver-calibration-v1` already has the downstream trend CTEs. The missing piece is historical reported segment rows in `research.segment_footnote_evidence`.

## Decisions

- Add bounded history parsing rather than unbounded full archive parsing.
- Keep all writes inside existing backend CLI/service boundaries.
- Keep recommendation weights, SOTP formulas, benchmark logic, portfolio guardrails, and broker/order flow unchanged.

## Exact Next Step

- exact next step: implement `periods_per_instrument` in the parser candidate SQL and add `segment-history-backfill-run` orchestration.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_segment_history_backfill tests.test_data_operations_cli tests.test_operating_data_orchestrator` (`Ran 117 tests`, `OK`).
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "segment-history-backfill-run|reported-segment-footnote-parser-run"`.
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`.

## Remaining Risks

- Older SEC filings may use a different segment table layout; parser coverage may still block some historical periods.
- SEC raw fetch depends on `STOCKANALYSIS_SEC_USER_AGENT` and SEC availability.
