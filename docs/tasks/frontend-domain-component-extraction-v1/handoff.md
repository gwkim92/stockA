# frontend-domain-component-extraction-v1 Handoff

## Status

- completed: local implementation, focused regression, build, API contract, roadmap, E2E route smoke, and browser desktop/mobile `/data-health` checks passed.
- scope completed: first safe extraction slice from `apps/web/src/app/data-health/page.tsx`

## Current Decision

- Keep this commit behavior-preserving and limited to the first `data-health` overview extraction.
- Do not keep extracting more sections in the same commit because the next likely slices touch different operational concerns: Toss broker data, scheduler details, runtime boundary, and professional analysis panels.
- Leave `admin-server-action-auth-boundary-v1` as a separate security task because React Doctor reports pre-existing server-action auth findings outside this UI extraction.

## Next Step

- exact next step: implement `data-health-toss-and-runtime-section-extraction-v1` by moving the Toss broker data section and bottom runtime/provider detail panels into rendering-only operations components, then run the same unit/build/E2E/browser gates.

## What Changed

- Added `apps/web/src/components/operations/DataHealthOverview.tsx`.
- Added `apps/web/src/components/operations/DataHealthOverview.test.tsx`.
- Replaced the top `data-health` hero, open-gate triage, and collection status JSX with `DataHealthOverview`.
- Kept the page-level normalization and backend DTO reads in `data-health/page.tsx` for this first slice.
- Did not change backend API DTOs, DB schema, AI behavior, recommendation scoring, benchmark, portfolio positions, broker submit, or order boundary.

## Verification Evidence

- Red check before implementation:
  - `cd apps/web && npm test -- --run src/components/operations/DataHealthOverview.test.tsx`
  - expected failure: missing `./DataHealthOverview` import
- Focused regression:
  - `cd apps/web && npm test -- --run src/components/operations/DataHealthOverview.test.tsx`
  - result: `1 passed`
- Full frontend unit:
  - `cd apps/web && npm test -- --run`
  - result: `6 passed`, `15 tests passed`
- Type/build:
  - `cd apps/web && npm run typecheck`
  - result: passed
  - `cd apps/web && npm run build`
  - result: passed
- API/roadmap:
  - `bash scripts/verify_frontend_api_contract.sh`
  - result: passed
  - `bash scripts/verify_project_execution_roadmap.sh`
  - result: passed
- Browser/E2E:
  - fixture API: `http://127.0.0.1:8765`
  - local production web: `http://127.0.0.1:13003`
  - `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
  - result: `51 passed`
  - in-app browser `/data-health` desktop `1280x900`: overflow `0`, overview/triage/collection present, raw internal terms absent
  - in-app browser `/data-health` mobile `390x844`: overflow `0`, overview/triage/collection present, raw internal terms absent

## File Size Notes

- `apps/web/src/components/operations/DataHealthOverview.tsx`: `167` pure LOC
- `apps/web/src/components/operations/DataHealthOverview.test.tsx`: `62` pure LOC
- `apps/web/src/app/data-health/page.tsx`: still oversized at `5324` pure LOC after this first slice

## Remaining Work

- Continue `data-health` extraction by moving the Toss broker data section and scheduler/runtime detail panels into rendering-only components.
- Then apply the same pattern to:
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- Separate calculation/view-model functions from JSX sections before adding new UI behavior.

## Risks

- This is behavior-preserving. It reduces review risk but does not yet solve the full oversized `data-health` file.
- Existing React Doctor findings around admin server-action auth are outside this task and should remain a separate `admin-server-action-auth-boundary-v1` task.
