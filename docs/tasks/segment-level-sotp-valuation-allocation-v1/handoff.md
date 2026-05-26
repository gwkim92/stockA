# segment-level-sotp-valuation-allocation-v1 Handoff

## Status

- in progress: contract, plan, local implementation, local tests, frontend typecheck, EC2 SQL `EXPLAIN`, and full Python 3.13 suite are complete. EC2 deploy/write smoke and final roadmap update are pending.

## Current Findings

- `segment-level-sotp-inputs-v1` exposed reported segment revenue, operating income, and margin.
- SOTP total fair values currently remain component-level only. There is no segment allocation view.

## Decisions

- Keep `market.sum_of_parts_component` schema unchanged.
- Allocate the existing `operating_business_fcf` component across reported segments for evidence only.
- Prefer operating-income share when total reported operating income is positive; fall back to revenue share.
- Do not change SOTP totals, recommendation weights, or order boundaries.

## Exact Next Step

- exact next step: implement SQL, DTO, and frontend allocation visibility, then run focused tests.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: EC2 Postgres `EXPLAIN` smoke for generated SOTP upsert SQL and valuation snapshot upsert SQL using the current local code, without data writes.
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)

## Remaining Risks

- This is allocation evidence, not a full segment-specific DCF or multiple model.
