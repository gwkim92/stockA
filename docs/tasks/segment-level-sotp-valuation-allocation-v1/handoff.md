# segment-level-sotp-valuation-allocation-v1 Handoff

## Status

- completed: contract, plan, local implementation, local tests, frontend typecheck, EC2 SQL `EXPLAIN`, full Python 3.13 suite, GitHub push, EC2 deploy, EC2 runner smoke, API smoke, and route smoke are complete.

## Current Findings

- `segment-level-sotp-inputs-v1` exposed reported segment revenue, operating income, and margin.
- SOTP total fair values currently remain component-level only. There is no segment allocation view.

## Decisions

- Keep `market.sum_of_parts_component` schema unchanged.
- Allocate the existing `operating_business_fcf` component across reported segments for evidence only.
- Prefer operating-income share when total reported operating income is positive; fall back to revenue share.
- Do not change SOTP totals, recommendation weights, or order boundaries.

## Exact Next Step

- exact next step: start `reported-segment-unit-normalization-v1` so SEC segment values reported as `USD_as_reported` can show the correct filing scale, such as dollars in millions, before segment-specific valuation assumptions are built.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: EC2 Postgres `EXPLAIN` smoke for generated SOTP upsert SQL and valuation snapshot upsert SQL using the current local code, without data writes.
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-level-sotp-valuation-allocation-v1`
- Pushed: `f0fd075 Add segment-level SOTP allocations`
- EC2 deployed: `/opt/stockanalysis/app` fast-forwarded to `f0fd075`.
- Passed: EC2 `sum-of-parts-valuation-run --execute` completed with `run_id=1062`, `reported_segment_input_count=5`, `component_row_count=45`, and `recommendation_scoring_mutated=false`.
- Passed: EC2 `valuation-snapshot-run --execute` completed with `run_id=1063`, `snapshot_count=68`, method counts `dcf_lite=16`, `relative_multiple=18`, `scenario_range=18`, `sum_of_parts=16`, and `recommendation_scoring_mutated=false`.
- Passed: EC2 `apps/web` `npm run typecheck && npm run build`.
- Passed: EC2 service restart; `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active.
- Passed: EC2 API smoke for `/api/stocks/AAPL` shows `sotp_evidence.reported_segment_allocations` count `5`; first row is `Americas`, allocation basis `operating_income_share`, allocation weight `0.41257535135504364`, allocated base fair value `57.54485598738951`, allocation sum `1`, `score_policy=recommendation_weights_unchanged`, and `order_boundary=read_only_no_order`.
- Passed: route smoke for `http://127.0.0.1:13000/stocks/AAPL` returned `200 OK` and rendered `사업부별 가치 배분`, `기존 영업사업 SOTP 총액`, `Americas`, `영업이익 비중`, and `SOTP 구성요소`.

## Remaining Risks

- This is allocation evidence, not a full segment-specific DCF or multiple model.
- Segment values still use `USD_as_reported`; the next task should normalize or clearly scale values from the filing context before any segment-specific growth/multiple model is built.
