# paper-trading-status-clarity-v2 Handoff

## Status

- status: completed
- completed: `/paper-trading` 상단을 페이퍼 거래 판정판 중심으로 재구성하는 작업을 완료했다.

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
- passed: EC2 deploy `npm run typecheck`, `npm run build`, `sudo systemctl restart stockanalysis-web.service`, `systemctl is-active stockanalysis-web.service`
- passed: local tunnel `/paper-trading` route smoke at `http://127.0.0.1:13000/paper-trading` confirmed `페이퍼 거래 판정판`, `실제 주문`, `페이퍼 검증`, `차단 조건`, `다음에 볼 곳`, `실제 주문 전송 0건`
- passed: EC2 internal `/paper-trading` route smoke at `http://127.0.0.1:3000/paper-trading` confirmed the same strings
- passed: Playwright snapshot confirmed the top paper trading verdict panel and four decision cards.

## Next Step

- exact next step: 다음 UX slice는 `/trading-readiness`에서 실제 주문 경계, broker submit 차단, kill switch, audit boundary를 첫 화면에 명확히 표시한다.
