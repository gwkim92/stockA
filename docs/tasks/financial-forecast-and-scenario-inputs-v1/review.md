# financial-forecast-and-scenario-inputs-v1 Review

## Review Status

- status: completed_ec2_verified

## Implemented

- Added `market.financial_forecast_input` for scenario/year forecast inputs.
- Added `financial-forecast-inputs-run` backend CLI and deterministic SQL runner.
- Added weekly cadence and `sec-filings-weekly` profile step before `valuation-snapshot`.
- Added professional coverage expansion step so active recommendation remediation creates forecast inputs before valuation snapshots.
- Extended valuation snapshot assumptions JSON with forecast source, forecast row count, forecast confidence, and scenario rows.
- Extended frontend valuation method DTO with `forecast_evidence`.
- Updated shared valuation card to render Korean forecast input summaries.

## Guardrails Checked

- Recommendation score weights were not changed.
- Benchmark split logic was not changed.
- Automatic order and broker submit remain disabled.
- Forecast rows are evidence inputs only.

## Verification

- Passed: targeted Python tests for forecast SQL/runner/CLI.
- Passed: targeted Python tests for cadence, operating profile, professional coverage expansion.
- Passed: targeted stock detail frontend adapter contract test.
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m compileall -q src tests`.
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 946 tests in 5.155s`, `OK`).
- Passed: `cd apps/web && npm run build`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`.
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task financial-forecast-and-scenario-inputs-v1`.
- Passed: `bash scripts/verify_migrations.sh` applied `0024_financial_forecast_inputs.sql` and created `market.financial_forecast_input`.

## EC2 Verification

- Passed: commit `b68bbb5` was pushed and fast-forwarded on EC2.
- Passed: EC2 migration created `market.financial_forecast_input`.
- Passed: EC2 `financial-forecast-inputs-run` for `2026-05-26` completed with `run_id=1016`, `forecast_row_count=285`, and scenario counts `base=95`, `bear=95`, `bull=95`.
- Passed: EC2 `valuation-snapshot-run` for `2026-05-26` completed with `run_id=1017`, `financial_forecast_input_count=285`, and `snapshot_count=52`.
- Passed: EC2 temporal smoke for `recommendation-151` used matching recommendation date `2026-05-25`; forecast `run_id=1027` and valuation `run_id=1028` completed.
- Passed: `/api/stocks/NVDA`, `/api/recommendations/recommendation-151`, and `/api/theses/thesis-5` expose forecast evidence on DCF and scenario range methods with `forecast_row_count=15` and `scenario_count=3`.
- Passed: `/stocks/NVDA`, `/recommendations/recommendation-151`, and `/theses/thesis-5` render `재무 forecast 입력`, `가정 품질`, and `모델 한계와 데이터 경고 보기`.
