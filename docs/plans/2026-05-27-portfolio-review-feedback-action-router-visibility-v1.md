# portfolio-review-feedback-action-router-visibility-v1 Plan

## Summary

- Goal: make action-router outcomes understandable in the cockpit.
- Rationale: a professional operating system must show not only that a scheduler ran, but whether it waited, executed feedback, executed calibration, or blocked on guardrails.

## Implementation Order

1. Add live adapter SQL for latest `portfolio_review_feedback_action_router`.
2. Normalize action-router payload fields and guardrails.
3. Add payload to `/api/data-health` and portfolio coverage risk budget.
4. Add concise Korean sections on `/data-health` and `/portfolio/coverage`.
5. Add focused tests, Next typecheck/build, roadmap verify, and AWH verify.

## Guardrails

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No portfolio position mutation.
- No benchmark composition mutation.
