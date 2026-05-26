# segment-history-coverage-expansion-v1 Review

## Review Summary

- Accepted. The task expands segment-history evidence from a single AAPL proof to active recommendation/portfolio coverage reporting. It also fixes financial period source linkage to use CIK-based SEC accession matching when CIK is available.

## Issues Found

- Initial EC2 run showed ADI stuck at `missing_source_document_linkage`; root cause was that source linkage accepted `cik` but did not use it in the matching SQL.
- Fixed in commit `f94502c`: SEC documents can now match by accession CIK prefix. With `max_filings=200`, ADI moved from missing linkage to `unsupported_layout`.

## Residual Risks

- ADI is now correctly surfaced as `unsupported_layout`, but no ADI segment metrics are parsed yet.
- Other issuers may need additional parser layouts beyond the current AAPL-style transposed and multiyear block parsers.
- ETF/holding-company style instruments may resolve through SEC but still not have useful operating segment footnotes.

## Verification Evidence

- Local: `PYTHONPATH=src python3 -m unittest tests.test_segment_history_coverage_expansion tests.test_segment_history_backfill tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_operating_data_orchestrator` ran `124` tests with `OK`.
- Local after CIK fix: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_segment_history_coverage_expansion tests.test_segment_history_backfill tests.test_data_operations_cli` ran `89` tests with `OK`.
- Local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- Local: `bash scripts/verify_project_execution_roadmap.sh` passed.
- EC2: commit `f94502c` deployed; FastAPI and Next services stayed `active`.
- EC2: `segment-history-coverage-expansion-run --execute --max-filings 200 --target-limit 2` completed with parent `run_id=1134`.
- EC2: AAPL remained `trend_backed`; ADI became `unsupported_layout` with 3 raw/source annual periods and 0 parsed segment periods.
