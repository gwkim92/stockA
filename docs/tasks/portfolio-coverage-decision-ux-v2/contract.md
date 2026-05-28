# portfolio-coverage-decision-ux-v2 Contract

## Task Request

- request: `/portfolio/coverage` 화면을 사용자가 보유 포트폴리오에서 무엇을 먼저 봐야 하는지 이해할 수 있게 재구성한다.

## Goal

- goal: 첫 화면에서 보유 검토, 위험 예산, 리밸런싱 후보, 성과 성숙 대기/weight 차단을 분리해 보여주고, 실제 주문이나 자동 리밸런싱으로 오해하지 않게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/portfolio-coverage-decision-ux-v2/*`

## Invariants

- Do not change portfolio coverage API contracts.
- Do not change recommendation scoring weights, benchmark definitions, portfolio positions, paper validation records, broker/order flow, or live trading.
- Do not add write actions, order buttons, or rebalance execution controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Add a first-screen portfolio command panel that separates holdings coverage, risk budget, rebalance review, and outcome maturity/weight-review boundary.
- Add section anchors so the command cards move users to the correct evidence blocks.
- Reduce first-screen operational ambiguity and make the read-only/no-order boundary explicit.
- Preserve existing detailed cards and tables.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-ux-v2`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/portfolio/coverage` has a first-screen Korean command panel explaining holdings coverage, risk budget, rebalance review, and outcome/weight boundary.
- [ ] The page routes users to review sections without implying a trade action.
- [ ] Local frontend verification passes.
- [ ] AWH task verification passes.
- [ ] EC2/tunnel route smoke confirms the new Korean copy renders.
