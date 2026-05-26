# reported-segment-unit-normalization-v1 Handoff

## Status

- completed: contract, plan, implementation, focused tests, regression tests, frontend typecheck, compileall, full Python 3.13 suite, EC2 deploy/write smoke, route smoke, review, and roadmap update are complete.

## Current Findings

- Simple segment fixture already infers `USD_millions_as_reported` because the table caption contains `in millions`.
- Apple transposed fixture includes `(dollars in millions)` in a paragraph before the table, so the previous table-only unit inference can miss it.

## Decisions

- Do not convert stored values to absolute dollars yet.
- Use normalized unit labels to prevent user misunderstanding while preserving reported values.
- Do not change SOTP totals, recommendation weights, benchmark logic, or order boundaries.

## Exact Next Step

- exact next step: `segment-specific-sotp-assumptions-v1`; use normalized reported segment units to add segment-specific growth, margin, multiple, and driver assumptions without changing recommendation weights.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)
- Passed: EC2 deploy fast-forwarded `/opt/stockanalysis/app` to commit `9d5fdfd`.
- Passed: EC2 `reported-segment-footnote-parser-run --execute` produced `run_id=1064`, `candidate_count=1`, `parsed_metric_count=10`, `reported_segment_metric_count=10`, `segment_revenue=5`, `segment_operating_income=5`, `recommendation_scoring_mutated=false`.
- Passed: EC2 `sum-of-parts-valuation-run --execute` produced `run_id=1065`, `reported_segment_input_count=5`, `component_row_count=45`, `recommendation_scoring_mutated=false`.
- Passed: EC2 `valuation-snapshot-run --execute` produced `run_id=1066`, `snapshot_count=68`, `sum_of_parts=16`, `recommendation_scoring_mutated=false`.
- Passed: EC2 `/api/stocks/AAPL` exposes first reported segment input `Americas`, revenue `178353.0`, operating income `72480.0`, operating margin `0.4063850902423845`, `metric_unit=USD_millions_as_reported`, `source_run_id=pipeline-run-1064`, and allocation basis `operating_income_share`.
- Passed: EC2 route `/stocks/AAPL` returned `200 OK` and rendered `백만 달러 단위`, `사업부별 실적 입력`, `사업부별 가치 배분`, `Americas`, and `영업마진`.

## Remaining Risks

- Broader unit normalization may require issuer-specific text patterns beyond millions/thousands.
- The stored reported values are still preserved in reported units rather than converted to absolute dollars; frontend and evidence labels now prevent misunderstanding, while future valuation tasks should use the unit metadata explicitly.
