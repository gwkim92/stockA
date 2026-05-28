# performance-decision-ux-v2 Contract

## Task Request

- request: `/performance` 화면을 성과가 측정됐는지, 표본이 충분한지, 어떤 항목이 제외됐는지, 추천 weight 변경과 어떤 관계인지 먼저 이해할 수 있게 재구성한다.

## Goal

- goal: 첫 화면에서 측정 상태, 표본 품질, 귀속 해석, 커버리지 제외/보완 필요를 분리해 보여주고 성과 화면을 추천 산식 변경이나 주문 실행으로 오해하지 않게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/performance/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/performance-decision-ux-v2/*`

## Invariants

- Do not change performance API contracts.
- Do not change recommendation scoring weights, benchmark definitions, portfolio positions, outcome records, paper validation records, broker/order flow, or live trading.
- Do not add write actions, order buttons, calibration execution, or weight-review controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen performance command panel that separates measured outcomes, sample quality, attribution lens, and coverage exclusions.
- Add section anchors for measured outcomes, quality evaluation, attribution, and coverage exclusions.
- Make the read-only/evaluation-only boundary explicit.
- Preserve existing performance outcome, attribution, exclusion, and quality gate sections.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task performance-decision-ux-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/performance` has a first-screen Korean command panel explaining measured outcomes, sample quality, attribution lens, and coverage exclusions.
- [ ] The page routes users to evidence sections without implying a trade action or weight change.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
