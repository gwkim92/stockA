# ai-evidence-results-decision-ux-v3 Contract

## Task Request

- request: `/ai-evidence/results` 구조화 결과 화면에서 통과 후보, 상위 흐름, 뉴스 묶음, 추천 경계를 더 명확히 보여준다.

## Goal

- goal: AI가 통과시킨 결과가 바로 주문이나 최종 추천이 아니라, 추천·보유검토의 입력 후보라는 점을 첫 화면에서 분명하게 만든다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `docs/tasks/ai-evidence-results-decision-ux-v3/*`

## Invariants

- Do not change event/news/API contracts.
- Do not change AI extraction, validator, propagation, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen Korean results command panel for direct stock results, macro/theme results, news clusters, and recommendation/order boundary.
- Add stable anchors from the panel to direct, macro, and cluster sections.
- Keep existing result cards and links.
- Make clear that passed AI results are review inputs, not final recommendations.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-results-decision-ux-v3`
- verification command: `git diff --check`

## Done Criteria

- [x] `/ai-evidence/results` has a first-screen Korean command panel explaining direct results, macro/theme results, clusters, and recommendation/order boundary.
- [x] The page routes users to direct, macro, and cluster result sections without implying final recommendation approval.
- [x] Local frontend verification passes.
- [x] AWH task verification passes.
- [x] EC2/tunnel route smoke confirms the new Korean copy renders.
