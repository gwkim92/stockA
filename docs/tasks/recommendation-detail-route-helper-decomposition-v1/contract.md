# recommendation-detail-route-helper-decomposition-v1 Contract

## Task Request

- request: continue recommendation detail UX normalization by extracting remaining route helpers from `page.tsx` without changing visible behavior.

## Goal

- goal: move product profile, order-boundary copy, professional-detail gating, and evidence trace card construction out of `apps/web/src/app/recommendations/[recommendationId]/page.tsx` into focused route-local model modules.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/recommendation-product-model.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/recommendation-evidence-trace-model.ts`
  - `docs/tasks/recommendation-detail-route-helper-decomposition-v1/*`

## Scope

- Extract product profile and order-boundary label helpers.
- Extract decision boundary copy and professional-detail gating helper.
- Extract recommendation evidence trace card model construction.
- Preserve route URLs, backend DTO usage, recommendation scoring, visible copy, and broker/order boundary.
- Keep new route-local model files below 250 pure LOC.

## Non Goals

- No recommendation score or weight changes.
- No backend API, database schema, or migration changes.
- No broker submit implementation.
- No visual redesign beyond behavior-preserving decomposition.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-route-helper-decomposition-v1`

## Acceptance Criteria

- Recommendation detail page remains functionally identical.
- Professional recommendation detail still shows decision board, quality boundary, market correlations, and deep sections.
- Summary recommendation records still use compatibility rendering.
- `page.tsx` owns route composition only and is below 250 pure LOC.
- New model files stay below 250 pure LOC.
- Browser QA shows no horizontal overflow and no forbidden investor-facing internal copy.
