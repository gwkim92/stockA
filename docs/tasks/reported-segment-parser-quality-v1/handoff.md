# reported-segment-parser-quality-v1 Handoff

## Status

- completed: root cause analysis, fixture, parser expansion, local verification, roadmap verification, harness verification, Python 3.13 full suite, GitHub push, EC2 deploy, and EC2 parser smoke are complete.

## Current Findings

- EC2 Apple 10-K raw artifact exists at `/opt/stockanalysis/runtime/artifacts/raw/sec/filings/0000320193-25-000079/aapl-20250927.htm`.
- The current parser failed because Apple's segment footnote table is transposed: the year row is followed by segment names as columns, while `Net sales` and `Operating income/(loss)` are metric rows.
- A naive transposed parser can overparse year/change/date columns, so the implementation requires a singleton filing-year row before the segment header row and excludes `Corporate` and `Total`.
- First EC2 smoke after parser expansion produced metrics but revealed a period-quality issue: candidate selection chose a `shares_outstanding` point-in-time period (`2025-10-17`) over the fiscal statement period (`2025-09-27`). Candidate selection now prioritizes periods with revenue, operating income, or net income metrics, and upsert removes stale reported segment rows for the same source document when period alignment changes.

## Decisions

- Add deterministic support for the Apple-style transposed reportable segment layout.
- Parse `Net sales` as `segment_revenue` and `Operating income/(loss)` as `segment_operating_income`.
- Keep values as reported and keep metric unit conservative when the unit context is outside the table.
- Do not change SOTP valuation math, recommendation scores, score weights, benchmark splits, or broker/order flow.

## Exact Next Step

- exact next step: start `segment-level-sotp-inputs-v1` so the reported segment revenue and operating income evidence becomes explicit SOTP input/visibility without changing recommendation weights.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis` (`Ran 34 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 122 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task reported-segment-parser-quality-v1`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests in 5.243s`, `OK`)
- Passed: `git diff --check`
- Manual local parser check against copied EC2 Apple 10-K artifact returned 10 rows: Americas, Europe, Greater China, Japan, and Rest of Asia Pacific for revenue and operating income.
- Re-passed after statement-period candidate correction: professional analysis test (`Ran 34 tests`, `OK`), focused regression (`Ran 122 tests`, `OK`), compileall, roadmap verification, AWH verify, Python 3.13 full suite (`Ran 971 tests in 5.257s`, `OK`), and `git diff --check`.
- Pushed: `15573ad Parse transposed SEC segment tables` and `cdcc1d5 Prioritize statement periods for segment parsing`.
- EC2 deployed: `/opt/stockanalysis/app` fast-forwarded to `cdcc1d5`.
- EC2 parser smoke passed: `reported-segment-footnote-parser-run --execute` completed with `run_id=1059`, `candidate_count=1`, `parsed_metric_count=10`, `reported_segment_metric_count=10`, `segment_revenue=5`, `segment_operating_income=5`, `removed_stale_metric_count=10`, `recommendation_scoring_mutated=false`.
- EC2 DB sample passed: AAPL reported segment rows for `as_of_date=2026-05-26` now have `row_count=10`, `periods=["2025-09-27"]`, segments `Americas/Europe/Greater China/Japan/Rest of Asia Pacific`, metric codes `segment_operating_income/segment_revenue`, and `stale_2025_10_17_count=0`.

## Remaining Risks

- This is not a complete inline XBRL dimensional parser.
- The parser still targets conservative table shapes and may miss other issuers' custom segment layouts.
- Unit context can remain `USD_as_reported` when the "dollars in millions" phrase is outside the HTML table.
- The parser still relies on deterministic table layout detection; broader issuer coverage should be added with fixture-driven parser patterns.
- SOTP math still does not allocate value by reported segment metrics; this task only makes the real reported segment evidence available.
