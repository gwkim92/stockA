# professional-source-gap-remediation-decision-v1 Handoff

## Status

- completed: local runner/CLI, SEC shares mapping remediation, EC2 decision execute, GOOG source refresh, SOTP rerun, and data-health smoke are complete.

## Context

- EC2 commit `44012fb` reports `professional_source_gap_prioritization.status=source_blockers_present`.
- Live top symbols are `EROK:source_blocker`, `GOOG:coverage_gap`, and `SPY:fund_not_applicable`.
- `EROK` is a true company source blocker: `sec_companyfacts_missing_us_gaap_facts`.
- `SPY` is not a failed company financial model. It is an ETF/fund not-applicable case and should stay on fund analysis surfaces.

## Exact Next Step

- exact next step: start `professional-source-blocker-raw-filing-remediation-v1` for the remaining true source blocker `EROK`. Do not fabricate EROK financial facts; inspect raw filing/XBRL or alternate public filing feasibility.

## Implementation Notes

- Added backend CLI: `stockanalysis-operations professional-source-gap-remediation-decision-run --env-file <ENV> --as-of-date YYYY-MM-DD --execute`.
- The runner reads live `professional_source_gap_prioritization` from the frontend data-health SQL boundary.
- `EROK` with `sec_companyfacts_missing_us_gaap_facts` is classified as `non_remediable_current_free_public_data`; no synthetic financial facts are created.
- `GOOG` with only `sum_of_parts_component` missing is classified as `deterministic_remediation_available` with `sum-of-parts-valuation-run`.
- `SPY` remains `fund_not_applicable`; it is not treated as a failed company-financial model.
- Execute mode records the decision in `ops.pipeline_run` and `ai.eval_run`; it does not change recommendation weights or order state.
- EC2 decision execute: `professional-source-gap-remediation-decision-run` completed with `run_id=1599`, `eval_run_id=29`, `decision_status=next_deterministic_remediation_available`.
- EC2 top gap decision: `EROK` classified as `non_remediable_current_free_public_data` because current SEC companyfacts lacks `facts.us-gaap` financial facts.
- EC2 selected remediation: `GOOG` classified as `deterministic_remediation_available` for `sum_of_parts_component`.
- Root cause found during remediation: GOOG SEC companyfacts uses `CommonStockSharesOutstanding`; the normalizer only mapped `EntityCommonStockSharesOutstanding`, so SOTP had no shares input.
- Added SEC companyfacts mapping for `CommonStockSharesOutstanding`, `WeightedAverageNumberOfDilutedSharesOutstanding`, and `WeightedAverageNumberOfSharesOutstandingBasic`.
- EC2 GOOG SEC companyfacts rerun: `run_id=1601`, `fact_count=926`, metric codes include `shares_outstanding`, `instrument_symbol=GOOG`.
- EC2 SOTP rerun after shares mapping: `run_id=1602`, `component_row_count=60`, `sotp_context_count=22`, `recommendation_scoring_mutated=false`.
- EC2 `/api/data-health` after remediation: `gap_count=2`, `source_blocker_count=1`, `coverage_gap_count=0`, `fund_not_applicable_count=1`, symbols `EROK:source_blocker`, `SPY:fund_not_applicable`, `order_boundary=read_only_no_order`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate missing financial facts.
- Do not classify ETF/fund products as failed company-financial coverage.

## Local Verification So Far

- `PYTHONPATH=src python3 -m unittest tests.test_professional_source_gap_remediation_decision`
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_professional_source_gap_remediation_decision_run_command_passes_env_and_writes_output`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_source_gap_remediation_decision tests.test_data_operations_cli.DataOperationsCliTests.test_professional_source_gap_remediation_decision_run_command_passes_env_and_writes_output tests.test_frontend_live_adapter`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-source-gap-remediation-decision-v1`

## EC2 Verification

- EC2 commit: `7b8fe1a`.
- `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_sec_companyfacts tests.test_professional_source_gap_remediation_decision`
- `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- `bash scripts/verify_project_execution_roadmap.sh`
- `stockanalysis-operations professional-source-gap-remediation-decision-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-05-26 --execute`
- `stockanalysis-ingest sec-companyfacts-upsert --cik 0001652044 --fallback-symbol GOOG`
- `stockanalysis-operations sum-of-parts-valuation-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-05-26 --execute`
- `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service`
- Route smoke: `/`, `/data-health`, `/stocks/GOOG` all returned HTTP `200`.
