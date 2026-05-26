# reported-segment-unit-normalization-v1 Review

## Review Summary

- Accepted. The implementation normalizes reported segment metric units from nearby filing table context, carries the unit metadata into SOTP evidence, and renders Korean unit labels so Apple-style segment rows are not shown as ambiguous `USD_as_reported` values.
- Scope boundaries held: SOTP totals, recommendation score weights, benchmark logic, and order boundaries were not changed.

## Issues Found

- None blocking.
- Non-blocking: values remain stored in reported filing units rather than converted to absolute dollars. This is intentional for this slice because downstream SOTP allocation currently uses ratios and evidence labels; segment-specific valuation assumptions should explicitly consume the unit metadata next.

## Residual Risks

- Issuer-specific filings may express units outside the currently covered millions/thousands patterns.
- HTML context extraction is deterministic and conservative; more complex SEC tables may still need parser expansion.

## Verification Evidence

- Local focused tests passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`).
- Local regression slice passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`).
- Local frontend typecheck passed: `cd apps/web && npm run typecheck`.
- Local compile/diff/full suite passed: `PYTHONPATH=src python3 -m compileall -q src tests`, `git diff --check`, and `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`).
- EC2 smoke passed on commit `9d5fdfd`: parser `run_id=1064`, SOTP `run_id=1065`, valuation `run_id=1066`.
- EC2 API verified `/api/stocks/AAPL` first reported segment input has `metric_unit=USD_millions_as_reported`, first segment `Americas`, revenue `178353.0`, operating income `72480.0`, and allocation basis `operating_income_share`.
- EC2 route smoke verified `/stocks/AAPL` renders `백만 달러 단위`, `사업부별 실적 입력`, `사업부별 가치 배분`, `Americas`, and `영업마진`.
