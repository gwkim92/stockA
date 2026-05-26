# segment-specific-sotp-assumptions-v1 Handoff

## Status

- completed: contract, plan, implementation, focused tests, regression tests, frontend typecheck, compileall, diff check, full Python 3.13 suite, EC2 deploy/write smoke, route smoke, review, and final roadmap update are complete.

## Current Findings

- Reported segment inputs and allocations are already available under SOTP assumptions JSON.
- Units are normalized to values such as `USD_millions_as_reported`, so segment assumptions can cite reported units without misleading users.
- The current SOTP limitation still says segment-specific growth/CAPEX/multiple is not modeled.

## Decisions

- Add assumptions as evidence-only JSON and UI visibility.
- Do not change SOTP fair values, recommendation weights, benchmark logic, portfolio guardrails, or order boundaries.
- Use deterministic conservative assumptions first; do not call LLM or external providers for this slice.

## Exact Next Step

- exact next step: `segment-sotp-driver-calibration-v1`; replace deterministic single-period segment proxies with multi-period segment trends and industry-specific driver templates, still without changing recommendation weights.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)
- Passed: EC2 deploy fast-forwarded `/opt/stockanalysis/app` to commit `478f49f`.
- Passed: EC2 `sum-of-parts-valuation-run --execute` produced `run_id=1067`, `reported_segment_input_count=5`, `component_row_count=45`, `recommendation_scoring_mutated=false`.
- Passed: EC2 `valuation-snapshot-run --execute` produced `run_id=1068`, `snapshot_count=68`, `sum_of_parts=16`, `recommendation_scoring_mutated=false`.
- Passed: EC2 `/api/stocks/AAPL` exposes `reported_segment_assumptions` count `5`; first assumption `Americas`, `driver_label=고마진 현금창출 사업부`, `base_growth_rate=0.06`, `base_multiple=20.0`, `allocation_basis=operating_income_share`, `source_run_id=pipeline-run-1064`.
- Passed: EC2 `/api/stocks/AAPL` target range keeps `score_policy=recommendation_weights_unchanged`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order`.
- Passed: EC2 route `/stocks/AAPL` on service port `3000` renders `사업부별 가정`, `성장률·마진·밸류에이션 배수 가정`, `고마진 현금창출 사업부`, and `Americas`.

## Remaining Risks

- Segment-specific assumptions are deterministic proxies until multi-period segment history and industry-specific drivers are available.
- The assumptions are visible to users and carried through DTOs, but they do not yet create a true segment-level DCF or segment-specific CAPEX model.
