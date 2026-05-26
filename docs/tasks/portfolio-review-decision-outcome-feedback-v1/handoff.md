# portfolio-review-decision-outcome-feedback-v1 Handoff

## Status

- in progress: this is the next task after `portfolio-review-decision-history-v1`.
- blockers: outcome windows may still be `not_due` until 2026-06-20; the runner must handle `too_early` cleanly.

## Context

- Portfolio review decisions are now persisted as `ai.eval_run` artifacts via `portfolio_review_decision_history`.
- The next professional step is not to change weights. It is to measure whether saved reduce/add/hold-review decisions later align with paper validation and outcome evidence.

## Exact Next Step

- exact next step: inspect recommendation outcome, paper validation, thesis, and price history joins that can classify saved review decisions as `too_early`, `validated`, `contradicted`, or `needs_more_data`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
