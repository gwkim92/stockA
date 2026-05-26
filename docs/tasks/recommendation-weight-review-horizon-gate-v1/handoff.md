# recommendation-weight-review-horizon-gate-v1 Handoff

## Status

- completed: implemented locally, pushed, deployed to EC2, and smoked against the live DB.

## Context

- EC2 outcome calibration execute `run_id=1595`, `eval_run_id=27` returned `no_due_outcome_window`.
- The older recommendation quality eval nested in that run returned `ready_for_weight_review`.
- This contradiction means the manual weight review audit path must consume the new horizon-grid calibration gate before any future pilot weight review can be considered.

## Exact Next Step

- exact next step: move to `recommendation-outcome-maturity-monitor-v1` so the system tracks when the currently `not_due` recommendation horizons become measurable and reruns outcome calibration at the right cadence.

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

## EC2 Verification

- deployed commit: `b3e2915`
- passed: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_recommendation_weight_review_readiness_audit tests.test_manual_weight_review_calibration_report tests.test_frontend_live_adapter`
- passed: `cd apps/web && npm run typecheck && npm run build`
- passed: `stockanalysis-operations recommendation-weight-review-readiness-audit-run --as-of-date 2026-05-27 --outcome-calibration-eval-run-id 27 --execute`
- EC2 result: `run_id=1598`, `audit_eval_run_id=28`, `source_eval_run_id=26`, `source_quality_status=ready_for_weight_review`, `outcome_calibration_eval_run_id=27`, `outcome_calibration_status=no_due_outcome_window`, `decision=blocked_by_outcome_calibration_no_due_outcome_window`, `manual_weight_review_allowed=false`, `automatic_weight_change_allowed=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `recommendation_scoring_mutated=false`.
- passed: `/api/data-health` exposes `recommendation_weight_review_readiness.status=blocked_by_outcome_calibration_no_due_outcome_window`, `manual_weight_review_allowed=false`, `outcome_calibration_status=no_due_outcome_window`, `outcome_calibration_eval_run_id=eval-run-27`.
- passed: `/data-health` renders `수동 weight 검토`, `성과 측정일 대기`, `추천 성과검증`, and `차단`.
- passed: `bash scripts/verify_project_execution_roadmap.sh`

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate outcomes.
- Do not bypass the new horizon-grid gate with the older quality eval alone.
