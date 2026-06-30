# recommendation-detail-route-helper-decomposition-v1 Handoff

## Status

- in progress: implementation complete locally; verification and rollout are pending.

## Current Status

- branch: `develop`
- target route: `/recommendations/[recommendationId]`

## Implementation Notes

- Added `recommendation-product-model.ts` for product profile, order boundary label, decision boundary copy, and professional-detail gating.
- Added `recommendation-evidence-trace-model.ts` for evidence trace card construction and evidence route/link labels.
- Updated `page.tsx` so it composes fetched data and renders sections, while route-local model files own helper logic.
- Kept recommendation scoring, backend DTOs, database schema, broker/order boundary, and route URLs unchanged.
- Current pure LOC:
  - `page.tsx`: `153`
  - `recommendation-product-model.ts`: `49`
  - `recommendation-evidence-trace-model.ts`: `132`
  - `recommendation-quality-model.ts`: `241`
  - `recommendation-waterfall-model.ts`: `202`

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test`
- passed: `cd apps/web && npm run build`
- passed: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e` (`69` tests)
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-route-helper-decomposition-v1`
- passed: `git diff --check`
- browser QA passed for `/recommendations/AAPL-professional-2026-06-25` and `/recommendations/AAPL-2024-11-01` at 375px, 768px, and 1280px.
- screenshot QA metrics: overflow `0`, professional trace present, summary route compact rendering present, deep disclosure open count `0`, forbidden internal copy absent.
- screenshot evidence:
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-route-helper-decomposition-v1/local/professional-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-route-helper-decomposition-v1/local/professional-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-route-helper-decomposition-v1/local/professional-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-route-helper-decomposition-v1/local/summary-mobile.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-route-helper-decomposition-v1/local/summary-tablet.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-route-helper-decomposition-v1/local/summary-desktop.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-route-helper-decomposition-v1/local/summary.json`

## Remaining Risks

- `recommendation-quality-model.ts` remains in the warning band at `241` pure LOC from the prior slice. The next edit touching quality/focus copy should split focus item construction first.
- This task does not change recommendation score, broker order flow, or data freshness behavior; it only reduces route file responsibility.

## Exact Next Step

- exact next step: commit the behavior-preserving helper split, push `develop`, deploy by EC2 `git pull --ff-only origin develop`, then run 13000 route smoke.
