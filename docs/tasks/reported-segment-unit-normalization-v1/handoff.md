# reported-segment-unit-normalization-v1 Handoff

## Status

- in progress: contract, plan, local implementation, focused tests, regression tests, frontend typecheck, compileall, diff check, and full Python 3.13 suite are complete. EC2 deploy/write smoke and final roadmap update are pending.

## Current Findings

- Simple segment fixture already infers `USD_millions_as_reported` because the table caption contains `in millions`.
- Apple transposed fixture includes `(dollars in millions)` in a paragraph before the table, so the previous table-only unit inference can miss it.

## Decisions

- Do not convert stored values to absolute dollars yet.
- Use normalized unit labels to prevent user misunderstanding while preserving reported values.
- Do not change SOTP totals, recommendation weights, benchmark logic, or order boundaries.

## Exact Next Step

- exact next step: implement table-neighborhood unit inference, update tests, and rerun focused verification.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)

## Remaining Risks

- Broader unit normalization may require issuer-specific text patterns beyond millions/thousands.
