# data-health-operations-console-helper-decomposition-v1

## Task Request

- request: Continue the professional investment UX/UI normalization by decomposing the oversized `/data-health` operations console route.
- request: Keep backend behavior unchanged while improving frontend structure and maintainability.

Continue the professional investment UX/UI normalization by decomposing the oversized `/data-health` operations console route. The user asked to keep progressing on the remaining core UI refactor and to avoid changing backend behavior while improving structure and maintainability.

## Concrete Goal

- goal: `/data-health` should still render the same operations-console evidence while large quality/provider/eval JSX sections and command-card helper composition are moved into typed route-local components/models.

Move large `/data-health` operating-console JSX sections and command-card helper composition out of `apps/web/src/app/data-health/page.tsx` into typed route-local components/models. The page should still render the same operational evidence, but the route file should primarily compose data and sections rather than owning every visible block.

## Objective

Reduce the `/data-health` route file by moving operating-console view sections and helper composition into route-local components/models while preserving existing API DTOs and rendered behavior.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthQualityAuditSection.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthLiveAiInvocationSection.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthOpenAiProviderSection.tsx`
  - `apps/web/src/app/data-health/_components/DataHealthNewsAiEvalQualitySection.tsx`
  - `apps/web/src/app/data-health/_components/dataHealthOverviewCardModel.ts`
  - `docs/tasks/data-health-operations-console-helper-decomposition-v1/contract.md`
  - `docs/tasks/data-health-operations-console-helper-decomposition-v1/handoff.md`

- `apps/web/src/app/data-health/page.tsx`
- `apps/web/src/app/data-health/_components/DataHealthQualityAuditSection.tsx`
- `apps/web/src/app/data-health/_components/DataHealthLiveAiInvocationSection.tsx`
- `apps/web/src/app/data-health/_components/DataHealthOpenAiProviderSection.tsx`
- `apps/web/src/app/data-health/_components/DataHealthNewsAiEvalQualitySection.tsx`
- `apps/web/src/app/data-health/_components/dataHealthOverviewCardModel.ts`
- `docs/tasks/data-health-operations-console-helper-decomposition-v1/contract.md`
- `docs/tasks/data-health-operations-console-helper-decomposition-v1/handoff.md`

## Scope

- Keep `/data-health` URL and backend API contract unchanged.
- Extract large quality/provider/eval sections from `apps/web/src/app/data-health/page.tsx`.
- Extract top-level operations command/summary card composition from the route file where it can be done safely.
- Keep investor-facing screens and recommendation scoring untouched.
- Keep broker submit and order boundary unchanged.

## Non Goals

- No DB schema changes.
- No recommendation weight changes.
- No AI analysis logic changes.
- No broker live order submit.
- No new paid tools or chart libraries.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-operations-console-helper-decomposition-v1`
- verification command: Browser QA for `/data-health` at 375px, 768px, and 1280px.

## Guardrails

- Do not commit `.omo/`, `apps/test-results/`, `apps/web/test-results/`, or `dogfood-output/`.
- EC2 deploy, if performed, must pull `develop` only.
- Operations-console details may expose technical execution terms, but investor-facing routes must not.
