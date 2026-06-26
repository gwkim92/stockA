# stock-detail-professional-redesign-v1 Handoff

## Status

- partially implemented locally on `feature/professional-investment-ux-normalization-v1`.

## Implemented

- Added route-local professional stock header:
  `apps/web/src/app/stocks/[symbol]/_components/StockResearchHeader.tsx`.
- Added CSS Module:
  `apps/web/src/app/stocks/[symbol]/_components/StockResearchHeader.module.css`.
- Wired stock presentation view model into `/stocks/[symbol]`.
- Header now distinguishes product type, price move, holding state, average cost / position reality where available, and analysis status before the long research sections.
- Reworded stock header and presentation view model copy from task-like instructions to judgment-oriented descriptions.
- Replaced raw broker/provider status exposure such as `분석 기준 가격 · missing` with `분석 기준 가격 · 원천 대기`.
- Replaced visible `미수집` copy in fund price/expense helpers and price-data aria label with user-facing data-state wording.
- Kept backend DTO, scoring, broker/order boundary, and DB schema unchanged.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm test`
- `cd apps/web && npm run build`
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`51` passed)
- Browser screenshot evidence:
  `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/stock-aapl-desktop.png`
  and `stock-aapl-mobile.png`.
- Additional browser screenshot evidence after provider-label cleanup:
  `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/stock-aapl-desktop-v3.png`
  and `stock-aapl-mobile-v3.png`.

## Remaining

- The stock detail page file is still oversized. Company and ETF/fund sections need further extraction in the next pass.
- Deeper sections still contain some legacy wording and should be moved behind explicit view-model mappings as they are extracted.
