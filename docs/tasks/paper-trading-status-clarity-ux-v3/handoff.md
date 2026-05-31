# paper-trading-status-clarity-ux-v3 Handoff

## Status

- in_progress: `/paper-trading` 화면의 가상 매매 상태, 실거래 차단, 후보 검토 문구를 정리 중이다.

## Completed

- completed: task contract를 생성했다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- pending: `cd apps/web && npm run typecheck`
- pending: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-clarity-ux-v3`
- pending: `git diff --check`
- pending: EC2 deploy and route/content smoke.
- pending: Playwright snapshot.

## Exact Next Step

- exact next step: `/paper-trading` visible copy and labels를 사용자용 한국어로 정리하고 검증한다.
