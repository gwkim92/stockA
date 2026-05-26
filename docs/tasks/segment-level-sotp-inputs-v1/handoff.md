# segment-level-sotp-inputs-v1 Handoff

## Status

- completed: local implementation, verification, GitHub push, EC2 deploy, EC2 SOTP/valuation rerun, API smoke, and route smoke are complete.

## Current Findings

- Previous task produced AAPL reported segment rows on EC2: revenue and operating income for Americas, Europe, Greater China, Japan, and Rest of Asia Pacific.
- Current SOTP already stores segment evidence rows, but the frontend does not present them as paired segment revenue/operating-income inputs.

## Decisions

- Use assumptions JSON rather than a new table for the first segment-input visibility layer.
- Keep SOTP component valuation math conservative and unchanged in this task.
- Treat segment inputs as valuation evidence, not automatic recommendation scoring inputs.

## Exact Next Step

- exact next step: start `segment-level-sotp-valuation-allocation-v1` to derive explicit segment-level valuation allocation evidence from reported segment inputs without changing recommendation weights.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: EC2 Postgres `EXPLAIN` smoke for generated SOTP upsert SQL and valuation snapshot upsert SQL using the current local code, without data writes.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-level-sotp-inputs-v1`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)
- Pushed: `705d8a2 Add segment-level SOTP inputs`
- EC2 deployed: `/opt/stockanalysis/app` fast-forwarded to `705d8a2`.
- Passed: EC2 `sum-of-parts-valuation-run --execute` completed with `run_id=1060`, `reported_segment_input_count=5`, `component_row_count=45`, and `recommendation_scoring_mutated=false`.
- Passed: EC2 `valuation-snapshot-run --execute` completed with `run_id=1061`, `snapshot_count=68`, method counts `dcf_lite=16`, `relative_multiple=18`, `scenario_range=18`, `sum_of_parts=16`, and `recommendation_scoring_mutated=false`.
- Passed: EC2 `apps/web` `npm run typecheck && npm run build`.
- Passed: EC2 service restart; `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active.
- Passed: EC2 API smoke for `/api/stocks/AAPL` shows `sotp_evidence.reported_segment_inputs` count `5`; first row is `Americas`, revenue `178353`, operating income `72480`, operating margin `0.4063850902423845`, `score_policy=recommendation_weights_unchanged`, and `order_boundary=read_only_no_order`.
- Passed: route smoke for `http://127.0.0.1:13000/stocks/AAPL` returned `200 OK` and rendered `사업부별 실적 입력`, `Americas`, `영업마진`, and `SOTP 구성요소`.

## Remaining Risks

- A full segment-level SOTP still needs segment-specific growth, margin, capital intensity, and multiple/DCF assumptions.
- Apple values currently retain `USD_as_reported` because the parser conservatively preserves the filing table's reported scale; a later unit-normalization task should derive "millions" context from surrounding prose.
