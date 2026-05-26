# portfolio-review-decision-outcome-feedback-v1 Handoff

## Status

- completed: portfolio review decision outcome feedback now has a backend CLI runner, `ai.eval_run` persistence, live API visibility, frontend visibility, and EC2 execute/smoke evidence.
- EC2 deploy/smoke: completed on commit `c846e4c`.
- blocker handled: young decision histories classify as `too_early` instead of forcing false validation.

## Context

- Portfolio review decisions are now persisted as `ai.eval_run` artifacts via `portfolio_review_decision_history`.
- The next professional step is not to change weights. It is to measure whether saved reduce/add/hold-review decisions later align with paper validation and outcome evidence.

## Exact Next Step

- exact next step: start `portfolio-review-feedback-calibration-v1` by aggregating multiple feedback artifacts over time before any future manual weight-pilot readiness.

## Implementation Notes

- Added `src/stockanalysis/operations/portfolio_review_decision_feedback.py`.
- Added CLI command `portfolio-review-decision-outcome-feedback-run`.
- Feedback reads latest or selected `portfolio_review_decision_history` eval artifact.
- Evidence lookup joins recommendation outcomes, thesis outcomes, latest thesis state, latest paper validation, and price evidence.
- Feedback item states are `too_early`, `validated`, `contradicted`, or `needs_more_data`.
- Output is stored only as `ai.eval_run` under `portfolio_review_decision_outcome_feedback`.
- `/api/data-health` and `/api/portfolio/{portfolio}/coverage` expose latest feedback state.
- `/data-health` and `/portfolio/coverage` show Korean read-only feedback cards.

## EC2 Evidence

- EC2 commit: `c846e4c`.
- Services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- Runner: `stockanalysis-operations portfolio-review-decision-outcome-feedback-run --portfolio-name "Long Term Paper" --as-of-date 2026-05-27 --execute` completed with `run_id=1635`, `eval_run_id=32`.
- Runner output: `feedback_status=too_early`, `decision_count=11`, `too_early_count=11`, `validated_count=0`, `contradicted_count=0`, source history `eval_run_id=31`, top feedback `TSLA`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- `/api/data-health`: `portfolio_review_decision_feedback.status=loaded`, `eval_run_id=eval-run-32`, `feedback_status=too_early`, `decision_count=11`, `too_early_count=11`, top symbol `TSLA`, `broker_submit_allowed=false`.
- `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25`: `risk_budget.review_decision_feedback.status=loaded`, `eval_run_id=eval-run-32`, `feedback_status=too_early`, `decision_count=11`, top symbol `TSLA`, `broker_submit_allowed=false`.
- Route smoke returned `200` for local tunnel `http://127.0.0.1:13000/`, `/data-health`, and `/portfolio/coverage`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
