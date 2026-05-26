# portfolio-position-sizing-policy-v1 Handoff

## Current Status

- 진행 중: backend DTO, unit test, frontend type, `/portfolio/coverage` UI first slice를 구현했다.

## Intent

The project needs professional portfolio risk management, not only news and cycle interpretation. This task adds the first read-only position sizing envelope so the cockpit can explain whether a holding is too large, too small, missing evidence, or acceptable for hold review.

## Current Guardrails

- Do not change recommendation score weights.
- Do not write order intents.
- Do not enable broker submit.
- Do not create hard target weights from benchmark drift.

## Implementation Notes

- The first slice should compose existing data instead of adding schema.
- Missing valuation or professional analysis should appear as evidence gaps.
- The UI should use Korean investment language and avoid operator-only wording.
- `risk_budget.position_sizing_review`는 read-only envelope이며 target weight나 order quantity가 아니다.
- 후보 구분은 `reduce_review`, `add_blocked_until_evidence`, `watch_small_position`, `hold_review` 네 가지다.
- `review_ceiling_weight`는 주문 목표가 아니라 검토 상한 참고값이다.
- 모든 후보는 `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`를 유지해야 한다.

## Verification

- Focused backend:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_portfolio_coverage_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_portfolio_position_sizing_context_sql_is_read_only_professional_context`
  - Result: `Ran 2 tests ... OK`
- Adapter suite:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest tests.test_frontend_live_adapter`
  - Result: `Ran 59 tests ... OK`
- Compile/type/build:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Result: passed

## Remaining Work

- Run full repository unittest/compile/roadmap/AWH verification.
- Deploy/pull on EC2 and run API/route smoke.
- Update this handoff with final verification evidence.

## Exact Next Step

- exact next step: EC2에 현재 브랜치를 반영하고 `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-26` 및 `/portfolio/coverage`에서 `position_sizing_review`와 “포지션 크기 검토” 섹션이 실제 운영 데이터로 보이는지 smoke 검증한다.
