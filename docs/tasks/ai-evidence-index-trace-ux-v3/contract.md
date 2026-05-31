# ai-evidence-index-trace-ux-v3 Contract

## Task Request

- request: `/ai-evidence` AI 뉴스 후보 목록에서 사용자가 무엇을 먼저 판단하고 어느 상세 화면으로 들어가야 하는지 더 명확하게 만든다.

## Goal

- goal: AI 후보 목록을 단순 카드 나열이 아니라 `원천 뉴스 → 한국어 번역 → AI 구조화 → validator 결과 → 종목/추천 연결` 추적 작업대로 재구성한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/ai-evidence-index-trace-ux-v3/*`

## Invariants

- Do not change event/news/API contracts.
- Do not change AI extraction, validator, propagation, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen Korean trace command panel for direct stock candidates, macro/theme candidates, blocked/suppressed candidates, and evidence detail review.
- Add stable anchors from the panel to the direct and macro candidate lists.
- Keep existing candidate cards and links.
- Make clear that AI candidates are inputs for review, not final recommendations or orders.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-index-trace-ux-v3`
- verification command: `git diff --check`

## Done Criteria

- [x] `/ai-evidence` has a first-screen Korean trace command panel explaining direct stock, macro/theme, blocked/suppressed, and detail-review lanes.
- [x] The page routes users to direct candidates, macro candidates, structured results, blocked candidates, and detail pages without implying final recommendation approval.
- [x] Local frontend verification passes.
- [x] AWH task verification passes.
- [x] EC2/tunnel route smoke confirms the new Korean copy renders.
