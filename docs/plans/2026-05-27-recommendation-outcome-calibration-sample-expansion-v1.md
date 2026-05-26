# recommendation-outcome-calibration-sample-expansion-v1 Plan

## Summary

The professional analysis foundation now has many evidence layers, but recommendation weight changes remain blocked until outcome evidence is broader and more auditable. This task expands outcome and calibration evidence without changing scoring weights or order flow.

## Implementation Order

1. Inspect current recommendation outcome, paper validation, and eval schemas.
2. Measure current outcome sample size by horizon, symbol, recommendation type, and missing reason.
3. Add a reproducible runner for outcome/calibration sample expansion using existing market price history and paper validation records.
4. Store or emit component-level diagnostics for zero-weight professional components.
5. Expose calibration readiness and blockers in user-facing or operator-facing DTOs.
6. EC2-smoke the runner and route/API visibility.

## Guardrails

- No score weight changes.
- No live broker submit.
- No benchmark split changes.
- No fabricated outcomes.
- No paid providers.
