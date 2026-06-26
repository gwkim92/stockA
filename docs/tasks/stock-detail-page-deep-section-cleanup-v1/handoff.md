# stock-detail-page-deep-section-cleanup-v1 Handoff

## Current Status

- status: implementation verified locally
- branch: `develop`
- completed: duplicated stock-detail research flow removed, deep sections decomposed, local type/test/build/e2e/visual smoke completed.
- blockers: none known locally; EC2 deploy/smoke remains the next operational step.

## Notes

- Starting point: `/stocks/AAPL` renders but the full-page visual smoke shows the page is too long and appears to repeat top-level analysis sections.
- Root cause identified so far: `StockResearchHeader` already includes a compact "이 종목에서 먼저 볼 것" reading map, but `page.tsx` renders a second `ProfessionalResearchFlow` with the same business/financial/valuation/news/thesis/paper layers.

## Implementation

- Removed the duplicated `ProfessionalResearchFlow` block from `/stocks/[symbol]`; the header reading map is now the only top-level navigation/summary.
- Extracted deep stock detail sections into route-local components:
  - `StockPriceAndMarketSections`
  - `StockRecommendationPositionPanel`
  - `StockValuationResearchPanel`
  - `StockNewsImpactSections`
- Reduced `apps/web/src/app/stocks/[symbol]/page.tsx` from 888 pure LOC at the start of this cleanup to 219 pure LOC.
- Replaced awkward portfolio fallback copy such as `추천 원장 대기` with user-facing portfolio/valuation data absence labels.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test` (`14` files, `36` tests)
- passed: `cd apps/web && npm run build`
- first local changed-build e2e attempt against `127.0.0.1:13008` failed because the local Next process did not receive the FastAPI read token and rendered API `401` errors. This was an environment issue, not a UI regression.
- passed after injecting the EC2 read token into the local Next process environment: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13008 npm run test:e2e` (`54` tests)
- visual smoke captured changed local production build screenshots:
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/stocks-AAPL-mobile.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/stocks-AAPL-tablet.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/stocks-AAPL-desktop.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/stocks-SPY-mobile.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/stocks-SPY-tablet.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/stocks-SPY-desktop.png`
- viewport screenshots were also captured to avoid long-page full-page stitching artifacts:
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/viewport/stocks-AAPL-desktop-1.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/viewport/stocks-AAPL-desktop-2.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/viewport/stocks-AAPL-desktop-3.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/viewport/stocks-SPY-desktop-1.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/viewport/stocks-SPY-desktop-2.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/viewport/stocks-SPY-desktop-3.png`
- visual checks: `stocks/AAPL` and `stocks/SPY` at mobile/tablet/desktop reported `overflow=0`, duplicated top flow `false`, server error `false`.
- DOM duplicate check: `h1` count `1`, stock header count `1`, price section count `1`, direct news section count `1`. The repeated areas seen in full-page screenshots were Playwright long-page stitching artifacts, not duplicate DOM.
- final visual smoke on the changed local production build saved viewport screenshots under `output/playwright/stock-detail-page-deep-section-cleanup-v1/final/`; representative desktop screenshots are:
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/final/stocks-AAPL-desktop.png`
  - `output/playwright/stock-detail-page-deep-section-cleanup-v1/final/stocks-SPY-desktop.png`

## Exact Next Step

- exact next step: run final repository checks, commit the task, push `develop`, deploy via EC2 `git pull --ff-only origin develop`, rebuild/restart Next, and run route smoke on `/stocks/AAPL` and `/stocks/SPY`.
