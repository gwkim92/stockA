# portfolio-review-feedback-calibration-v1 Handoff

## Status

- completed: local runner, CLI, read-only API payloads, data-health UI, portfolio coverage UI, focused tests, and typecheck are in place.
- in progress: full local regression, AWH verification, commit/push, EC2 deployment, execute smoke, and route/API smoke.

## Context

- Single-run feedback can say whether one saved review history is too early, validated, contradicted, or needs more data.
- The next step is not to change weights. It is to aggregate feedback over enough histories to decide whether a future manual pilot review is even eligible.

## Exact Next Step

- exact next step: run full regression, push the completed task, deploy to EC2, execute `portfolio-review-feedback-calibration-run --execute`, and confirm `/api/data-health` plus `/api/portfolio/Long%20Term%20Paper/coverage` expose `portfolio_review_feedback_calibration` without enabling weights or orders.

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

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat sparse histories as `insufficient_history`, not readiness.
- Even `manual_review_ready` does not change weights automatically; it only allows a future separately approved manual pilot review task.
