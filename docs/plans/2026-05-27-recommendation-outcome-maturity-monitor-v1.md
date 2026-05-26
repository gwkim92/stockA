# recommendation-outcome-maturity-monitor-v1 Plan

## Summary

The weight review horizon gate now correctly blocks manual review because selected recommendation outcome windows are not due. The next task makes that waiting state operational: show when outcome windows become due, whether the monthly outcome job is stale, and what exact runner should execute next.

## Implementation Order

1. Inspect the latest calibration sample audit schema and data-health payload.
2. Add an outcome maturity monitor projection or runner with next due date, due count, overdue count, and price-gap blockers.
3. Expose the monitor on `/api/data-health` and `/data-health` in Korean.
4. Add tests proving that `not_due` does not become weight-review readiness.
5. Smoke on EC2 without changing recommendation weights or broker/order state.

## Guardrails

- No recommendation weight changes.
- No synthetic outcome rows.
- No automatic broker/order submit.
- No benchmark split changes.
