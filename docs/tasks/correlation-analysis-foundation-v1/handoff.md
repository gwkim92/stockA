# correlation-analysis-foundation-v1 Handoff

## Status

- implemented locally; EC2 migration/run/smoke is the next step.

## Current Status

- 상태: local implementation and verification passed.
- 기준일: 2026-06-14
- 완료:
  - `signal.asset_correlation_snapshot` migration added.
  - `stockanalysis-operations correlation-analysis-run` added.
  - `asset-correlation-daily` cadence metadata added.
  - `cross-asset-daily` operating profile now runs the correlation step after regime/news linkage and before zero-weight recommendation cross-asset components.
  - `/market-map` API and page expose correlation summaries as co-movement only, not causality.
- 막힌 점:
  - EC2 has not yet applied migration `0031_asset_correlation_snapshot.sql`.
  - EC2 has not yet run `correlation-analysis-run --execute`.

## Implemented

- DB: `db/migrations/0031_asset_correlation_snapshot.sql` creates an idempotent rolling correlation snapshot table.
- Backend: `src/stockanalysis/operations/correlation_analysis.py` computes 20/60/120 day rolling return correlation and beta for active recommendation/portfolio instruments versus benchmark/sector assets and market indicators.
- CLI: `correlation-analysis-run --env-file <ENV> --as-of-date YYYY-MM-DD --execute` is registered in `src/stockanalysis/operations/cli.py`.
- Cadence/orchestration: `asset-correlation-daily` is registered in data-health cadence and in `cross-asset-daily` operating profile.
- API/UI: `/market-map` receives `correlations` and renders a Korean section explaining which assets moved together without making causal claims.

## Verification

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_correlation_analysis tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_cross_asset_market tests.test_correlation_analysis`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_correlation_analysis tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_frontend_live_adapter tests.test_cross_asset_market`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task correlation-analysis-foundation-v1`

## Exact Next Step

- exact next step: commit and push to `develop`, deploy to EC2 by `git pull --ff-only origin develop`, apply migration `0031_asset_correlation_snapshot.sql`, run `stockanalysis-operations correlation-analysis-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-14 --execute`, then smoke `/api/market-map` and `/market-map` for non-empty correlation rows.

## Notes

- This task adds statistical co-movement analysis. It does not replace existing ontology/exposure propagation and must not make causal claims.
- Recommendation scoring weights, benchmark definitions, portfolio positions, and broker/order flow were not changed.
