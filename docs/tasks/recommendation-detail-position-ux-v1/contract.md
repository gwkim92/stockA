# recommendation-detail-position-ux-v1 Contract

## Task Request

- request: Improve `http://127.0.0.1:13000/recommendations/recommendation-471`.
- request: Explain and fix why holding position and average cost are not visible on the recommendation detail page.
- request: Renew the page UX/UI using a professional investment research workspace structure inspired by Bloomberg-like analyst terminals, adapted to this product.

## Goal

- goal: Recommendation detail should show the user what the recommendation is, whether the portfolio already holds the symbol, the position size and average cost when available, the current price context, the thesis/evidence stack, paper/order boundary, and what to review next in a professional Korean investment report layout.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/components/recommendation-position-reality.tsx`
  - `apps/web/src/components/recommendation-position-reality.module.css`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/presentation/`
  - `apps/web/src/components/research/`
  - related tests
  - `docs/tasks/recommendation-detail-position-ux-v1/`

## Invariants

- No recommendation score weight changes.
- No benchmark, portfolio position, or paper validation mutation.
- No broker submit or live order flow.
- No paid provider or external service.
- API changes must remain read-only and backward compatible.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-position-ux-v1`
- verification command: Playwright smoke for `/recommendations/recommendation-471` at 375px, 768px, 1280px.

## Acceptance Criteria

- The page clearly shows holding status, quantity/market value/weight, and average cost if the data exists.
- If average cost does not exist in source data, the page says why and where the blocker lives.
- The visible structure follows `decision → position reality → evidence stack → valuation/financials → risk/order boundary → next actions`.
- Investor-facing copy does not expose internal runner/pipeline/artifact terminology.
- Existing order boundary remains `read_only_no_order`.
