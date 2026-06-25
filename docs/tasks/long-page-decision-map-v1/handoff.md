# long-page-decision-map-v1 Handoff

## Current Status

- 상태: completed; implemented, pushed to `develop`, deployed to EC2, and smoke tested through `http://127.0.0.1:13000`.
- 진행 중: no implementation work remains for this task.
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
- Repository and deployment verification completed:
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter`
  - `bash scripts/verify_frontend_api_contract.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task long-page-decision-map-v1`
  - EC2 deploy commit `b67e444e`; `stockanalysis-web.service`, `stockanalysis-web-public-13000.service`, and `stockanalysis-frontend-api.service` all active.
  - EC2 internal `http://127.0.0.1:13000/portfolio/coverage` and `/data-health` returned 200 and rendered the new decision map copy.
  - Local tunnel `http://127.0.0.1:13000` Playwright smoke passed at 375px and 1280px with missing text `[]`, horizontal overflow `0`, console issues `[]`.

## Next Step

- exact next step: continue the professional workspace redesign by splitting the remaining dense sections of `/portfolio/coverage` and `/data-health` into focused components or dedicated detail subpages; do not change recommendation weights or order boundaries.
