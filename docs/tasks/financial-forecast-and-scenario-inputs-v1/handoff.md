# financial-forecast-and-scenario-inputs-v1 Handoff

## Status

- in progress: forecast table, runner, CLI, automation profile, professional coverage expansion, valuation assumptions, API DTO, UI, and local verification are complete; EC2 migration/run/API/route smoke is pending.

## Current Findings

- `market.valuation_snapshot` already stores method-level assumptions JSON and the frontend now renders method assumptions, sensitivity, data quality, and limitations.
- Current DCF-lite still uses a single FCF/share, growth rate, discount rate, and terminal growth rate.
- There is no canonical table for future revenue, margin, CAPEX intensity, or FCF forecast rows.
- `sec-filings-weekly` profile previously ran valuation snapshot directly after peer relative analysis; this task inserts forecast inputs before valuation snapshot.

## Decisions

- Add a deterministic forecast input table rather than hiding forecast assumptions only inside `valuation_snapshot.assumptions_json`.
- Forecast rows are evidence only. Recommendation weights, benchmark splits, and order flow remain unchanged.
- First slice uses public financial statement data and normalized metrics already in Postgres; missing inputs are explicit rather than guessed aggressively.
- Schema change is explicit: new `market.financial_forecast_input` table.

## Exact Next Step

- exact next step: commit/push, deploy to EC2, apply migration, run `financial-forecast-inputs-run`, rerun `valuation-snapshot-run`, and smoke API/routes.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis.ProfessionalEquityAnalysisTests.test_financial_forecast_inputs_preview_sql_is_read_only tests.test_professional_equity_analysis.ProfessionalEquityAnalysisTests.test_financial_forecast_inputs_upsert_sql_creates_scenarios_without_recommendation_mutation tests.test_professional_equity_analysis.ProfessionalEquityAnalysisTests.test_run_financial_forecast_inputs_dry_run_reads_preview_without_writes tests.test_professional_equity_analysis.ProfessionalEquityAnalysisTests.test_run_financial_forecast_inputs_execute_records_pipeline_and_upsert_summary tests.test_data_operations_cli.DataOperationsCliTests.test_financial_forecast_inputs_run_command_passes_env_and_guardrails`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_coverage_expansion tests.test_operating_data_orchestrator tests.test_data_operations_cadence`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape tests.test_professional_equity_analysis tests.test_data_operations_cli.DataOperationsCliTests.test_financial_forecast_inputs_run_command_passes_env_and_guardrails`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m compileall -q src tests`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 946 tests in 5.155s`, `OK`)
- Passed: `cd apps/web && npm run build`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task financial-forecast-and-scenario-inputs-v1`
- Passed: `bash scripts/verify_migrations.sh` applied through `0024_financial_forecast_inputs.sql` and created `market.financial_forecast_input`.
- Pending: EC2 migration/run/API/route smoke.

## Remaining Risks

- The first forecast model is deterministic and coarse; it should be labeled as forecast input evidence, not a precise analyst model.
- Forecast rows depend on available SEC/companyfacts and normalized metrics; symbols with sparse financials may stay uncovered.
- This task still does not add sum-of-the-parts valuation.
