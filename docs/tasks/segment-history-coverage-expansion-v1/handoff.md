# segment-history-coverage-expansion-v1 Handoff

## Status

- in progress: backend coverage runner, CLI command, target resolution, coverage status report, and local unit/CLI tests are implemented. EC2 deployment/smoke and final roadmap evidence are pending.

## Context

- `segment-history-backfill-v1` proved the path on AAPL and fixed parser pollution from total/tax tables.
- Current EC2 proof: AAPL has 4 annual reported segment periods, 5 clean geographic segment labels per period, `bad_segment_count=0`, and SOTP assumptions use `multi_period_segment_trend_template`.

## Exact Next Step

- Deploy the new runner to EC2 and execute `segment-history-coverage-expansion-run --execute` with a small target set that includes AAPL and at least one non-AAPL active symbol.

## Implemented

- Added `stockanalysis.operations.segment_history_coverage_expansion`.
- Added CLI: `stockanalysis-operations segment-history-coverage-expansion-run`.
- Target source: active recommendations plus latest `Long Term Paper` portfolio holdings.
- CIK resolution: SEC `company_tickers_exchange` via existing market universe adapter.
- Coverage report fields include parsed period count, parsed segment count, unsupported candidate count, single-period fallback flag, bad segment count, trend-backed assumption count, and coverage status.
- Guardrails remain explicit: `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_segment_history_coverage_expansion tests.test_segment_history_backfill tests.test_data_operations_cli` (`Ran 83 tests`, `OK`).
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "segment-history-coverage-expansion-run|segment-history-backfill-run"`.
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not add shell-only orchestration when a backend CLI/service boundary is appropriate.

## Remaining Risks

- EC2 SQL/runtime smoke is still pending.
- Some active holdings such as ETFs may not resolve to SEC company CIKs through `company_tickers_exchange`; these must be reported as unmatched rather than treated as failures.
- Non-AAPL issuer segment footnote layouts may remain unsupported; the runner should surface those as `unsupported_layout` or related coverage statuses.
