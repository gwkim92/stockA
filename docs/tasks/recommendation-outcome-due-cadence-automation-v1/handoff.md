# recommendation-outcome-due-cadence-automation-v1 Handoff

## Status

- pending: this is the immediate next task after `recommendation-outcome-maturity-monitor-v1`.

## Context

- EC2 maturity monitor reports `status=not_due`, `next_due_date=2026-06-20`, `next_due_count=19`.
- `recommendation_weight_review_readiness` remains `blocked_by_outcome_calibration_no_due_outcome_window`.
- The monitor is visible, but scheduler/cadence still needs to use it as an operational trigger.

## Exact Next Step

- exact next step: inspect the existing data operations cadence/profile scheduler definitions and decide how to trigger or request `recommendation-outcome-calibration-sample-expansion-run` when maturity status becomes `due_outcomes_ready` or `overdue_outcomes_ready`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate outcomes.
- Do not treat `not_due` as a failure.
