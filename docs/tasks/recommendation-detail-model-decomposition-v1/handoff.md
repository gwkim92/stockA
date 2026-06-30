# recommendation-detail-model-decomposition-v1 Handoff

## Status

- in progress: implementation complete locally; verification and rollout are pending.

## Current Status

- branch: `develop`
- target route: `/recommendations/[recommendationId]`

## Implementation Notes

- Added `recommendation-quality-model.ts` for recommendation quality decision, quality checks, and immediate focus item construction.
- Added `recommendation-waterfall-model.ts` for recommendation waterfall card construction.
- Updated `page.tsx` so it composes fetched data and renders sections while the route-local model files own quality/waterfall view-model construction.
- Kept scoring, backend DTOs, database schema, broker/order boundary, and route URLs unchanged.
- Current pure LOC:
  - `page.tsx`: `341`
  - `recommendation-quality-model.ts`: `241`
  - `recommendation-waterfall-model.ts`: `202`

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test`
- passed: `cd apps/web && npm run build`
- passed: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e` (`69` tests)
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-model-decomposition-v1`
- passed: `git diff --check`
- browser QA passed for `/recommendations/AAPL-professional-2026-06-25` and `/recommendations/AAPL-2024-11-01` at 375px, 768px, and 1280px.
- screenshot QA metrics: overflow `0`, decision board present, deep disclosure open count `0`, forbidden internal copy absent.
- screenshot evidence:
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-model-decomposition-v1/local/professional-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-model-decomposition-v1/local/professional-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-model-decomposition-v1/local/professional-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-model-decomposition-v1/local/summary-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-model-decomposition-v1/local/summary-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-model-decomposition-v1/local/summary-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-model-decomposition-v1/local/summary.json`

## Remaining Risks

- `page.tsx` remains above the 250 pure LOC ceiling because evidence trace and route composition still live there. This is a legacy-large file now reduced in scope; future slices should extract evidence trace cards and product profile/order boundary helpers.
- `recommendation-quality-model.ts` is in the warning band at 241 pure LOC. Next edits to that file should split focus-item construction before adding behavior.

## Exact Next Step

- exact next step: commit the behavior-preserving refactor, push `develop`, deploy by EC2 `git pull --ff-only origin develop`, then run 13000 route smoke.
