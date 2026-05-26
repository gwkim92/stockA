# segment-history-coverage-expansion-v1 Handoff

## Status

- completed: backend coverage runner, CLI command, target resolution, coverage status report, CIK-based source linkage fix, local unit/CLI tests, EC2 deployment, and EC2 smoke are complete.

## Context

- `segment-history-backfill-v1` proved the path on AAPL and fixed parser pollution from total/tax tables.
- Current EC2 proof: AAPL has 4 annual reported segment periods, 5 clean geographic segment labels per period, `bad_segment_count=0`, and SOTP assumptions use `multi_period_segment_trend_template`.

## Exact Next Step

- exact next step: start `reported-segment-parser-layout-expansion-v1` to add parser support for the non-AAPL SEC segment table layouts surfaced by ADI, without weakening the existing AAPL bad-label filters.

## Implemented

- Added `stockanalysis.operations.segment_history_coverage_expansion`.
- Added CLI: `stockanalysis-operations segment-history-coverage-expansion-run`.
- Target source: active recommendations plus latest `Long Term Paper` portfolio holdings.
- CIK resolution: SEC `company_tickers_exchange` via existing market universe adapter.
- Coverage report fields include parsed period count, parsed segment count, unsupported candidate count, single-period fallback flag, bad segment count, trend-backed assumption count, and coverage status.
- `financial_period_source_linkage` now uses normalized CIK to match SEC source documents by accession prefix when CIK is provided, instead of relying only on company-name text in SEC document title/summary.
- Guardrails remain explicit: `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_segment_history_coverage_expansion tests.test_segment_history_backfill tests.test_data_operations_cli` (`Ran 83 tests`, `OK`).
- Passed after CIK source-linkage fix: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_segment_history_coverage_expansion tests.test_segment_history_backfill tests.test_data_operations_cli` (`Ran 89 tests`, `OK`).
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "segment-history-coverage-expansion-run|segment-history-backfill-run"`.
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`.
- EC2 deployed commit `f94502c`; `tests.test_financial_period_source_linkage` and `tests.test_segment_history_coverage_expansion` passed on EC2 (`Ran 10 tests`, `OK`).
- EC2 dry-run artifact: `/opt/stockanalysis/runtime/artifacts/segment-history-coverage-dry-run.json`; selected targets were AAPL and ADI.
- EC2 execute artifact after CIK source-linkage fix and `max_filings=200`: `/opt/stockanalysis/runtime/artifacts/segment-history-coverage-execute-cik-200.json`.
- EC2 execute parent `run_id=1134`; AAPL child `run_id=1135`, parser `run_id=1139`; ADI child `run_id=1142`, source linkage `run_id=1143`, parser `run_id=1147`.
- EC2 coverage summary: `trend_backed_count=1`, `unsupported_layout_count=1`, `single_period_fallback_count=0`, `contaminated_segment_label_count=0`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`.
- EC2 AAPL evidence: `coverage_status=trend_backed`, `parsed_period_count=4`, `parsed_segment_count=5`, `bad_segment_count=0`, `trend_backed_assumption_count=5`.
- EC2 ADI evidence: `coverage_status=unsupported_layout`, `source_document_period_count=3`, `raw_document_period_count=3`, `parsed_period_count=0`, `unsupported_candidate_count=3`; this proves the next bottleneck is parser layout coverage, not missing source documents.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not add shell-only orchestration when a backend CLI/service boundary is appropriate.

## Remaining Risks

- Some active holdings such as ETFs may not have useful operating segment filings even when they resolve through `company_tickers_exchange`; these must be reported as explicit quality gaps rather than treated as successful coverage.
- Non-AAPL issuer segment footnote layouts remain unsupported in at least one active target (`ADI`); the next parser task should use the raw SEC artifacts fetched by this run as fixtures/evidence.
