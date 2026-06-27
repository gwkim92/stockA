# recommendation-detail-top-density-v1 Handoff

## Status

- completed: implementation, local route smoke, screenshot QA, frontend contract, roadmap verification, Next typecheck/build/test/e2e, commit/push, and EC2 rollout smoke all passed.
- pending rollout: none.

## Current Status

- local implementation complete; EC2 deployment pending.
- branch: `develop`
- target route: `/recommendations/[recommendationId]`

## Implementation Notes

- Preserve backend/API/scoring/order boundaries.
- Replaced the equal-weight executive summary cards with a single editorial decision brief, compact decision line, reading path, and compact metric strip.
- Removed the separate `RecommendationProductOverview` block from the recommendation detail top section to avoid repeated product/position copy.
- Removed the separate top `RecommendationFocusPanel` render and folded the first actionable focus item into the decision waterfall.
- Removed the now-dead `RecommendationFocusPanel` export and stale `.recommendation-focus-*` CSS selectors.
- Inlined the single-use recommendation brief formatter helpers into `RecommendationExecutiveBrief` instead of adding a one-use shared file.
- Reduced the position reality grid by moving portfolio/order-boundary context into a summary band.
- Normalized visible `UNKNOWN` copy and `/stocks/UNKNOWN` links in recommendation detail professional flow/audit panels to the actual recommendation symbol.
- Added e2e coverage for the compact decision board: no focus panel, decision line visible, position summary visible, first waterfall card starts with the next-check callout, and no `UNKNOWN` body copy.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test` (`14` files, `36` tests)
- passed: `cd apps/web && npm run build`
- passed: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13009 npm run test:e2e -- --workers=1` (`60` tests)
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `git diff --check`
- local route check: `http://127.0.0.1:13009/recommendations/AAPL-2024-11-01` returned `200` with no `UNKNOWN`, `검토 가능`, `확인한다`, `봐야 한다`, `미수집`, or Server Components render text.
- local screenshot QA:
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/local-final/mobile-375.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/local-final/tablet-768.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/local-final/desktop-1280.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/local-final/qa.json`
- screenshot QA metrics: overflow `0`, product overview count `0`, focus panel count `0`, decision line count `1`, position summary count `1`, waterfall cards `8`, unknown copy `false`, forbidden copy `false` at 375/768/1280.
- visual QA revise findings resolved:
  - `뉴스·사이클` visible recommendation-detail copy was changed to `뉴스와 사이클` to avoid punctuation-led Korean wraps.
  - `AAPL · 분석 입력 차단` waterfall heading was shortened to `AAPL · 입력 차단`.
  - visible `blocked until 근거 검토` copy was mapped to `근거 검토 전까지 차단`.
- final screenshot QA metrics after those fixes: overflow `0`, product overview count `0`, focus panel count `0`, decision line count `1`, position summary count `1`, waterfall cards `8`, unknown copy `false`, forbidden copy `false`, compact heading `true`, Korean evidence copy `true`, focus CSS leak `false` at 375/768/1280.
- note: `RecommendationProductOverview` component remains in `apps/web/src/components/recommendation-product-overview.tsx` because this file still provides the `RecommendationQualityDecision` type used by active recommendation detail panels. The product overview render is not used in `/recommendations/[recommendationId]`.
- first attempted full e2e failed because the local Next server lacked `STOCKANALYSIS_FRONTEND_API_READ_TOKEN` and FastAPI returned 401. After restarting the local Next server with the EC2 runtime read token injected into process env, the same suite passed. The token value was not printed.
- EC2 deployed commit: `78e32dac`.
- EC2 passed: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`.
- EC2 services after restart: `stockanalysis-web.service=active`, `stockanalysis-frontend-api.service=active`.
- EC2 route smoke passed:
  - `/` -> `200`
  - `/recommendations/AAPL-2024-11-01` -> `200`
  - `/recommendations` -> `200`
  - `/data-health` -> `200`
- EC2 recommendation detail HTML checks:
  - `데이터 서버 연결 중단=0`
  - `UNKNOWN=0`
  - `뉴스·사이클=0`
  - `blocked until=0`
  - `AAPL · 분석 입력 차단=0`
  - `추천 상세 핵심 판단=2`
  - `recommendation-focus-panel=0`
- Local tunnel route `http://127.0.0.1:13000/recommendations/AAPL-2024-11-01` returned latest content with the same forbidden-copy checks passing.
- EC2 screenshot QA:
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/ec2/mobile-375.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/ec2/tablet-768.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/ec2/desktop-1280.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/recommendation-detail-top-density-v1/ec2/qa.json`
- EC2 screenshot QA metrics: overflow `0`, product overview count `0`, focus panel count `0`, decision line count `1`, position summary count `1`, waterfall cards `8`, unknown copy `false`, forbidden copy `false`, focus CSS leak `false` at 375/768/1280.

## Exact Next Step

- exact next step: continue the broader UX normalization on the next highest-traffic decision screen: `/stocks/[symbol]` top-density and company-vs-ETF distinction, using the same screenshot/e2e gate.
