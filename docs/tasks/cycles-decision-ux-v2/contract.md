# cycles-decision-ux-v2 Contract

## Task Request

- request: `/cycles` 사이클 화면을 사용자가 무엇을 먼저 보고 어디로 이동해야 하는지 이해할 수 있게 재구성한다.

## Goal

- goal: `/cycles`를 테마별 사이클 상태표로 명확히 만들고, `/cycle-map`은 상위 흐름 경로 지도라는 차이를 첫 화면에서 설명한다.

## Mutable Surface

- mutable surface:
- `apps/web/src/app/cycles/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/cycles-decision-ux-v2/*`

## Invariants

- Do not change cycle snapshot API contracts.
- Do not change cycle scoring, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen Korean command panel explaining how to read cycle status, state changes, evidence features, and next navigation.
- Explain the difference between `/cycles` and `/cycle-map`.
- Keep existing cycle rows and theme links.
- Make clear that cycle state is context, not an automatic buy/sell signal.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycles-decision-ux-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/cycles` has a first-screen Korean command panel explaining status, changes, evidence axes, and next navigation.
- [ ] The page distinguishes `/cycles` from `/cycle-map` without implying cycle status is a final recommendation.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
