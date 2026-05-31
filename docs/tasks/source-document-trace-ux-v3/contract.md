# source-document-trace-ux-v3 Contract

## Task Request

- request: `/source-documents/[documentId]` 원천 문서 화면에서 문서 목적, 한국어 요약, AI 근거 연결, 원문 접근 상태를 더 명확히 보여준다.

## Goal

- goal: 원천 문서 상세를 영어 원문 저장소처럼 보이지 않게 하고, AI 근거가 무엇을 근거로 해석됐는지 한국어로 먼저 확인하는 화면으로 만든다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/source-documents/[documentId]/page.tsx`
  - `docs/tasks/source-document-trace-ux-v3/*`

## Invariants

- Do not change source document/detail API contracts.
- Do not change ingestion, translation, AI extraction, validator, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen Korean source-document command panel.
- Anchor the panel to document summary, excerpts, linked AI evidence, and access policy sections.
- Keep existing source excerpts, linked evidence, and download/access policy behavior.
- Make clear that source documents support evidence verification only and do not approve recommendations or orders.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task source-document-trace-ux-v3`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/source-documents/[documentId]` has a first-screen Korean command panel explaining document summary, excerpts, linked AI evidence, and access policy.
- [ ] The page routes users to source summary, excerpts, linked AI evidence, and access policy without implying approval/write actions.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
