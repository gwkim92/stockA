# recommendation-outcome-due-action-router-v1 Review

## Review Notes

- The router is intentionally deterministic. It uses the same outcome sample audit as calibration and only executes the existing calibration runner when `ready_for_backfill_count > 0`.
- Price gap states are blocked rather than repaired by this router. Price repair remains a separate market-price/data collection responsibility.
- The child calibration runner can write price-based recommendation/thesis outcomes through its existing boundary; the router itself only writes `ops.pipeline_run` and `ai.eval_run`.
- Recommendation scoring weights, broker submit, order flow, benchmark definitions, portfolio positions, and rebalance actions remain disabled.
- Frontend visibility is limited to data-health; recommendation detail weight changes remain blocked until outcome/eval evidence matures.

## Verification

- Passed focused Python tests for router, CLI, cadence, orchestrator, and live adapter.
- Passed `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`.
- Passed Next.js `typecheck` and `build`.

## Residual Risk

- EC2 smoke is still pending.
- Actual live action status depends on current EC2 sample maturity; if windows remain not due, the expected router result is a no-op wait artifact.
