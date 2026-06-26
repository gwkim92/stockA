# stock-evidence-progressive-disclosure-v1 Contract

## Task Request

- request: Continue the stock detail UX cleanup by reducing the dense evidence/source area on `/stocks/[symbol]`.
- request: Keep all evidence available, but make the investor page summary-first and progressively disclose detailed validator, story-group, source-document, and boundary information.

## Goal

- goal: `/stocks/AAPL` and `/stocks/SPY` should show the news/evidence connection as a concise decision path first, with deeper automatic checks, story groups, source documents, and usage boundaries hidden behind clear Korean disclosure panels.

## Scope

- Add reusable route-local disclosure UI for stock evidence details.
- Keep the stock evidence summary and decision path visible.
- Move quality-gate details, story-group details, source-document details, and usage-boundary details into closed disclosure panels.
- Keep route URL, backend DTO, recommendation score, portfolio data, and broker/order boundary unchanged.

## Non Goals

- No API DTO change.
- No DB schema change.
- No recommendation weight change.
- No broker submit or live order automation.
- No new paid UI/chart dependency.
- No global page redesign outside the stock evidence section.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/[symbol]/_components/StockEvidenceNeighborhoodPanel.tsx`
  - `apps/web/src/app/stocks/[symbol]/_components/StockEvidenceDisclosure.tsx`
  - `apps/web/src/app/stocks/[symbol]/_components/StockEvidenceDisclosure.module.css`
  - `apps/web/src/app/stocks/[symbol]/_components/StockEvidenceNeighborhoodPanel.module.css`
  - `docs/tasks/stock-evidence-progressive-disclosure-v1/*`
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
- verification command: visual smoke for `/stocks/AAPL` and `/stocks/SPY` at mobile/tablet/desktop against the changed local production build.
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stock-evidence-progressive-disclosure-v1`

## Acceptance Criteria

- Evidence/source detail remains accessible through disclosures.
- `/stocks/AAPL` and `/stocks/SPY` have no horizontal overflow at 375px, 768px, and 1280px.
- Investor-facing text does not expose forbidden process wording such as `확인한다`, `봐야 한다`, `검토 가능`, or `미수집`.
- The screen does not show duplicate top-level research flow blocks.
- No recommendation, portfolio, or broker/order behavior changes.
