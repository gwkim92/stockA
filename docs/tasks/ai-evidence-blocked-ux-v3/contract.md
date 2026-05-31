# ai-evidence-blocked-ux-v3 Contract

## Task Request

- request: `/ai-evidence/blocked` 차단 후보 화면에서 제외 이유와 다음 처리 방향을 더 명확히 보여준다.

## Goal

- goal: 차단 후보를 단순 실패 목록이 아니라 `추천 입력 제외`, `저신호 보류`, `분류 보강 후보`, `주문 경계 유지`로 구분해 운영자가 무엇을 해야 하는지 이해하게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `docs/tasks/ai-evidence-blocked-ux-v3/*`

## Invariants

- Do not change event/news/API contracts.
- Do not change AI extraction, validator, propagation, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen Korean blocked-candidate command panel.
- Keep existing blocked candidate list and event cards.
- Make clear that blocked/suppressed candidates are not recommendation inputs.
- Avoid implying that the user can approve or submit from this screen.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-blocked-ux-v3`
- verification command: `git diff --check`

## Done Criteria

- [x] `/ai-evidence/blocked` has a first-screen Korean command panel explaining blocked, suppressed, remediation, and order-boundary lanes.
- [x] The page routes users to blocked list and related result screens without implying approval/write actions.
- [x] Local frontend verification passes.
- [x] AWH task verification passes.
- [x] EC2/tunnel route smoke confirms the new Korean copy renders.
