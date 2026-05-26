# financial-forecast-and-scenario-inputs-v1 Review

## Review Status

- status: local_verified_pending_ec2

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

## Pending

- EC2 migration, runner execution, valuation rerun, API smoke, and route smoke.
