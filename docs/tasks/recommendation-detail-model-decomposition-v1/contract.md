# recommendation-detail-model-decomposition-v1 Contract

## Task Request

- request: continue professional investment UX normalization by extracting remaining recommendation detail model construction from the route page without changing visible behavior.

## Goal

- goal: move recommendation quality decision, quality checks, immediate focus, and waterfall card construction out of `apps/web/src/app/recommendations/[recommendationId]/page.tsx` into focused route-local model modules.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/recommendation-quality-model.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/recommendation-waterfall-model.ts`
  - `docs/tasks/recommendation-detail-model-decomposition-v1/*`

## Scope

- Extract quality decision and focus-item model creation.
- Extract recommendation waterfall card model creation.
- Preserve route URLs, backend DTO usage, recommendation score values, broker/order boundary, and rendered copy.
- Keep new route-local model files under the 250 pure LOC ceiling.

## Non Goals

- No recommendation weight changes.
- No backend API, DB schema, or migration changes.
- No broker submit or order boundary changes.
- No UI redesign beyond behavior-preserving decomposition.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-model-decomposition-v1`

## Acceptance Criteria

- Recommendation detail page renders the same professional decision board and deep sections.
- Summary recommendation records still use the compatibility report.
- New quality and waterfall model files are route-local and under 250 pure LOC.
- `page.tsx` no longer owns quality/waterfall model construction.
- Browser QA confirms no horizontal overflow and no forbidden investor-facing internal terms.
