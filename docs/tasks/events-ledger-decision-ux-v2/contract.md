# events-ledger-decision-ux-v2 Contract

## Task Request

- request: `/events` 수집 뉴스 원장 화면을 사용자가 무엇을 먼저 확인해야 하는지 이해할 수 있게 재구성한다.

## Goal

- goal: 첫 화면에서 수집 원장, 1차 분류, AI 분석 연결, 차단/저신호 검토를 분리해 보여주고, 뉴스가 추천이나 주문으로 바로 이어지는 것이 아님을 명확히 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/events-ledger-decision-ux-v2/*`

## Invariants

- Do not change event/news API contracts.
- Do not change AI extraction, validator, propagation, recommendation scoring, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions or review submission controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen event command panel that separates raw collection, classification, AI evidence linkage, and blocked/low-signal review.
- Add section anchors for the event ledger and next evidence screens.
- Keep the existing news ledger cards and processing-stage links.
- Make the read-only/evidence-only boundary explicit.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-ledger-decision-ux-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/events` has a first-screen Korean command panel explaining collection, classification, AI linkage, and blocked/low-signal review.
- [ ] The page routes users to evidence sections without implying a recommendation, trade action, or manual approval flow.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
