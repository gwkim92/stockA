# correlation-risk-visibility-v1 Contract

## Task Request

- request: Continue from `correlation-analysis-foundation-v1` by removing duplicate/self correlation pairs and exposing stock/recommendation correlation risk context.
- context: EC2 smoke showed duplicate pairs such as `QQQ ↔ Nasdaq 100 ETF` and duplicated ETF instrument/indicator comparisons. The market map is useful, but stock and recommendation detail pages do not yet show correlation context.

## Goal

- goal: Correlation snapshots should avoid self/proxy duplicate pairs, and stock/recommendation detail pages should show recent co-movement risks as read-only context.

## Scope

- Include:
  - filter self/proxy correlation pairs in the correlation runner.
  - clear same-date/lookback rows before upsert so stale duplicate rows disappear after rerun.
  - add `market_correlations` to stock detail API payload.
  - add `market_correlations` to recommendation detail API payload.
  - render market co-movement sections on `/stocks/[symbol]` and `/recommendations/[recommendationId]`.
  - unit and frontend contract tests.
- Exclude:
  - recommendation score/weight changes.
  - benchmark definition changes.
  - portfolio position changes.
  - broker/order flow.
  - causal claims from correlation.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/correlation_analysis.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/`
  - `docs/tasks/correlation-risk-visibility-v1/*`

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_correlation_analysis tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task correlation-risk-visibility-v1`

## Acceptance Criteria

- Self/proxy pairs such as `instrument:QQQ` versus `indicator:QQQ` are filtered.
- Duplicate comparison asset pairs prefer indicator metadata over raw ETF instrument duplicates.
- Stock detail shows co-movement context without implying causality.
- Recommendation detail shows co-movement risk context without changing total score or order boundary.
- Rerunning the correlation task removes stale duplicate rows for the target date/lookbacks.
