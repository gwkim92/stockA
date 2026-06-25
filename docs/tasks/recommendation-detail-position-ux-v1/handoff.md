# recommendation-detail-position-ux-v1 Handoff

## Current Status

- 상태: implementation verified locally, EC2 deploy and browser QA pending.
- 완료:
  - `recommendation-471` runtime evidence checked.
  - API payload now includes `recommended_weight` and read-only `position_context`.
  - Recommendation detail page now renders a dedicated `포지션 현실` section with holding status, quantity, average cost, current price, market value, P&L, recommended weight, broker reference, and order boundary.
  - Task contract and handoff are in place.

## Root Cause

- `recommendation-471` is for `SPY`.
- EC2 DB has no `portfolio.position_snapshot` row for `SPY` in `Long Term Paper`; for this exact recommendation, the correct state is `not_held`, not a hidden SPY average-cost value.
- The real product gap was that `/api/recommendations/{id}` did not return any position context, so the UI could not distinguish `not held`, `held but cost basis missing`, and `broker account reference missing`.
- The fix keeps portfolio data read-only and exposes the existing position snapshots as presentation context only.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter`: `120 tests OK`.
- `PYTHONPATH=src python3 -m compileall src tests`: passed.
- `cd apps/web && npm test -- --run`: `28 passed`.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `bash scripts/verify_frontend_api_contract.sh`: passed.
- `bash scripts/verify_project_execution_roadmap.sh`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-position-ux-v1`: passed readiness checks.

## Notes

- The work should prefer fixing read model and presentation gaps over mutating portfolio/recommendation data.
- Keep broker/order boundary read-only.
- Recommendation score weights, benchmark logic, portfolio positions, and broker submit flow were not changed.
- `src/stockanalysis/frontend/live_adapter.py` and recommendation detail page are inherited oversized files; this task uses narrow adapters/components rather than broad file decomposition.

## Next Step

- exact next step: commit feature branch, merge to `develop`, deploy to EC2, then run browser QA for `/recommendations/recommendation-471` at 375px, 768px, and 1280px.
