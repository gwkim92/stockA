# Session Handoff

## Current Status

- 상태: implemented and EC2 smoke passed.
- 기준일: 2026-05-21
- 완료:
  - Local schema, runner, recommendation, cycle, frontend, and tests are implemented.
  - Python 3.13 venv tests, Next typecheck/build, and Docker migration verification passed.
  - EC2 deployed commit `5a4b8c1`.
  - EC2 migration/seed applied. `ref.instrument_factor_exposure` has 11 rows.
  - EC2 `macro-event-propagation-run --execute` completed as `pipeline-run-45`, creating 47 propagated impact rows from 12 events across 7 instruments.
  - EC2 cycle/recommendation/thesis refresh completed as `pipeline-run-46` through `pipeline-run-49`.
  - EC2 recommendation detail includes `macro_flow_score` with `macro_flow_propagation` provenance.
  - EC2 pages `/intelligence`, `/stocks/TSLA`, `/recommendations/recommendation-2` returned HTTP 200.
  - EC2 news cluster duplicate event ids check returned `[]`.
- 막힌 점:
  - Recommendation evidence review is `needs_evidence_review` because outcome measurement is not due yet; there are no blocked gates.

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

- Let the normal performance outcome schedule create outcome rows when the recommendation measurement window matures.
- Expand factor exposure coverage beyond the starter 11 rows after more instruments/themes are active.
- Add a dedicated dashboard card for propagated macro/theme flow counts if the current stock/recommendation detail placement is not enough.

## Exact Next Step

- exact next step: monitor the next scheduled `news-intraday` and `decision-daily` runs and confirm propagated flow counts continue to update without manual intervention.
