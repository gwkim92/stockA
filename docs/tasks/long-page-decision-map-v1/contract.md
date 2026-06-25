# long-page-decision-map-v1 Contract

## Task Request

- request: Continue the professional workspace redesign by making dense long-form screens easier to understand.
- request: Add a visible review-order layer so users know what to read first before entering long tables and audit details.

## Goal

- goal: `/portfolio/coverage` and `/data-health` should each show a compact Korean decision map that links to the most important sections first, without changing URLs, DTOs, scoring, benchmark, portfolio positions, broker/order boundaries, or backend behavior.

## Mutable Surface

- mutable surface:
  - `apps/web/src/components/research/`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - tests for the new component
  - `docs/tasks/long-page-decision-map-v1/`

## Invariants

- No recommendation score weight changes.
- No portfolio position, benchmark, paper trading, broker, or order flow changes.
- No API/DTO contract changes.
- No new paid dependencies or external services.
- Existing long pages may receive only minimal wiring; new UI logic belongs in a separate component.

## Acceptance Criteria

- `/portfolio/coverage` shows a compact Korean guide for the order of review: portfolio return, concentration/risk, rebalance, professional evidence, paper/order boundary.
- `/data-health` shows a compact Korean guide for the order of review: service status, data coverage, quality audit, AI/provider health, scheduler/execution.
- The guide uses semantic anchors and does not expose raw runner/pipeline/artifact terminology in investor-facing copy.
- 375px, 768px, and 1280px browser smoke has no horizontal overflow.
- Existing frontend tests/build and project verification pass.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run src/components/research/PageDecisionMap.test.tsx src/components/operations/DataHealthOverview.test.tsx src/lib/presentation/returns.test.ts`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task long-page-decision-map-v1`
- verification command: browser smoke at 375px, 768px, 1280px for `/portfolio/coverage` and `/data-health`
