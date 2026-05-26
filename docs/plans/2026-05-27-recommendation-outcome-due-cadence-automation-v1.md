# recommendation-outcome-due-cadence-automation-v1 Plan

## Summary

The system now knows when outcome windows are not due and when the next measurable window opens. The next step is to connect that maturity state to operations cadence so due windows trigger the correct backfill/calibration workflow while preserving the no-weight-change rule.

## Implementation Order

1. Inspect data operations cadence and profile scheduler definitions.
2. Add or adjust a read-only cadence signal for recommendation outcome due work.
3. Surface the exact next command/action in `/data-health`.
4. Add tests for `not_due`, `due_outcomes_ready`, `overdue_outcomes_ready`, and price-gap states.
5. Smoke on EC2 without mutating weights or broker/order state.

## Guardrails

- No recommendation weight changes.
- No synthetic outcomes.
- No automatic broker/order submit.
- No benchmark split changes.
