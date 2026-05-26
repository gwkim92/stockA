# recommendation-weight-review-horizon-gate-v1 Plan

## Summary

The outcome calibration runner proved that the older quality eval can say `ready_for_weight_review` even when selected 30/90/180/365-day horizons are all not due. This task makes the manual weight review readiness path consume the new horizon-grid outcome calibration gate.

## Implementation Order

1. Inspect current recommendation weight review readiness audit and manual calibration report inputs.
2. Add latest outcome calibration eval lookup by date or explicit eval id.
3. Block readiness when calibration is missing or status is not eligible.
4. Expose the horizon-gate status and next action in audit/report payloads.
5. Update tests and EC2 smoke against `eval_run_id=27`.

## Guardrails

- No recommendation weight changes.
- No live broker submit.
- No synthetic outcomes.
- No benchmark split changes.
