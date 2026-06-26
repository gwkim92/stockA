# data-health-model-boundary-decomposition-v1 Contract

## Task Request

- request: Continue the `/data-health` operations-console cleanup by reducing the transitional `dataHealthModel.ts` module size.
- request: Preserve the existing `/data-health` route behavior and public import surface while moving low-risk model boundaries out of the route-local monolith.

## Goal

- goal: Extract data-health type aliases into a dedicated type module.
- goal: Extract `DEFAULT_*` fallback objects into a dedicated defaults module.
- goal: Keep `apps/web/src/app/data-health/_components/dataHealthModel.ts` as the compatibility barrel for existing page imports.
- goal: Do not change backend DTOs, DB schema, scheduler cadence, AI logic, recommendation weights, or broker/order boundary.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/_components/dataHealthModel.ts`
  - `apps/web/src/app/data-health/_components/dataHealthTypes.ts`
  - `apps/web/src/app/data-health/_components/dataHealthDefaults.ts`
  - `docs/tasks/data-health-model-boundary-decomposition-v1/**`

## Non-goals

- No visual redesign in this slice beyond verifying the rendered `/data-health` behavior remains intact.
- No function-level domain split yet. Scheduler, AI/provider, outcome/professional function groups will be split after this lower-risk type/default extraction.
- No changes to API DTOs, scoring, portfolio positions, benchmark data, or order submission behavior.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:<PORT> npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-model-boundary-decomposition-v1`
