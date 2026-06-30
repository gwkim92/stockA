# recommendation-detail-deep-section-decomposition-v1 Handoff

## Status

- completed: implementation, typecheck, unit tests, frontend API contract, build, e2e, browser QA, commit, push, EC2 deployment, and 13000 smoke passed.
- pending rollout: none.

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
- EC2 deployed commit: `09168f4f`
- EC2 passed: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- EC2 services after restart: `stockanalysis-frontend-api.service=active`, `stockanalysis-web.service=active`, `stockanalysis-web-public-13000.service=active`
- EC2 internal route smoke passed: `/`, `/recommendations`, `/recommendations/recommendation-522`, `/stocks/AAPL`, `/data-health` all returned `200`.
- Local tunnel `http://127.0.0.1:13000` route smoke passed for the same routes.
- EC2 browser QA passed for `/recommendations/recommendation-522` at 375px, 768px, and 1280px: overflow `0`, recommendation content present, no visible `TECH_DOMAIN`, `DOMAIN TO SECTOR`, `canonical`, `shadow`, `runner`, `artifact`, `검토 가능`, `확인한다`, `봐야 한다`, or `미수집`.
- EC2 screenshot evidence:
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/ec2/recommendation-522-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/ec2/recommendation-522-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/ec2/recommendation-522-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-deep-section-decomposition-v1/ec2/summary.json`

## Remaining Risks

- `apps/web/src/app/recommendations/[recommendationId]/page.tsx` remains above the 250 pure LOC target because it still owns recommendation quality decisions, trace card creation, waterfall card creation, and page composition.
- This slice is behavior-preserving only. It does not improve recommendation quality or scoring.

## Exact Next Step

- exact next step: continue splitting `apps/web/src/app/recommendations/[recommendationId]/page.tsx` by moving quality-decision and waterfall-card construction into route-local model modules.
