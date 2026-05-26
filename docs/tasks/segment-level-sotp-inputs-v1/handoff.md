# segment-level-sotp-inputs-v1 Handoff

## Status

- in progress: local implementation and focused verification are complete. EC2 deploy/smoke and final roadmap evidence are still pending.

## Current Findings

- Previous task produced AAPL reported segment rows on EC2: revenue and operating income for Americas, Europe, Greater China, Japan, and Rest of Asia Pacific.
- Current SOTP already stores segment evidence rows, but the frontend does not present them as paired segment revenue/operating-income inputs.

## Decisions

- Use assumptions JSON rather than a new table for the first segment-input visibility layer.
- Keep SOTP component valuation math conservative and unchanged in this task.
- Treat segment inputs as valuation evidence, not automatic recommendation scoring inputs.

## Exact Next Step

- exact next step: deploy the committed changes to EC2, rerun `sum-of-parts-valuation-run` and `valuation-snapshot-run`, and verify `/api/stocks/AAPL` exposes non-empty `sotp_evidence.reported_segment_inputs`.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: EC2 Postgres `EXPLAIN` smoke for generated SOTP upsert SQL and valuation snapshot upsert SQL using the current local code, without data writes.

## Remaining Risks

- A full segment-level SOTP still needs segment-specific growth, margin, capital intensity, and multiple/DCF assumptions.
