# paper-trading-status-clarity-v2 Handoff

## Status

- status: in_progress
- in progress: `/paper-trading` 상단을 페이퍼 거래 판정판 중심으로 재구성하는 작업을 진행 중이다.

## Intent

페이퍼 거래 화면은 주문 화면이 아니라 안전 검증 화면이다. 사용자는 첫 화면에서 실제 주문이 나갔는지, 후보가 시뮬레이션인지, 어떤 조건이 실거래 전환을 막는지 바로 알아야 한다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-clarity-v2`
- passed: `git diff --check`

## Next Step

- exact next step: 변경사항을 커밋하고 EC2에 배포한 뒤 `/paper-trading` route smoke를 수행한다.
