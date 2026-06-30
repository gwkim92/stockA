# toss-broker-visibility-v1 Handoff

## Status

- completed: local implementation, fixture e2e, unit tests, typecheck, build, frontend API contract, roadmap verification, AWH verification, merge to `develop`, push, EC2 pull/build/restart, and EC2 route smoke all passed.
- pending rollout: none.

## Current Status

- branch: `develop`
- target routes: `/stocks/[symbol]`, `/recommendations/[recommendationId]`, `/cycle-map`, `/paper-trading`

## Completed

- Added frontend presentation helpers for broker data use and order boundary labels.
- Added a Toss broker reality card to `/stocks/[symbol]`.
- Split recommendation broker reality into a dedicated component used by recommendation position reality.
- Reworded broker labels to avoid implying Toss is already used for scoring.
- Shortened and wrapped dense Korean labels to reduce mobile/tablet line break problems.
- Added Korean labels for cycle map relation codes such as `DOMAIN_TO_SECTOR` and `TECH_DOMAIN`.
- Fixed legacy summary recommendation routing so `AAPL-2024-11-01` uses the compact compatibility report while `AAPL-professional-2026-06-25` keeps the professional detail layout.

## Verification

- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm test`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `bash scripts/verify_frontend_api_contract.sh`
- Passed: fixture-backed Playwright e2e, 69 tests:
  `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13004 npm run test:e2e`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task toss-broker-visibility-v1`
- EC2 deployed commit: `b41b993c`
- EC2 passed: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- EC2 services after restart: `stockanalysis-frontend-api.service=active`, `stockanalysis-web.service=active`, `stockanalysis-web-public-13000.service=active`
- EC2 internal route smoke passed: `/`, `/data-health`, `/stocks/AAPL`, `/paper-trading`, `/cycle-map`, `/recommendations`, `/recommendations/recommendation-522` all returned `200`.
- Local tunnel `http://127.0.0.1:13000` route smoke passed: `/`, `/data-health`, `/stocks/AAPL`, `/paper-trading`, `/cycle-map`, `/recommendations/recommendation-522` all returned `200`.
- EC2 browser QA rendered `/stocks/AAPL`, `/recommendations/recommendation-522`, `/cycle-map`, `/paper-trading` with overflow `0` and no visible `TECH_DOMAIN`, `DOMAIN TO SECTOR`, `canonical`, `shadow`, `runner`, or `artifact`.
- Screenshot evidence:
  - `/Users/woody/ai/stockanalysis/output/playwright/toss-broker-visibility-v1/ec2/stocks-AAPL.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/toss-broker-visibility-v1/ec2/recommendation-522.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/toss-broker-visibility-v1/ec2/cycle-map.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/toss-broker-visibility-v1/ec2/paper-trading.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/toss-broker-visibility-v1/ec2/summary.json`

## Remaining Risks

- The recommendation detail route file is still a legacy large file. This task only fixed the broker visibility, summary/professional split, and user-facing wording around touched sections.
- Toss data remains a broker reality and quality-check input. It is not promoted to scoring, cycle, or order execution input in this task.
- Full EC2 deployment verification must be repeated after merging this branch into `develop`.

## Exact Next Step

- exact next step: continue broader UX cleanup by reducing the remaining large recommendation detail and cycle-map route files, without changing scoring or broker/order boundaries.
