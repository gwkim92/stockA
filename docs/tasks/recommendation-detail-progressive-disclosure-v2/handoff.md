# recommendation-detail-progressive-disclosure-v2 Handoff

## Current Status

- completed: implemented, pushed to `develop`, deployed to EC2, and route/screenshot smoke passed.
- branch: `develop`
- commit: `9683f4b7`
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
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-progressive-disclosure-v2`: passed.
- EC2 `git pull --ff-only origin develop`: fast-forwarded to `9683f4b7`.
- EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck`: passed.
- EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`: passed.
- EC2 services after restart: `stockanalysis-web.service=active`, `stockanalysis-frontend-api.service=active`.
- EC2 internal route smoke: `/`, `/recommendations/AAPL-2024-11-01`, `/recommendations`, `/data-health` all returned `200`.
- Local tunnel route smoke: `http://127.0.0.1:13000/`, `/recommendations/AAPL-2024-11-01`, `/recommendations`, `/data-health` all returned `200`.
- EC2 browser QA for `/recommendations/AAPL-2024-11-01` at 375px, 768px, 1280px: no horizontal overflow, 5 disclosure groups, 0 open by default, no forbidden copy, no server error.
- EC2 screenshots:
  - `output/playwright/recommendation-detail-progressive-disclosure-v2/ec2/recommendation-AAPL-mobile.png`
  - `output/playwright/recommendation-detail-progressive-disclosure-v2/ec2/recommendation-AAPL-tablet.png`
  - `output/playwright/recommendation-detail-progressive-disclosure-v2/ec2/recommendation-AAPL-desktop.png`

## Exact Next Step

- exact next step: Start the next UX slice by reducing first-half recommendation detail density: executive brief cards, decision waterfall, and position reality should become more visual and less card-heavy without changing backend DTOs or scoring.
