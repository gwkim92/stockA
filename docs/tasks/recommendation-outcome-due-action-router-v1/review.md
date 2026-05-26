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

## EC2 Result

- EC2 smoke produced `run_id=1654`, `eval_run_id=36`.
- Current live status is `no_op_wait_until_next_due_date` with `wait_until=2026-06-20`; this is expected because all 45 recommendation×30-day windows are still `not_due`.
- `/data-health` renders the new Korean router section and keeps `order_boundary=read_only_no_order`.

## Residual Risk

- The router has not yet executed the child calibration runner on EC2 because no due outcome windows exist yet.
- The next decisive smoke should be repeated on or after `2026-06-20`.
