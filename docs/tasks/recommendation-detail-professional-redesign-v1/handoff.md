# recommendation-detail-professional-redesign-v1 Handoff

## Status

- partially implemented locally on `feature/professional-investment-ux-normalization-v1`.

## Implemented

- Added route-local professional header:
  `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationDecisionHeader.tsx`.
- Added CSS Module:
  `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationDecisionHeader.module.css`.
- Wired recommendation presentation view model into the recommendation detail top decision area.
- Added compatibility rendering for fixture/legacy recommendation DTOs that do not yet include professional evidence fields.
- Extracted compatibility rendering into:
  `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationCompatibilityReport.tsx`.
- Extracted compact compatibility styling into:
  `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationCompatibilityReport.module.css`.
- Reworded legacy/fallback recommendation copy from generic "기본 기록/확인한다" style to "요약형 추천 기록/판단 제한" style.
- Reworded recommendation detail header and score audit copy to avoid ambiguous investor-facing phrases such as `확인한다` and `검토 가능`.
- Replaced `미수집` visible fallbacks in recommendation price/fund helper copy with `데이터 없음`, `가격 자료 없음`, or `비용률 자료 없음`.
- Kept recommendation score, benchmark, position, broker/order boundary, DB schema, and API DTO unchanged.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm test`
- `cd apps/web && npm run build`
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`51` passed)
- Browser screenshot evidence:
  `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/recommendation-aapl-desktop.png`
  and `recommendation-aapl-mobile.png`.
- Additional browser screenshot evidence:
  `/Users/woody/ai/stockanalysis/dogfood-output/professional-investment-ux-normalization-v1/screenshots/recommendation-detail-aapl-desktop-v2.png`
  and `recommendation-detail-aapl-mobile-v2.png`.

## Remaining

- The recommendation detail page file is still oversized and needs deeper component extraction.
- The fixture fallback is intentionally basic because fixture data lacks the professional detail payload; live recommendation IDs should use the richer header and professional sections.
