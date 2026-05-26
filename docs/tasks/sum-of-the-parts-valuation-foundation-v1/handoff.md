# sum-of-the-parts-valuation-foundation-v1 Handoff

## Status

- in progress: schema, runner, CLI, operations integration, valuation aggregation, DTO/UI, and local verification are complete; commit/push and EC2 migration/run/API/route smoke are pending.

## Current Findings

- `market.valuation_snapshot` currently supports `dcf_lite`, `relative_multiple`, and `scenario_range`.
- The previous task added `market.financial_forecast_input`, and DCF/scenario methods can now read explicit forecast evidence.
- There is no canonical SOTP component table yet.
- The existing valuation DTO/card can show method-level assumptions, forecast evidence, quality, and limitations, so SOTP can be added as another method plus a component breakdown.

## Decisions

- Add `market.sum_of_parts_component` rather than hiding components only inside valuation `assumptions_json`.
- Add `sum_of_parts` as a valuation method, but keep it as evidence only.
- Use conservative proxy components first: operating business, balance-sheet adjustment, and data-gap reserve.
- Do not change recommendation weights, benchmark splits, or broker/order flow.

## Exact Next Step

- exact next step: commit/push, deploy to EC2, apply migration, run `sum-of-parts-valuation-run`, rerun `valuation-snapshot-run`, and smoke API/routes.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_recommendation_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_thesis_detail_response_matches_frontend_contract_shape`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `bash scripts/verify_migrations.sh` applied through `0025_sum_of_parts_valuation.sql` and created `market.sum_of_parts_component`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task sum-of-the-parts-valuation-foundation-v1`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 952 tests in 5.216s`, `OK`)
- Passed: `cd apps/web && npm run build`
- Note: default `python3` maps to Python 3.14 and full unittest fails there due local `pyexpat`/missing `fastapi`; project verification uses `/private/tmp/stockanalysis-verify-venv/bin/python`.
- Pending: EC2 migration/run/API/route smoke.

## Remaining Risks

- The first SOTP model is not segment-level SOTP. It is a conservative component evidence foundation until segment data and footnote parsing exist.
- Symbols with sparse assets/liabilities/share count or forecast evidence may have partial SOTP coverage.
- Recommendation weight changes remain blocked until evaluation evidence supports them.
