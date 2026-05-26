# financial-period-source-document-linkage-v1 Review

## Review Summary

- scope check: within bounds. The task adds source-document linkage and raw artifact availability around existing SEC ingest and parser flows.
- schema check: no migration is introduced; existing `market.financial_statement_period.source_document_id` and `ingest.source_document.raw_storage_uri` are used.
- scoring check: no recommendation score, score component weight, benchmark, or broker/order mutation is introduced.
- runtime check: the new step is inserted before the reported segment parser in weekly SEC/fundamental orchestration.

## Issues Found

- None found in the focused local verification pass.
- None found in the Python 3.13 full suite.
- EC2 first smoke found an operational default issue: `--max-filings 3` did not include 10-K/10-Q filings for Apple because recent submissions were Form 4/144. The fix keeps the normal SEC metadata step lightweight but makes source linkage use a bounded 200-filing lookback.

## Residual Risks

- EC2 smoke proved real SEC documents can be linked and raw-fetched in the deployed database.
- Parser coverage can remain low even after linkage if filings use complex inline XBRL or non-table segment disclosure formats.
- Broader all-symbol source linkage is not implemented in this slice; the runner is bounded by the configured CIK and run limits.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator` passed with `Ran 88 tests`.
- `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` passed with `Ran 970 tests`.
- `PYTHONPATH=src python3 -m compileall -q src tests`, CLI help grep, roadmap verification, AWH verify, and `git diff --check` passed.
- After correcting the source-linkage lookback, focused unittest, `compileall`, CLI help grep, roadmap verification, AWH verify, Python 3.13 full suite, and `git diff --check` all passed again.
- EC2 first smoke completed with `run_id=1039` but produced `linked_period_count=0` due to insufficient filing lookback.
- EC2 corrected smoke completed with `run_id=1042`, `filing_count=200`, `raw_fetch_candidate_count=1`, `raw_fetch_success_count=1`, and raw Apple 10-K artifact persisted under `/opt/stockanalysis/runtime/artifacts/raw/sec/filings/0000320193-25-000079/aapl-20250927.htm`.
- EC2 DB linkage check returned `linked_periods=29`, `raw_sec_docs=1`, `linked_raw_periods=2`, and `aapl_linked_periods=29`.
- EC2 parser follow-up completed with `run_id=1046`, `candidate_count=1`, `reported_segment_metric_count=0`, and `recommendation_scoring_mutated=false`.
