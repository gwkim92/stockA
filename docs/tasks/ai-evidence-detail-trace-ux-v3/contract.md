# ai-evidence-detail-trace-ux-v3 Contract

## Task Request

- request: `/ai-evidence/[evidenceId]` 상세 화면에서 원천, 번역, AI 구조화, 자동 검증, 추천 연결 경계를 더 선명하게 만든다.

## Goal

- goal: 개별 AI 근거 상세를 dense card 나열이 아니라 한눈에 보는 근거 흐름 중심으로 재구성하고, 중복되는 요약/질문 블록을 줄인다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `docs/tasks/ai-evidence-detail-trace-ux-v3/*`

## Invariants

- Do not change AI evidence/detail API contracts.
- Do not change AI extraction, validator, propagation, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Render the existing visibility trace board on individual AI evidence detail pages.
- Remove the redundant status-rail and review-question blocks that repeat the same first-screen decision information.
- Keep source preview, structured fields, model input, neighborhood, and safety/audit sections.
- Make clear that the evidence detail remains read-only and cannot approve recommendations or orders.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-detail-trace-ux-v3`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/ai-evidence/[evidenceId]` renders a Korean visibility trace board for source, translation, AI structure, validator, recommendation linkage, and read-only boundary.
- [ ] Redundant first-screen status/question blocks are removed without removing source preview or detailed evidence sections.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
