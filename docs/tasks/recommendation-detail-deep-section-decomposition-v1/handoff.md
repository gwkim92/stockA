# recommendation-detail-deep-section-decomposition-v1 Handoff

## Status

- completed: implementation, typecheck, unit tests, frontend API contract, build, e2e, browser QA, and diff check passed.
- pending rollout: commit, push, EC2 deployment.

## Current Status

- branch: `develop`
- target route: `/recommendations/[recommendationId]`

## Implementation Notes

- Added `RecommendationProfessionalDetailSections` as the route-local owner for lower-fold professional evidence disclosures.
- Removed lower-fold disclosure composition from the page file while keeping data preparation and high-level decision rendering in the page.
- Kept scoring, broker/order boundary, backend DTOs, and database schema unchanged.
- New component pure LOC: `210`.
- Recommendation page pure LOC after split: `762`, still legacy-large and needs future splits.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test`
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `cd apps/web && npm run build`
- passed: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e` (`69` tests)
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-deep-section-decomposition-v1`
- passed: `git diff --check`
- browser QA passed for `/recommendations/AAPL-professional-2026-06-25` and `/recommendations/AAPL-2024-11-01` at 375px, 768px, and 1280px.
- screenshot QA metrics: overflow `0`, deep disclosure open count `0`, decision board present, forbidden internal copy absent.
- screenshot evidence:
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/local/professional-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/local/professional-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/local/professional-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/local/summary-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/local/summary-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/local/summary-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/local/summary.json`

## Remaining Risks

- `apps/web/src/app/recommendations/[recommendationId]/page.tsx` remains above the 250 pure LOC target because it still owns recommendation quality decisions, trace card creation, waterfall card creation, and page composition.
- This slice is behavior-preserving only. It does not improve recommendation quality or scoring.

## Exact Next Step

- exact next step: commit and push `develop`, then deploy to EC2 with `git pull --ff-only origin develop`, build, restart services, and smoke `http://127.0.0.1:13000`.
