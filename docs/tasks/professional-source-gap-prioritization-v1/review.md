# professional-source-gap-prioritization-v1 Review

## Review Summary

- Implemented. Data-health now ranks professional analysis source gaps by active recommendation exposure, missing layer count, and source blocker severity.
- ETF/fund-like products are labeled as company-financial-model not applicable, not failed company financial analysis.
- Each visible gap includes a concrete remediation action and, when applicable, a backend CLI command. Cases with missing SEC us-gaap facts explicitly say not to fabricate financials.

## Issues Found

- None found in the focused local verification.

## Residual Risks

- The prioritization is read-only and does not itself run remediation. The next task should execute the top deterministic remediation command only after inspecting the live ranked list.
- Free public data may remain unavailable for some non-US-GAAP or fund-like products; those should stay blocked rather than filled with synthetic data.

## Verification Evidence

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -k data_health`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed on EC2 commit `44012fb`: focused data-health tests, compileall, Next typecheck/build, service restart.
- Passed on EC2 `/api/data-health`: `status=source_blockers_present`, `gap_count=3`, `source_blocker_count=1`, `fund_not_applicable_count=1`, top symbols `EROK:source_blocker`, `GOOG:coverage_gap`, `SPY:fund_not_applicable`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`.
- Passed on EC2 `/data-health`: visible text includes `전문 분석 소스 공백`, `원천 차단 종목 있음`, `EROK`, `SPY`, and `기업 재무 모델 비적용`.
