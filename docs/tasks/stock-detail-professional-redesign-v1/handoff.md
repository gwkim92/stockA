# stock-detail-professional-redesign-v1 Handoff

## Status

- decomposition slice implemented locally on `feature/professional-investment-ux-normalization-v1`.

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
- Extracted the large stock detail display sections into route-local components:
  `StockFinancialStatementModelPanel`,
  `StockFundInstrumentAnalysisPanel`,
  `StockIndustryCompetitivePositionPanel`,
  `StockProfessionalEvidenceAuditPanel`,
  `StockProfessionalSourceGuardrailPanel`,
  `StockEvidenceNeighborhoodPanel`,
  `StockStoryGroupSection`,
  `StockEvidenceSourceSection`,
  and local presentation helpers.
- Reduced `apps/web/src/app/stocks/[symbol]/page.tsx` from `2,033` lines / about `1,944` pure LOC at the start of this task sequence to `888` pure LOC in this slice.
- Kept each newly extracted stock component/model under the 250 pure LOC limit. The largest new file is `stock-professional-layer-model.ts` at `204` pure LOC.
- Changed deeper stock detail source/status wording away from raw internal source codes where the section was moved, including order boundary and source blocker labels.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm test`
- `cd apps/web && npm run build`
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`51` passed)
- Latest decomposition verification:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm test` (`14` files, `36` tests)
  - pure LOC check for the changed stock route/components
- Browser screenshot evidence:
  `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/stock-aapl-desktop.png`
  and `stock-aapl-mobile.png`.
- Additional browser screenshot evidence after provider-label cleanup:
  `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/stock-aapl-desktop-v3.png`
  and `stock-aapl-mobile-v3.png`.

## Remaining

- The stock detail page is still larger than the target architecture budget (`888` pure LOC), but the most problematic professional audit, source guardrail, financial model, ETF/fund, industry, and AI evidence neighborhood sections are now separated.
- Remaining stock page sections that can be extracted later: price/correlation, recommendation/position, equity research/valuation, macro-flow/direct-news.
- Browser QA and e2e hard-gate evidence still need to be refreshed after portfolio/paper/data-health cleanup.
