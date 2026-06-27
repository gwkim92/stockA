# recommendation-detail-progressive-disclosure-v2 Handoff

## Current Status

- in progress: implemented locally; EC2 deployment pending.
- branch: `develop`
- target route: `/recommendations/[recommendationId]`

## Implementation Notes

- Preserve backend/API/scoring/order boundaries.
- Use route-local CSS Modules and native `<details>` disclosure components.
- Keep investor-facing summaries visible; move deep audit/source/score internals into progressive disclosure.
- Added `RecommendationDetailDisclosure`, `RecommendationQualityBoundaryPanel`, `RecommendationEquityResearchPanel`, and `RecommendationEvidenceReviewPanel`.
- Replaced deep inline sections in `page.tsx` with route-local components and closed disclosure groups.
- Removed investor-visible `source_pipeline` copy from the financial statement source blocker panel.
- Added an e2e assertion that recommendation detail deep evidence sections are collapsed by default.

## Verification

- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm test`: passed, 14 files / 36 tests.
- `cd apps/web && npm run build`: passed.
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13008 npm run test:e2e`: passed, 57 tests.
- Local browser QA for `/recommendations/AAPL-2024-11-01` at 375px, 768px, 1280px: no horizontal overflow, 5 disclosure groups, 0 open by default, no forbidden copy, no server error.
- Local screenshots:
  - `output/playwright/recommendation-detail-progressive-disclosure-v2/local/recommendation-AAPL-mobile.png`
  - `output/playwright/recommendation-detail-progressive-disclosure-v2/local/recommendation-AAPL-tablet.png`
  - `output/playwright/recommendation-detail-progressive-disclosure-v2/local/recommendation-AAPL-desktop.png`

## Exact Next Step

- exact next step: Run `git diff --check` and AWH verify, commit the scoped UX changes, push `develop`, deploy to EC2 with `git pull --ff-only origin develop`, then record EC2 route smoke and screenshot evidence in this handoff.
