# reported-segment-parser-layout-expansion-v1 Review

## Review Summary

- Accepted. The task correctly avoids fabricating segment rows for ADI. It classifies ADI as a single reportable segment case and preserves AAPL trend-backed segment evidence.

## Issues Found

- First EC2 smoke showed ADI skipped candidates leaking into AAPL `segment_parser_skip_reasons` because coverage override keyed reasons by target report symbol instead of skipped candidate symbol.
- Fixed in commit `0bec5bd`: skip reasons are now grouped by `skipped.primary_symbol`, with target symbol only as a fallback.

## Residual Risks

- Broader active symbol coverage is still incomplete; true unsupported layouts may appear after running more than the AAPL/ADI target set.
- Single reportable segment issuers need different valuation treatment from multi-segment SOTP evidence.

## Verification Evidence

- Local focused tests passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_segment_history_coverage_expansion` (`Ran 41 tests`, `OK`).
- Local regression passed: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_segment_history_coverage_expansion tests.test_segment_history_backfill tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_operating_data_orchestrator` (`Ran 131 tests`, `OK`).
- Local compileall, roadmap verification, AWH verification, and `git diff --check` passed.
- EC2 focused tests passed after deploy.
- EC2 coverage run `run_id=1165` produced AAPL `trend_backed` and ADI `single_reportable_segment_no_disaggregated_segment_table`; `unsupported_layout_count=0`.
