# recommendation-weight-review-horizon-gate-v1 Handoff

## Status

- in progress: local implementation is complete; EC2 deployment/smoke is pending.

## Context

- EC2 outcome calibration execute `run_id=1595`, `eval_run_id=27` returned `no_due_outcome_window`.
- The older recommendation quality eval nested in that run returned `ready_for_weight_review`.
- This contradiction means the manual weight review audit path must consume the new horizon-grid calibration gate before any future pilot weight review can be considered.

## Exact Next Step

- exact next step: deploy to EC2, run `recommendation-weight-review-readiness-audit-run --execute`, and confirm the latest `eval_run_id=27` outcome calibration gate blocks manual weight review with `blocked_by_outcome_calibration_no_due_outcome_window`.

## Local Implementation Notes

- `recommendation_weight_review_readiness_audit` now reads the latest or explicitly selected `recommendation_outcome_calibration_sample_expansion` eval before deciding manual weight review readiness.
- A `ready_for_weight_review` quality eval is no longer sufficient by itself. Outcome calibration status must be `ready_for_manual_weight_review`.
- Missing calibration, `no_due_outcome_window`, `backfill_candidates_remain`, `price_history_gaps_remain`, and `no_outcome_sample_available` all block manual weight review.
- Audit JSON now includes `outcome_calibration_gate`, and `/data-health` exposes `recommendation_weight_review_readiness` so the user-facing status shows why weight review is blocked.
- CLI now accepts `--outcome-calibration-eval-run-id` for explicit horizon-gate selection.

## Local Verification

- passed: `PYTHONPATH=src python3 -m unittest tests.test_recommendation_weight_review_readiness_audit tests.test_manual_weight_review_calibration_report tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate outcomes.
- Do not bypass the new horizon-grid gate with the older quality eval alone.
