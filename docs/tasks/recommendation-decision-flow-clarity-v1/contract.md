# recommendation-decision-flow-clarity-v1 Contract

## Task Request

- request: `/recommendations`와 `/recommendations/[id]` 화면의 UX 문구를 정리해 추천 신호, 근거, 보유 상태, 가상 매매 검증, 실거래 차단 상태를 사용자 관점에서 이해 가능하게 만든다.

## Goal

- goal: 추천 목록과 추천 상세가 주문 화면이나 수동 검토 UI처럼 보이지 않고, 사용자가 “왜 이 종목이 올라왔는지”, “어떤 근거가 연결됐는지”, “어디까지 사용할 수 있는지”, “왜 실거래 주문은 막혀 있는지”를 바로 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/recommendation-decision-flow-clarity-v1/*`

## Invariants

- Do not change API contracts.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, performance outcomes, paper validation records, broker/order flow, live trading, or scheduler cadence.
- Do not add write actions, order buttons, calibration execution, or manual review controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Replace ambiguous “후보/검토/판단/페이퍼” wording where it implies a missing manual workflow.
- Use “추천 신호”, “확인 대상”, “추천 상태”, “결정 입력”, “가상 매매” and “실거래 상태” consistently.
- Keep the read-only/no-order/no-weight-change boundary explicit.
- Preserve existing sections and data layout unless small wording adjustments are needed for clarity.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-decision-flow-clarity-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] `/recommendations` uses user-facing recommendation signal wording and avoids manual-review copy.
- [x] `/recommendations/[id]` top decision flow explains current recommendation status and boundaries without implying an order action.
- [x] The pages keep the read-only/no-order/no-weight-change boundary explicit.
- [x] Local frontend/backend verification passes.
- [x] EC2 route smoke confirms the updated Korean copy renders.
