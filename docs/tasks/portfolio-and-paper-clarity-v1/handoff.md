# portfolio-and-paper-clarity-v1 Handoff

## Status

- partially implemented locally on `feature/professional-investment-ux-normalization-v1`.

## Implemented

- Added `buildPortfolioCoverageViewModel` and `buildPaperTradingViewModel`.
- Portfolio coverage hero now foregrounds market value, unrealized profit/loss, return, and benchmark/feedback context instead of internal execution state.
- `PortfolioReturnSummaryPanel` table wrapper now has keyboard focus support for the scrollable region.
- Paper trading hero now separates simulated candidates from real orders and uses state wording:
  `실행 가능`, `안전장치 차단`, `데이터 부족`, `승인 필요`, `실거래 비활성`.
- Added `apps/web/src/app/paper-trading/PaperTradingPage.module.css` to stop the global command-grid card style from turning the first paper status card into an oversized blank block.
- Kept live broker submit blocked and did not change paper/order safety logic.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm test`
- `cd apps/web && npm run build`
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`51` passed)
- Browser screenshot evidence:
  `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/portfolio-coverage-desktop.png`
  and `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/paper-trading-desktop.png`.

## Remaining

- Portfolio and paper pages still contain deeper legacy sections. Next pass should extract position table, broker reality, and paper candidate cards into route-local components.
