# long-page-decision-map-v1 Handoff

## Current Status

- 상태: implemented locally; repository-level verification is in progress.
- 진행 중: repository-level regression, commit, develop merge, push, EC2 deploy, and deployed route smoke remain.
- 완료: reusable `PageDecisionMap` component is implemented and wired to `/portfolio/coverage` and `/data-health` with local frontend verification.
- implemented: reusable `PageDecisionMap` component added under `apps/web/src/components/research/`.
- wired locally: `/portfolio/coverage` now opens with a portfolio review order map for return, risk budget, rebalance candidates, positions, and outcome/order boundary.
- wired locally: `/data-health` now opens with an operations review order map for overall status, collection coverage, quality audit, AI/provider health, and scheduler state.
- preserved: frontend API DTOs, backend behavior, recommendation weights, benchmark, portfolio positions, and broker/order boundary.

## Notes

- Existing `/portfolio/coverage` and `/data-health` pages remain oversized. This task intentionally adds a reading-order layer without splitting those pages yet.
- The component describes the review order in Korean, uses semantic anchor links, and keeps internal execution terms out of the visible guide copy.
- Local verification completed before handoff update:
  - `cd apps/web && npm test -- --run`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Playwright viewport smoke at 375px, 768px, 1280px for `/portfolio/coverage` and `/data-health`; missing text `[]`, horizontal overflow `0`, console issues `[]`.

## Next Step

- exact next step: finish repository-level regression, commit the feature branch, merge into `develop`, push, deploy to EC2, then smoke `/portfolio/coverage` and `/data-health` through `http://127.0.0.1:13000`.
