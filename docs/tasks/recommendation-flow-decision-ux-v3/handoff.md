# recommendation-flow-decision-ux-v3 Handoff

## Status

- in_progress: 추천 목록과 추천 상세의 사용자 문구, 라벨, 읽기 흐름을 정리 중이다.

## Completed

- completed: task contract를 생성했다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- pending: `cd apps/web && npm run typecheck`
- pending: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-flow-decision-ux-v3`
- pending: `git diff --check`
- pending: EC2 deploy and route/content smoke.

## Exact Next Step

- exact next step: 추천 목록과 추천 상세의 내부 표현을 사용자용 한국어로 바꾸고 로컬 검증을 실행한다.
