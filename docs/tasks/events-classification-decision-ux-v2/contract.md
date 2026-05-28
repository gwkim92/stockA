# events-classification-decision-ux-v2 Contract

## Task Request

- request: `/events/classification` 1차 분류 태그 화면을 사용자가 무엇을 검수해야 하는지 이해할 수 있게 재구성한다.

## Goal

- goal: 첫 화면에서 테마 묶음, 직접 종목 뉴스, 상위 흐름 뉴스, AI 비교 필요 항목을 분리해 보여주고, 1차 분류가 최종 AI 판단이나 추천 근거가 아님을 명확히 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/events/classification/page.tsx`
  - `docs/tasks/events-classification-decision-ux-v2/*`

## Invariants

- Do not change event/news API contracts.
- Do not change rule classification, AI extraction, validator, propagation, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen classification command panel that separates theme grouping, direct instrument tags, macro/theme-only tags, and AI comparison.
- Add section anchors for theme classification groups.
- Keep existing theme-group cards and links.
- Make the preliminary-rule-classification boundary explicit.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-classification-decision-ux-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/events/classification` has a first-screen Korean command panel explaining theme groups, direct instrument tags, macro/theme-only tags, and AI comparison.
- [ ] The page routes users to classification groups and AI evidence without implying final recommendation approval.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
