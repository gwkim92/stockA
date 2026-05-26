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

## Result

- Implemented in commits `5de2ef8` and `8c3cbb1`.
- Added `recommendation-outcome-calibration-sample-expansion-run`, which combines outcome backfill preview/execute, horizon-grid sample audit, quality eval, and component diagnostics without score or order changes.
- Added `/api/data-health` and `/data-health` visibility for recommendation outcome calibration readiness.
- EC2 execute `run_id=1595` wrote `eval_run_id=27`. The result is `no_due_outcome_window`: 45 active recommendations across 30/90/180/365-day horizons produce 180 recommendation-horizon rows, all currently `not_due`, with zero outcome rows and zero backfill candidates.
- The older quality eval still returned `ready_for_weight_review`, so the next task must make manual weight review readiness depend on this new horizon-grid gate.
