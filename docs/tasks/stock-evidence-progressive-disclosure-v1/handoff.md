# stock-evidence-progressive-disclosure-v1 Handoff

## Current Status

- status: local implementation, e2e, and visual smoke completed; commit/deploy are next.
- branch: `develop`
- completed: stock evidence/source details now use summary-first decision path plus closed disclosure panels for automatic checks, story groups, source documents, and usage boundaries.
- blockers: none known locally.

## Implementation

- Added `StockEvidenceDisclosure` as a route-local native `<details>` disclosure component.
- Added CSS modules for disclosure layout and stock evidence focus strip.
- Kept the high-level evidence counts and the four-step evidence chain visible.
- Moved verbose quality gates, news story-group cards, source-document cards, and read-only boundary notes behind disclosure panels.
- Preserved all links to source documents, AI evidence, collected news, recommendation detail, and thesis detail.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test` (`14` files, `36` tests)
- passed: `cd apps/web && npm run build`
- passed after final CSS alignment tweak: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13008 npm run test:e2e` (`54` tests)
- passed after final CSS alignment tweak: local production visual smoke for `/stocks/AAPL` and `/stocks/SPY`
  - mobile/tablet/desktop `overflow=0`
  - evidence panel disclosures present
  - top duplicated flow `false`
  - forbidden copy `false`
  - server error `false`
- screenshot evidence:
  - `output/playwright/stock-evidence-progressive-disclosure-v1/local/stocks-AAPL-evidence-desktop-v2.png`
  - `output/playwright/stock-evidence-progressive-disclosure-v1/local/stocks-SPY-evidence-desktop-v2.png`

## Exact Next Step

- exact next step: run `git diff --check` and AWH verify, commit, push `develop`, deploy to EC2, rebuild/restart Next, and smoke `/stocks/AAPL` and `/stocks/SPY`.
