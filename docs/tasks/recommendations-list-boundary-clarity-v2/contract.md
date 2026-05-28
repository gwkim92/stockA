# recommendations-list-boundary-clarity-v2 Contract

## Task Request

- request: `/recommendations` 목록 화면을 사용자가 바로 이해할 수 있게 재구성한다. 추천 신호, 페이퍼 대기, 주문 차단, 전문 분석 근거를 첫 화면에서 분리해 보여준다.

## Goal

- goal: 추천 목록 첫 화면이 "무엇을 봐야 하는가"를 먼저 말하고, 추천 후보가 실제 주문 지시가 아니라 읽기 전용 검토 신호임을 명확히 보여준다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/recommendations-list-boundary-clarity-v2/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change recommendation generation, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or order buttons.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a top recommendation command panel that separates signal status, paper validation state, order boundary, and professional evidence visibility.
- Reduce repeated explanatory copy and route users to the correct next section.
- Keep existing recommendation list links to recommendation detail, stock detail, thesis, and AI evidence.
- Preserve all data contracts and API calls.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendations-list-boundary-clarity-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/recommendations` has a first-screen Korean command panel explaining recommendation signal, paper wait, order block, and professional evidence.
- [ ] The page avoids implying that a recommendation can be directly ordered.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
