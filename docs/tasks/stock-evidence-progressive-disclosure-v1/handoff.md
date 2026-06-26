# stock-evidence-progressive-disclosure-v1 Handoff

## Current Status

- status: implemented, verified locally, committed, pushed to `develop`, deployed to EC2, and route-smoked through `http://127.0.0.1:13000`.
- branch: `develop`
- latest implementation commit: `e099ac0b Add stock evidence disclosures`
- completed: stock evidence/source details now use summary-first decision path plus closed disclosure panels for automatic checks, story groups, source documents, and usage boundaries.
- blockers: none known.

## Implementation

- Added `StockEvidenceDisclosure` as a route-local native `<details>` disclosure component.
- Added CSS modules for disclosure layout and stock evidence focus strip.
- Kept the high-level evidence counts and the four-step evidence chain visible.
- Moved verbose quality gates, news story-group cards, source-document cards, and read-only boundary notes behind disclosure panels.
- Preserved all links to source documents, AI evidence, collected news, recommendation detail, and thesis detail.

## Verification

- passed: `git diff --check`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm test` (`14` files, `36` tests)
- passed: `cd apps/web && npm run build`
- passed after final CSS alignment tweak: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13008 npm run test:e2e` (`54` tests)
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stock-evidence-progressive-disclosure-v1`
- passed after final CSS alignment tweak: local production visual smoke for `/stocks/AAPL` and `/stocks/SPY`
  - mobile/tablet/desktop `overflow=0`
  - evidence panel disclosures present
  - top duplicated flow `false`
  - forbidden copy `false`
  - server error `false`
- passed on EC2 after deploy:
  - EC2 HEAD: `e099ac0b`
  - `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
  - `cd /opt/stockanalysis/app/apps/web && npm run build`
  - `stockanalysis-web.service`: `active`
  - `stockanalysis-frontend-api.service`: `active`
  - EC2 internal route smoke: `/`, `/stocks/AAPL`, `/stocks/SPY`, `/data-health` returned `200`
  - local tunnel route smoke: `http://127.0.0.1:13000/`, `/stocks/AAPL`, `/stocks/SPY`, `/data-health` returned `200`
  - deployed Playwright smoke on `/stocks/AAPL` and `/stocks/SPY`: mobile/tablet/desktop `overflow=0`, `details=12`, `open=0`, disclosure copy present, forbidden copy `false`, server error `false`
- screenshot evidence:
  - `output/playwright/stock-evidence-progressive-disclosure-v1/local/stocks-AAPL-evidence-desktop-v2.png`
  - `output/playwright/stock-evidence-progressive-disclosure-v1/local/stocks-SPY-evidence-desktop-v2.png`
  - `output/playwright/stock-evidence-progressive-disclosure-v1/ec2/stocks-AAPL-desktop.png`
  - `output/playwright/stock-evidence-progressive-disclosure-v1/ec2/stocks-SPY-desktop.png`

## Exact Next Step

- exact next step: continue UX normalization on the remaining dense recommendation-detail and stock-detail lower sections, using the same progressive-disclosure rule and investor-facing copy contract.
