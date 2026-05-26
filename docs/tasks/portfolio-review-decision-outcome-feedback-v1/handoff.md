# portfolio-review-decision-outcome-feedback-v1 Handoff

## Status

- in progress: local implementation is complete; full verification and EC2 smoke pending.
- blocker handled: young decision histories classify as `too_early` instead of forcing false validation.

## Context

- Portfolio review decisions are now persisted as `ai.eval_run` artifacts via `portfolio_review_decision_history`.
- The next professional step is not to change weights. It is to measure whether saved reduce/add/hold-review decisions later align with paper validation and outcome evidence.

## Exact Next Step

- exact next step: run full local verification, deploy to EC2, execute `portfolio-review-decision-outcome-feedback-run`, and confirm `/api/data-health` plus `/api/portfolio/Long%20Term%20Paper/coverage` expose the feedback artifact.

## Implementation Notes

- Added `src/stockanalysis/operations/portfolio_review_decision_feedback.py`.
- Added CLI command `portfolio-review-decision-outcome-feedback-run`.
- Feedback reads latest or selected `portfolio_review_decision_history` eval artifact.
- Evidence lookup joins recommendation outcomes, thesis outcomes, latest thesis state, latest paper validation, and price evidence.
- Feedback item states are `too_early`, `validated`, `contradicted`, or `needs_more_data`.
- Output is stored only as `ai.eval_run` under `portfolio_review_decision_outcome_feedback`.
- `/api/data-health` and `/api/portfolio/{portfolio}/coverage` expose latest feedback state.
- `/data-health` and `/portfolio/coverage` show Korean read-only feedback cards.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
