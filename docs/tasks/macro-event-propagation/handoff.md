# Session Handoff

## Current Status

- 상태: implemented locally, EC2 smoke pending.
- 기준일: 2026-05-21
- 완료:
  - Local schema, runner, recommendation, cycle, frontend, and tests are implemented.
  - Python 3.13 venv tests, Next typecheck/build, and Docker migration verification passed.
- 막힌 점:
  - EC2 deploy/smoke has not run yet in this handoff state.

## Implemented

- Added `ref.instrument_factor_exposure` and `signal.propagated_instrument_impact` in `db/migrations/0014_macro_event_propagation.sql`.
- Added starter exposure seed in `db/seeds/0003_factor_exposure_seed.sql` for `SPY`, `QQQ`, `TLT`, `XLF`, `XLE`, `NVDA`, `MSFT`, `TSLA`, `XOM`.
- Added `stockanalysis.signal.macro_event_propagation` with:
  - candidate lookup from `event.event_classification_impact`
  - factor exposure propagation
  - idempotent upsert into `signal.propagated_instrument_impact`
  - `run_macro_event_propagation(... execute=True|False)`
- Added operations CLI command:
  - `stockanalysis-operations macro-event-propagation-run --as-of-date YYYY-MM-DD --limit 200 --execute`
- Added the propagation step to the `news-intraday` operating-data profile after RSS enrichment, cluster evidence, and AI evidence.
- Extended cycle snapshot event heat to count both direct event impacts and propagated macro/theme impacts.
- Extended recommendation scoring with `macro_flow_score`; default component weight is `0.10`, configurable with `STOCKANALYSIS_RECOMMENDATION_MACRO_FLOW_WEIGHT`.
- Extended live API/frontend:
  - stock detail now includes `macro_flow_impacts`
  - stock page separates 상위 흐름 전파 from 직접 뉴스
  - recommendation detail provenance links `macro_flow_score` to `macro_flow_propagation`
  - intelligence wording now treats macro/theme-only news as valid upstream flow.

## Verification

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_macro_event_propagation tests.test_recommendation_bootstrap tests.test_cycle_state_snapshot tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/test-venv/bin/python -m unittest discover -s tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `bash scripts/verify_migrations.sh`
- Failed only in unsupported local default `python3` path: `PYTHONPATH=src python3 -m unittest discover -s tests` because default Python is Homebrew Python 3.14 with known `pyexpat` breakage and missing FastAPI dependency. The project MVP runtime uses Python 3.13 venv.

## Remaining

- Apply migration/seed on EC2.
- Run `macro-event-propagation-run --execute` on EC2.
- Verify `signal.propagated_instrument_impact` row count.
- Restart API/web services after deploying code.
- Smoke `/intelligence`, `/stocks/SPY`, and a recommendation detail page.
- Confirm `/api/ai/news-clusters` duplicate event ids stay empty.

## Exact Next Step

- exact next step: push the implementation branch, deploy it to EC2, apply `db/migrations/0014_macro_event_propagation.sql` and `db/seeds/0003_factor_exposure_seed.sql`, then run `macro-event-propagation-run --execute` against the EC2 database.
