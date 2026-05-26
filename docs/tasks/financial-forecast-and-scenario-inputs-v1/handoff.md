# financial-forecast-and-scenario-inputs-v1 Handoff

## Status

- completed: forecast table, runner, CLI, automation profile, professional coverage expansion, valuation assumptions, API DTO, UI, local verification, and EC2 migration/run/API/route smoke are complete.

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

- exact next step: begin `sum-of-the-parts-valuation-foundation-v1` with a new task contract before adding any SOTP valuation evidence layer.

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
- Passed: commit `b68bbb5` was pushed to `origin/codex/local-mvp-runtime-aws-bootstrap` and fast-forwarded on EC2 `/opt/stockanalysis/app`.
- Passed: EC2 migration applied `0024_financial_forecast_inputs.sql`; `market.financial_forecast_input` exists.
- Passed: EC2 Next build and service restart; `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active, `/__health` returns `status=ok`, and the home route returned 41304 bytes.
- Passed: EC2 `financial-forecast-inputs-run --as-of-date 2026-05-26 --statement-scope annual --execute` completed with `run_id=1016`, `forecast_row_count=285`, scenario counts `base=95`, `bear=95`, `bull=95`, and `recommendation_scoring_mutated=false`.
- Passed: EC2 `valuation-snapshot-run --as-of-date 2026-05-26 --statement-scope annual --execute` completed with `run_id=1017`, `financial_forecast_input_count=285`, `snapshot_count=52`, method counts `dcf_lite=16`, `relative_multiple=18`, `scenario_range=18`, and `recommendation_scoring_mutated=false`.
- Passed: EC2 same-day recommendation smoke for `recommendation-151` required temporal alignment because the recommendation is dated `2026-05-25`; `financial-forecast-inputs-run` `run_id=1027` and `valuation-snapshot-run` `run_id=1028` completed for `2026-05-25`.
- Passed: EC2 API smoke showed forecast evidence available on `/api/stocks/NVDA`, `/api/recommendations/recommendation-151`, and `/api/theses/thesis-5`; DCF and scenario range methods each expose `forecast_row_count=15`, `scenario_count=3`, and the matching forecast `as_of_date`.
- Passed: EC2 route smoke for `/stocks/NVDA`, `/recommendations/recommendation-151`, and `/theses/thesis-5` rendered `재무 forecast 입력`, `가정 품질`, and `모델 한계와 데이터 경고 보기`.

## Remaining Risks

- The first forecast model is deterministic and coarse; it should be labeled as forecast input evidence, not a precise analyst model.
- Forecast rows depend on available SEC/companyfacts and normalized metrics; symbols with sparse financials may stay uncovered.
- This task still does not add sum-of-the-parts valuation.
