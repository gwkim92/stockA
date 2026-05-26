# segment-level-sotp-inputs-v1 Review

## Review Summary

- scope check: within bounds. The task converts existing reported segment evidence into structured SOTP input visibility without changing recommendation weights, benchmark logic, portfolio guardrails, or order flow.
- schema check: no migration was introduced; existing assumptions JSON carries the new payload.
- scoring check: `recommendation_scoring_mutated=false` remains true for both SOTP and valuation snapshot EC2 runs.
- frontend check: the shared valuation card now shows Korean segment input rows before raw segment/footnote evidence.

## Issues Found

- EC2 SQL syntax was validated with `EXPLAIN` before write execution because the new query uses JSON aggregation and aggregate filters that unit string tests cannot fully prove.
- The current UI labels `USD_as_reported` as `공시 보고 단위` because the parser does not yet normalize external "dollars in millions" prose.

## Residual Risks

- This is still not a full segment-level SOTP allocation model. It exposes segment revenue, operating income, and margin as valuation input evidence.
- Segment-specific growth, capital intensity, discount rate, and multiple assumptions remain future work.

## Verification Evidence

- Local focused tests passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`).
- Local regression passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`).
- Local frontend typecheck passed: `cd apps/web && npm run typecheck`.
- Local compile and diff checks passed: `PYTHONPATH=src python3 -m compileall -q src tests`, `git diff --check`.
- Roadmap and AWH checks passed.
- Python 3.13 full suite passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`).
- EC2 SOTP run passed with `run_id=1060`, `reported_segment_input_count=5`, and `recommendation_scoring_mutated=false`.
- EC2 valuation snapshot run passed with `run_id=1061`, `snapshot_count=68`, and `recommendation_scoring_mutated=false`.
- EC2 API smoke passed: `/api/stocks/AAPL` exposes 5 reported segment inputs under SOTP, with the first input `Americas`.
- EC2 route smoke passed: `/stocks/AAPL` renders `사업부별 실적 입력`, `Americas`, `영업마진`, and `SOTP 구성요소`.
