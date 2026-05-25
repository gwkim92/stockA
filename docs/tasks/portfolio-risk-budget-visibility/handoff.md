# Session Handoff

## Current Status

- 완료: 포트폴리오 커버리지 API와 화면에 위험 예산/포지션 사이징 visibility를 추가했고, 로컬 계약/타입/빌드/AWH와 EC2 API/route smoke를 통과했다.

## Implementation Notes

- 새 migration은 만들지 않는다.
- 기존 `portfolio.allocation_policy`를 read-only로 재사용한다.
- `/api/portfolio/{portfolio}/coverage`는 `allocation_policy`, `risk_budget`, position별 `position_size_status`를 반환한다.
- risk budget은 추천 점수나 주문을 바꾸지 않고, 보유 검토와 포지션 사이징 설명에만 사용한다.
- position size status:
  - `within_budget`
  - `below_rebalance_floor`
  - `over_single_position_limit`
  - `missing_weight`

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-visibility`
- Passed on EC2: pulled `9a8f307`, rebuilt `apps/web`, restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
- Passed on EC2 service check: both services returned `active`.
- Passed on EC2 API: `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-23` returned allocation policy `global_default_long_term_guardrail`, max single position `0.25`, risk status `needs_position_review`, largest `MSFT` at `0.3078`, over-limit count `2`, position count `4`.
- Passed on EC2 route smoke: `/portfolio/coverage` rendered `위험 예산 / 포지션 크기`, `단일 종목 상한`, `한도 초과`, `비중 한도`.

## Exact Next Step

- exact next step: 다음 작업은 `recommendation-detail-equity-research-link`로 추천 상세에서 기업 리서치 artifact까지 추적하게 하거나, `portfolio-risk-budget-policy-v2`로 sector/theme concentration limit을 추가한다.
