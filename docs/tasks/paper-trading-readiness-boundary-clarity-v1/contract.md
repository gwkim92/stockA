# paper-trading-readiness-boundary-clarity-v1 Contract

## Task Request

- request: `/paper-trading`과 `/trading-readiness` 화면의 UX 문구를 정리해 가상 매매, 실거래 차단, 증권사 제출 가능 여부, 안전 조건 상태를 사용자 관점에서 이해 가능하게 만든다.

## Goal

- goal: 사용자가 “현재 실제 주문이 나갔는지”, “가상 매매는 무엇을 계산하는지”, “어떤 조건이 실거래 전환을 막는지”, “어디를 다음에 확인해야 하는지”를 바로 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `docs/tasks/paper-trading-readiness-boundary-clarity-v1/*`

## Invariants

- Do not change API contracts.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, performance outcomes, paper validation records, broker/order flow, live trading, or scheduler cadence.
- Do not add write actions, order buttons, calibration execution, or manual review controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Replace ambiguous “후보/검토/판정/페이퍼” wording where it implies a missing manual workflow or order action.
- Use “가상 매매 항목”, “확인 대상”, “실거래 경계”, “상태”, “안전 조건” consistently.
- Keep the read-only/no-order/no-broker-submit boundary explicit.
- Preserve existing sections and data layout unless small wording adjustments are needed for clarity.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task paper-trading-readiness-boundary-clarity-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/paper-trading` clearly labels simulated actions as 가상 매매 항목, not order candidates.
- [ ] `/trading-readiness` clearly labels real-trading boundaries and safety conditions without implying an order UI.
- [ ] The pages keep the read-only/no-order/no-broker-submit boundary explicit.
- [ ] Local frontend/backend verification passes.
- [ ] EC2 route smoke confirms the updated Korean copy renders.
