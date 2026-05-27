# paper-trading-status-clarity-v2 Contract

## Task Request

- request: 페이퍼 거래 화면에서 현재가 테스트 중인지, 차단 상태인지, 실행 가능한 상태인지 명확히 구분한다.

## Goal

- goal: `/paper-trading` 첫 화면에서 “실제 주문이 나갔는가”, “가상 검증 후보가 있는가”, “실거래 전환이 왜 막혔는가”, “다음에 어디를 봐야 하는가”를 바로 이해할 수 있게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/paper-trading/page.tsx`
  - `docs/tasks/paper-trading-status-clarity-v2/*`

## Invariants

- Do not change backend DTO shape.
- Do not change DB schema, scheduler, data ingestion, or AI analysis jobs.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper execution.
- Do not enable live broker submit or write actions.

## Scope

- Add a clear current-state summary for paper trading.
- Clarify that paper actions are simulations and not orders.
- Make blocked reasons and next steps visible before the candidate table.
- Preserve existing candidate links to recommendation, thesis, and stock detail.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-clarity-v2`

## Done Criteria

- [x] `/paper-trading` clearly labels current state as simulation/blocked/no live order.
- [x] Candidate table labels paper actions as simulated actions.
- [x] Blocked reasons and next steps are visible before detailed tables.
- [x] Local frontend verification passes.
- [x] EC2 and local tunnel route smoke pass.
