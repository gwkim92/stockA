# trading-readiness-boundary-clarity-v2 Handoff

## Status

- status: in_progress
- in progress: `/trading-readiness` 상단을 실거래 경계 판정판 중심으로 재구성하는 작업을 진행 중이다.

## Intent

거래 안전 화면은 “실거래 가능한가?”에 바로 답해야 한다. 세부 조건을 읽기 전에 실거래 결론, 증권사 제출 가능 여부, 킬 스위치, 감사·페이퍼 검증 상태를 먼저 보여준다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task trading-readiness-boundary-clarity-v2`
- passed: `git diff --check`

## Next Step

- exact next step: 변경사항을 커밋하고 EC2에 배포한 뒤 `/trading-readiness` route smoke를 수행한다.
