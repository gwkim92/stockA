# reported-segment-parser-quality-v1 Handoff

## Status

- in progress: root cause analysis, fixture, parser expansion, local verification, roadmap verification, harness verification, and Python 3.13 full suite are complete.
- remaining: GitHub push, EC2 deploy, and EC2 parser smoke.

## Current Findings

- EC2 Apple 10-K raw artifact exists at `/opt/stockanalysis/runtime/artifacts/raw/sec/filings/0000320193-25-000079/aapl-20250927.htm`.
- The current parser failed because Apple's segment footnote table is transposed: the year row is followed by segment names as columns, while `Net sales` and `Operating income/(loss)` are metric rows.
- A naive transposed parser can overparse year/change/date columns, so the implementation requires a singleton filing-year row before the segment header row and excludes `Corporate` and `Total`.

## Decisions

- Add deterministic support for the Apple-style transposed reportable segment layout.
- Parse `Net sales` as `segment_revenue` and `Operating income/(loss)` as `segment_operating_income`.
- Keep values as reported and keep metric unit conservative when the unit context is outside the table.
- Do not change SOTP valuation math, recommendation scores, score weights, benchmark splits, or broker/order flow.

## Exact Next Step

- exact next step: run roadmap/harness/full verification, commit and push, deploy to EC2, then rerun `reported-segment-footnote-parser-run --execute` to confirm `reported_segment_metric_count > 0`.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis` (`Ran 34 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 122 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task reported-segment-parser-quality-v1`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests in 5.243s`, `OK`)
- Passed: `git diff --check`
- Manual local parser check against copied EC2 Apple 10-K artifact returned 10 rows: Americas, Europe, Greater China, Japan, and Rest of Asia Pacific for revenue and operating income.

## Remaining Risks

- This is not a complete inline XBRL dimensional parser.
- The parser still targets conservative table shapes and may miss other issuers' custom segment layouts.
- Unit context can remain `USD_as_reported` when the "dollars in millions" phrase is outside the HTML table.
