# data-health-toss-runtime-section-extraction-v1 Handoff

## Status

- completed: local implementation, focused regression, build, API contract, roadmap, AWH, E2E route smoke, browser desktop/mobile `/data-health` checks, EC2 deploy, EC2 route smoke, and local tunnel smoke passed.
- scope completed: Toss broker data section extraction from `apps/web/src/app/data-health/page.tsx`.

## Current Decision

- Keep Toss as broker reality evidence only. The component preserves wording that Toss data checks account/order reality and does not replace analysis reference pricing.
- Do not change recommendation/cycle scoring or live order boundaries.
- Leave bottom runtime/provider detail panels for the next slice to keep this commit small.

## Next Step

- exact next step: implement `data-health-runtime-detail-panel-extraction-v1` by moving provider budget, active recommendation price freshness, and runtime boundary detail panels into rendering-only operations components, then run the same regression/build/E2E/browser gates.

## What Changed

- Added `apps/web/src/components/operations/DataHealthTossBrokerSection.tsx`.
- Added `apps/web/src/components/operations/DataHealthTossBrokerSection.test.tsx`.
- Replaced inline Toss broker section JSX in `apps/web/src/app/data-health/page.tsx` with display-ready props.

## Verification Evidence

- Red check before implementation:
  - `cd apps/web && npm test -- --run src/components/operations/DataHealthTossBrokerSection.test.tsx`
  - expected failure: missing `./DataHealthTossBrokerSection` import
- Focused regression:
  - `cd apps/web && npm test -- --run src/components/operations/DataHealthTossBrokerSection.test.tsx`
  - result: `1 passed`
- Typecheck:
  - `cd apps/web && npm run typecheck`
  - result: passed
- Full frontend unit:
  - `cd apps/web && npm test -- --run`
  - result: `7 passed`, `16 tests passed`
- Build:
  - `cd apps/web && npm run build`
  - result: passed
- Project gates:
  - `bash scripts/verify_frontend_api_contract.sh`
  - result: passed
  - `bash scripts/verify_project_execution_roadmap.sh`
  - result: passed
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-toss-runtime-section-extraction-v1`
  - result: passed
  - `git diff --check`
  - result: passed
- Browser/E2E:
  - fixture API: `http://127.0.0.1:8765`
  - local production web: `http://127.0.0.1:13003`
  - `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
  - result: `51 passed`
  - in-app browser `/data-health` desktop `1280x900`: overflow `0`, Toss title present, broker reality copy present, order blocked copy present, raw internal terms absent
  - in-app browser `/data-health` mobile `390x844`: overflow `0`, Toss title present, broker reality copy present, order blocked copy present, raw internal terms absent
- EC2:
  - commit deployed: `888fb771`
  - `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
  - result: passed
  - `cd /opt/stockanalysis/app/apps/web && npm run build`
  - result: passed
  - `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service`
  - result: `active`, `active`
  - EC2 route smoke: `/` `200`, `/data-health` `200`, FastAPI `__ready.status=ok`
  - local tunnel `http://127.0.0.1:13000/data-health` rendered `토스증권 브로커 데이터`, `브로커 현실 데이터`, and `증권사 주문 제출 차단`

## File Size Notes

- `apps/web/src/components/operations/DataHealthTossBrokerSection.tsx`: `61` pure LOC
- `apps/web/src/components/operations/DataHealthTossBrokerSection.test.tsx`: `26` pure LOC
- `apps/web/src/app/data-health/page.tsx`: still oversized at `5305` pure LOC

## Risks

- This is behavior-preserving and does not yet extract the bottom runtime/provider panels.
- React Doctor still reports pre-existing admin server-action auth findings outside this Toss rendering extraction.
