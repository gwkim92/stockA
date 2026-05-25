# Session Handoff

## Current Status

- 완료: 포트폴리오 커버리지 API와 화면에 위험 예산/포지션 사이징 visibility를 추가했고, 로컬 계약/타입/빌드/AWH 검증을 통과했다.

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
- Pending: EC2 pull/rebuild/restart and `/api/portfolio/Long%20Term%20Paper/coverage`, `/portfolio/coverage` smoke.

## Exact Next Step

- exact next step: 변경사항을 commit/push한 뒤 EC2에서 pull, `apps/web` rebuild, FastAPI/Next restart를 수행하고 API/route smoke를 확인한다.
