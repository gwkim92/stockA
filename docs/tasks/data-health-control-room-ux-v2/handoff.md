# data-health-control-room-ux-v2 Handoff

## Status

- status: in_progress
- in progress: `/data-health` 상단을 운영 판정판 중심으로 재구성하는 작업을 진행 중이다.

## Intent

운영 로그를 많이 보여주는 것보다 사용자가 먼저 알아야 하는 결론을 앞에 둔다.

첫 화면의 질문은 네 가지다.

- 서비스 접근이 가능한가?
- 자동 수집이 돌고 있는가?
- 데이터·AI 품질이 투자 판단에 쓸 수 있는 상태인가?
- 추천 weight와 주문은 안전하게 차단되어 있는가?

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-control-room-ux-v2`
- passed: `git diff --check`

## Next Step

- exact next step: 변경사항을 커밋하고 EC2에 배포한 뒤 `/data-health` route smoke를 수행한다.
