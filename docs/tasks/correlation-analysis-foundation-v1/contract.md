# correlation-analysis-foundation-v1 Contract

## Task Request

- request: Add first-class statistical correlation analysis that is separate from existing news/theme exposure propagation.
- context: Current system has `event.news_indicator_link`, `ref.instrument_factor_exposure`, and propagated impacts, but no rolling return correlation or beta analysis.

## Goal

- goal: Active recommendation and portfolio instruments can be compared against core market indicators and benchmark/sector assets with rolling 20/60/120 day correlation and beta snapshots, visible as read-only market context.

## Scope

- Include:
  - `signal.asset_correlation_snapshot` migration.
  - `stockanalysis-operations correlation-analysis-run --as-of-date YYYY-MM-DD --execute`.
  - daily cadence metadata for data-health.
  - market-map API payload and UI summary for strongest correlations.
  - unit tests for SQL generation and CLI registration.
- Exclude:
  - recommendation score/weight changes.
  - broker/order flow.
  - causal claims from correlation.
  - paid data providers or external vector/graph services.

## Mutable Surface

- mutable surface:
  - `db/migrations/`
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/market-map/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `tests/`
  - `docs/tasks/correlation-analysis-foundation-v1/*`

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_correlation_analysis tests.test_data_operations_cli tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_cross_asset_market`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task correlation-analysis-foundation-v1`

## Acceptance Criteria

- Rolling correlation and beta snapshots are idempotently upserted.
- Correlation output states that it is co-movement, not causality.
- `/market-map` can show correlation summary without mutating recommendations.
- Recommendation weights, benchmark definitions, portfolio positions, and broker/order boundary remain unchanged.
