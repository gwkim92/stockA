# segment-specific-sotp-assumptions-v1 Handoff

## Status

- in progress: contract, plan, implementation, focused tests, regression tests, frontend typecheck, compileall, diff check, and full Python 3.13 suite are complete. EC2 deploy/write smoke, review, and final roadmap update are pending.

## Current Findings

- Reported segment inputs and allocations are already available under SOTP assumptions JSON.
- Units are normalized to values such as `USD_millions_as_reported`, so segment assumptions can cite reported units without misleading users.
- The current SOTP limitation still says segment-specific growth/CAPEX/multiple is not modeled.

## Decisions

- Add assumptions as evidence-only JSON and UI visibility.
- Do not change SOTP fair values, recommendation weights, benchmark logic, portfolio guardrails, or order boundaries.
- Use deterministic conservative assumptions first; do not call LLM or external providers for this slice.

## Exact Next Step

- exact next step: commit and deploy to EC2, rerun SOTP/valuation, and verify `/api/stocks/AAPL` plus `/stocks/AAPL` expose `reported_segment_assumptions` and `사업부별 가정`.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)

## Remaining Risks

- Segment-specific assumptions are deterministic proxies until multi-period segment history and industry-specific drivers are available.
