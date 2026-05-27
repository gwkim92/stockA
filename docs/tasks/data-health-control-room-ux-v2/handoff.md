# data-health-control-room-ux-v2 Handoff

## Status

- status: completed
- completed: `/data-health` 상단을 운영 판정판 중심으로 재구성하는 작업을 완료했다.

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
- passed: EC2 deploy `npm run typecheck`, `npm run build`, `sudo systemctl restart stockanalysis-web.service`, `systemctl is-active stockanalysis-web.service`
- passed: local tunnel `/data-health` route smoke at `http://127.0.0.1:13000/data-health` confirmed `운영 판정판`, `서비스 접근`, `자동 수집`, `데이터·AI 품질`, `투자 경계`, `오늘 조치`
- passed: EC2 internal `/data-health` route smoke at `http://127.0.0.1:3000/data-health` confirmed the same strings
- passed: Playwright snapshot confirmed the top operating verdict panel and four decision cards.

## Next Step

- exact next step: 다음 UX slice는 `/paper-trading`에서 페이퍼 거래가 테스트 중인지, 차단 상태인지, 실행 가능한 상태인지 첫 화면에 명확히 표시한다.
