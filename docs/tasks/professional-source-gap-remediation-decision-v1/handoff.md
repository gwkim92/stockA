# professional-source-gap-remediation-decision-v1 Handoff

## Status

- in progress: local runner, CLI, and unit tests have been added. EC2 execute/remediation smoke is still pending.

## Context

- EC2 commit `44012fb` reports `professional_source_gap_prioritization.status=source_blockers_present`.
- Live top symbols are `EROK:source_blocker`, `GOOG:coverage_gap`, and `SPY:fund_not_applicable`.
- `EROK` is a true company source blocker: `sec_companyfacts_missing_us_gaap_facts`.
- `SPY` is not a failed company financial model. It is an ETF/fund not-applicable case and should stay on fund analysis surfaces.

## Exact Next Step

- exact next step: run local full verification, deploy the new CLI to EC2, execute `professional-source-gap-remediation-decision-run`, then run the selected deterministic `sum-of-parts-valuation-run` remediation for `GOOG` if it remains the next coverage gap.

## Implementation Notes

- Added backend CLI: `stockanalysis-operations professional-source-gap-remediation-decision-run --env-file <ENV> --as-of-date YYYY-MM-DD --execute`.
- The runner reads live `professional_source_gap_prioritization` from the frontend data-health SQL boundary.
- `EROK` with `sec_companyfacts_missing_us_gaap_facts` is classified as `non_remediable_current_free_public_data`; no synthetic financial facts are created.
- `GOOG` with only `sum_of_parts_component` missing is classified as `deterministic_remediation_available` with `sum-of-parts-valuation-run`.
- `SPY` remains `fund_not_applicable`; it is not treated as a failed company-financial model.
- Execute mode records the decision in `ops.pipeline_run` and `ai.eval_run`; it does not change recommendation weights or order state.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate missing financial facts.
- Do not classify ETF/fund products as failed company-financial coverage.

## Local Verification So Far

- `PYTHONPATH=src python3 -m unittest tests.test_professional_source_gap_remediation_decision`
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_professional_source_gap_remediation_decision_run_command_passes_env_and_writes_output`
