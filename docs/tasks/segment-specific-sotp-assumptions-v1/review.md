# segment-specific-sotp-assumptions-v1 Review

## Review Summary

- Accepted. The task adds evidence-only segment-level SOTP assumptions from reported segment revenue, operating income, margin, and allocation shares.
- Scope boundaries held: SOTP total fair values, recommendation score weights, benchmark logic, portfolio guardrails, and broker/order flow were not changed.
- Frontend check passed: `/stocks/AAPL` renders a Korean `사업부별 가정` section.

## Issues Found

- None blocking.
- Non-blocking: assumptions are deterministic single-period proxies. They are appropriate for visibility and review but are not yet a sell-side segment DCF.

## Residual Risks

- More robust segment assumptions need multi-period segment history, industry-specific driver templates, and segment CAPEX/capital-intensity inputs.
- Loss-making or restructuring segments may need different multiple policy than the current conservative margin/share proxy.

## Verification Evidence

- Local focused tests passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`).
- Local regression slice passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`).
- Local frontend typecheck passed: `cd apps/web && npm run typecheck`.
- Local compile/diff/full suite passed: `PYTHONPATH=src python3 -m compileall -q src tests`, `git diff --check`, and `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`).
- EC2 smoke passed on commit `478f49f`: SOTP `run_id=1067`, valuation `run_id=1068`, both with `recommendation_scoring_mutated=false`.
- EC2 API verified `/api/stocks/AAPL` exposes 5 `reported_segment_assumptions`; first assumption is `Americas` with `base_growth_rate=0.06`, `base_multiple=20.0`, and `driver_label=고마진 현금창출 사업부`.
- EC2 route smoke verified `/stocks/AAPL` renders `사업부별 가정`, `성장률·마진·밸류에이션 배수 가정`, `고마진 현금창출 사업부`, and `Americas`.
