# segment-level-sotp-valuation-allocation-v1 Review

## Review Summary

- scope check: within bounds. The task adds segment allocation evidence while preserving existing SOTP component totals and all recommendation/order boundaries.
- schema check: no migration was introduced; allocation evidence is carried in existing assumptions JSON.
- scoring check: EC2 SOTP and valuation runs both report `recommendation_scoring_mutated=false`.
- frontend check: `/stocks/AAPL` now shows a Korean `사업부별 가치 배분` section.

## Issues Found

- The allocation is intentionally evidence-only. It splits the existing operating-business component value by operating-income share first, revenue share fallback, and does not introduce segment-specific valuation assumptions.
- Values still retain `USD_as_reported`, so unit normalization remains a next task before building segment-specific valuation drivers.

## Residual Risks

- This does not yet model segment growth, CAPEX, capital intensity, or segment-specific multiples.
- Negative operating-income segments may receive negative allocation weights under the operating-income-share basis. This is explainable evidence but should be revisited if future issuers contain loss-making segments.

## Verification Evidence

- Local focused tests passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`).
- Local regression passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`).
- Local frontend typecheck passed: `cd apps/web && npm run typecheck`.
- Local compile and diff checks passed: `PYTHONPATH=src python3 -m compileall -q src tests`, `git diff --check`.
- EC2 SQL `EXPLAIN` passed for generated SOTP upsert SQL and valuation snapshot upsert SQL.
- Python 3.13 full suite passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`).
- Roadmap and AWH checks passed.
- EC2 SOTP run passed with `run_id=1062`, `reported_segment_input_count=5`, and `recommendation_scoring_mutated=false`.
- EC2 valuation snapshot run passed with `run_id=1063`, `snapshot_count=68`, and `recommendation_scoring_mutated=false`.
- EC2 API smoke passed: `/api/stocks/AAPL` exposes 5 reported segment allocations under SOTP, with first input `Americas`, allocation basis `operating_income_share`, allocation weight `0.41257535135504364`, allocated base fair value `57.54485598738951`, and allocation sum `1`.
- EC2 route smoke passed: `/stocks/AAPL` renders `사업부별 가치 배분`, `기존 영업사업 SOTP 총액`, `Americas`, and `영업이익 비중`.
