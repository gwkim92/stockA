# cycle-map-flow-clarity-v1 Contract

## Task Request

- request: `/cycles`와 `/cycle-map` 화면의 UX 문구를 정리해 사이클 상태, 상위 흐름 지도, 종목 연결, 추천 연결을 사용자 관점에서 이해 가능하게 만든다.

## Goal

- goal: 사용자가 “사이클은 매수 신호가 아니라 흐름 확인 지도”, “상위 뉴스가 어떤 경로로 테마와 종목에 닿는지”, “추천과 거래 안전은 별도 화면에서 확인해야 하는지”를 바로 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycles/page.tsx`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `docs/tasks/cycle-map-flow-clarity-v1/*`

## Invariants

- Do not change API contracts.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, cycle state data, AI artifacts, broker/order flow, live trading, or scheduler cadence.
- Do not add write actions, order buttons, calibration execution, or manual review controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Replace ambiguous “판정/판단/후보/페이퍼/보유검토” wording where it implies a missing manual workflow or order action.
- Use “현황판”, “확인 근거”, “추천 신호”, “가상 매매”, “보유 상태” consistently.
- Keep the read-only/no-order/no-weight-change boundary explicit.
- Preserve existing sections and data layout unless small wording adjustments are needed for clarity.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-map-flow-clarity-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] `/cycles` no longer uses ambiguous 판정/판단/후보 wording for cycle status.
- [x] `/cycle-map` no longer uses ambiguous 후보/페이퍼/보유검토 wording for flow paths.
- [x] The pages keep the read-only/no-order/no-weight-change boundary explicit.
- [x] Local frontend/backend verification passes.
- [x] EC2 route smoke confirms the updated Korean copy renders.
