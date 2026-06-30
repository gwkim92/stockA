# toss-broker-visibility-v1 Handoff

## Status

- completed: local implementation, fixture e2e, unit tests, typecheck, build, frontend API contract, and roadmap verification passed.
- pending rollout: merge to `develop`, EC2 pull/rebuild/restart, and EC2 route smoke.

## Current Status

- branch: `feature/toss-broker-visibility-v1`
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
- Passed before final summary-route fix: live EC2 route smoke for `/`, `/data-health`, `/stocks/AAPL`, `/paper-trading`; Toss sync and read-only account status were successful.

## Remaining Risks

- The recommendation detail route file is still a legacy large file. This task only fixed the broker visibility, summary/professional split, and user-facing wording around touched sections.
- Toss data remains a broker reality and quality-check input. It is not promoted to scoring, cycle, or order execution input in this task.
- Full EC2 deployment verification must be repeated after merging this branch into `develop`.

## Exact Next Step

- exact next step: commit the verified branch, merge it into `develop`, deploy by pulling `develop` on EC2, and repeat route smoke on `http://127.0.0.1:13000`.
