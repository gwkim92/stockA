# stock-detail-page-deep-section-cleanup-v1 Contract

## Task Request

- request: Continue the professional investment UX/UI normalization work by cleaning the stock detail route after the recommendation detail and header cleanup.
- request: Make `/stocks/[symbol]` read like a single investment research report, not a repeated process explanation or backend status page.

## Goal

- goal: `/stocks/AAPL` and `/stocks/SPY` should render one clear stock/fund research report with a single top-level reading map, decomposed sections, user-facing Korean copy, visible price/position/recommendation context, and no duplicated professional research flow.

## Scope

- Remove duplicate top-level explanation from the stock detail page when the header already provides the reading map.
- Keep route URL, backend DTO, recommendation score, benchmark, portfolio position, and broker/order boundary unchanged.
- Reduce `apps/web/src/app/stocks/[symbol]/page.tsx` by moving deep sections into route-local components where practical.
- Keep company stock and ETF/fund product boundaries visible.
- Keep user-facing Korean copy; do not expose internal terms in investor-facing sections.

## Non Goals

- No DB schema change.
- No API DTO change.
- No recommendation weight change.
- No real broker submit or order automation.
- No paid external UI/charting dependency.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/_components/*`
  - `docs/tasks/stock-detail-page-deep-section-cleanup-v1/*`
- do not mutate:
  - backend API DTOs
  - database schema
  - recommendation scoring weights
  - benchmark definitions
  - portfolio positions
  - broker submit/order boundary
  - secrets or deployment configuration

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:<local-production-port> npm run test:e2e`
- verification command: visual smoke for `/stocks/AAPL` and `/stocks/SPY` against the changed local production build, then EC2 route smoke after deploy when applicable.
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stock-detail-page-deep-section-cleanup-v1`

## Acceptance Criteria

- `/stocks/[symbol]` keeps the existing URL and API contract.
- The duplicated `ProfessionalResearchFlow` no longer appears below `StockResearchHeader`.
- `page.tsx` is reduced to data loading and section composition; deep content lives in route-local components.
- Company stock and ETF/fund detail surfaces remain distinct.
- Investor-facing route content does not expose internal execution terms as visible copy.
