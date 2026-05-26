# portfolio-review-feedback-calibration-v1 Handoff

## Status

- completed: runner, CLI, read-only API payloads, data-health UI, portfolio coverage UI, tests, typecheck/build, AWH, EC2 deployment, execute smoke, and route/API smoke are complete.
- EC2 deploy/smoke: completed on commit `932c562`.
- blocker handled: sparse feedback classifies as `insufficient_history`, not readiness.

## Context

- Single-run feedback can say whether one saved review history is too early, validated, contradicted, or needs more data.
- The next step is not to change weights. It is to aggregate feedback over enough histories to decide whether a future manual pilot review is even eligible.

## Exact Next Step

- exact next step: start `portfolio-review-feedback-cadence-v1` so feedback and calibration are rerun when outcome windows mature instead of relying on ad-hoc manual execution.

## Implementation Notes

- Added `src/stockanalysis/operations/portfolio_review_feedback_calibration.py`.
- Added CLI command `portfolio-review-feedback-calibration-run`.
- Reads recent `portfolio_review_decision_outcome_feedback` `ai.eval_run` artifacts over a bounded lookback.
- Aggregates feedback by decision family, decision type, and symbol.
- Emits one of `insufficient_history`, `collect_more_feedback`, `contradiction_review_required`, or `manual_review_ready`.
- Stores only an audit `ai.eval_run` under `portfolio_review_feedback_calibration`.
- Exposes latest calibration on `/api/data-health` and `/api/portfolio/{portfolio}/coverage`.
- Frontend shows calibration on `/data-health` and `/portfolio/coverage`.
- Recommendation scoring, benchmark composition, portfolio positions, rebalance, broker submit, and order flow remain unchanged.

## EC2 Evidence

- EC2 commit: `932c562`.
- Services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- Runner: `stockanalysis-operations portfolio-review-feedback-calibration-run --portfolio-name "Long Term Paper" --as-of-date 2026-05-27 --execute` completed with `run_id=1636`, `eval_run_id=33`.
- Runner output: `calibration_status=insufficient_history`, `feedback_run_count=1`, `decision_count=11`, `mature_decision_count=0`, `too_early_count=11`, `validated_count=0`, `contradicted_count=0`, family counts `benchmark_drift=7`, `position_sizing=4`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- `/api/data-health`: `portfolio_review_feedback_calibration.status=loaded`, `eval_run_id=eval-run-33`, `calibration_status=insufficient_history`, `feedback_run_count=1`, `decision_count=11`, `too_early_count=11`, `broker_submit_allowed=false`.
- `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25`: `risk_budget.review_feedback_calibration.status=loaded`, `eval_run_id=eval-run-33`, `calibration_status=insufficient_history`, `feedback_run_count=1`, `decision_count=11`, top family `benchmark_drift`, `broker_submit_allowed=false`.
- Route smoke returned `200` for local tunnel and EC2 local web on `/`, `/data-health`, and `/portfolio/coverage`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat sparse histories as `insufficient_history`, not readiness.
- Even `manual_review_ready` does not change weights automatically; it only allows a future separately approved manual pilot review task.
