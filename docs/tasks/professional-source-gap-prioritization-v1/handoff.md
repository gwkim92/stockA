# professional-source-gap-prioritization-v1 Handoff

## Status

- completed: implemented, pushed, deployed to EC2, and smoked against the live DB/UI.

## Context

- Outcome weight review remains blocked until 2026-06-20 or later.
- Professional coverage is sufficient for the current guardrail, but visible source blockers remain.
- Known examples: SPY/fund-like products are not applicable to company financial models; EROK lacks SEC companyfacts US-GAAP financial statement facts.
- This task does not mutate recommendation scoring weights, broker/order state, or source facts.

## Implemented

- Backend: `src/stockanalysis/frontend/live_adapter.py` adds `professional_source_gap_prioritization` to data-health from active recommendations, portfolio exposure, professional coverage layers, fund source layers, and source linkage blockers.
- Frontend: `apps/web/src/app/data-health/page.tsx` adds a user-facing section that separates operating-company source blockers from ETF/fund company-model not-applicable cases.
- Types: `apps/web/src/lib/types.ts` adds the DTO shape.
- Tests: `tests/test_frontend_live_adapter.py` verifies EROK-style SEC source blockers, SPY-style fund not-applicable cases, remediation actions, and non-mutating safety flags.

## Exact Next Step

- exact next step: use the live ranked list to run only the deterministic remediation command for the top true source gap. Current top live source blocker is `EROK`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate missing financial facts.
- Do not classify ETF/fund products as failed company-financial coverage.

## Verification Evidence

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -k data_health`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed on EC2 commit `44012fb`: focused data-health tests, compileall, Next typecheck/build, service restart.
- Passed on EC2 `/api/data-health`: `professional_source_gap_prioritization.status=source_blockers_present`, `gap_count=3`, `source_blocker_count=1`, `fund_not_applicable_count=1`, top symbols `EROK:source_blocker`, `GOOG:coverage_gap`, `SPY:fund_not_applicable`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`.
- Passed on EC2 `/data-health`: rendered `전문 분석 소스 공백`, `원천 차단 종목 있음`, `EROK`, `SPY`, and `기업 재무 모델 비적용`.
