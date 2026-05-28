# cycle-map-path-ux-v2 Contract

## Task Request

- request: `/cycle-map` 흐름 지도 화면에서 중복 안내를 줄이고, 뉴스가 상위 흐름과 종목/추천으로 연결되는 경로를 더 직접적으로 보여준다.

## Goal

- goal: `/cycle-map`을 `/cycles` 상태표와 분리된 경로 지도 화면으로 명확히 만들고, 사용자가 무엇을 클릭해야 근거를 이어볼 수 있는지 첫 화면에서 이해하게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/cycle-map-path-ux-v2/*`

## Invariants

- Do not change cycle map API contracts.
- Do not change graph edges, propagation, cycle scoring, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Replace generic repeated review strip copy with a page-specific path panel.
- Translate major sector/factor node labels that appear on the flow map.
- Keep the existing node groups, relationship chips, and detail links.
- Explain that `/cycle-map` shows causal paths while `/cycles` shows theme state snapshots.
- Make clear that path evidence is not an order or final recommendation.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-map-path-ux-v2`
- verification command: `git diff --check`

## Done Criteria

- [x] `/cycle-map` has a first-screen Korean path panel explaining news, flow nodes, instrument exposure, and recommendation links.
- [x] The page distinguishes `/cycle-map` from `/cycles` without implying graph paths are final trade instructions.
- [x] Local frontend verification passes.
- [x] AWH task verification passes.
- [x] EC2/tunnel route smoke confirms the new Korean copy renders.
