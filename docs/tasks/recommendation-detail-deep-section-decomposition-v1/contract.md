# recommendation-detail-deep-section-decomposition-v1 Contract

## Task Request

- request: continue UX/UI normalization by reducing the remaining large recommendation detail route file without changing recommendation scoring, backend DTOs, database schema, broker boundaries, or visible behavior.

## Goal

- goal: move the lower-fold recommendation evidence disclosures out of `apps/web/src/app/recommendations/[recommendationId]/page.tsx` into a focused route-local component, preserving the existing professional recommendation detail layout and e2e contract.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationProfessionalDetailSections.tsx`
  - `docs/tasks/recommendation-detail-deep-section-decomposition-v1/*`

## Scope

- Extract professional flow, ETF/company deep evidence, score component panels, and evidence trace disclosure composition.
- Keep all data fetching and score calculation behavior unchanged.
- Keep investor-facing route URLs unchanged.

## Non Goals

- No recommendation weight changes.
- No backend API or DB schema changes.
- No broker submit or order boundary changes.
- No redesign beyond preserving existing UI after extraction.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-deep-section-decomposition-v1`

## Acceptance Criteria

- Professional recommendation detail still shows the compact decision board.
- Deep evidence disclosures remain collapsed by default.
- Summary recommendation records still use the compact compatibility report.
- No horizontal overflow on `/recommendations/AAPL-professional-2026-06-25`.
- The new component stays under the 250 pure LOC ceiling.
