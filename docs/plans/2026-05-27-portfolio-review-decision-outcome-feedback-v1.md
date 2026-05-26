# portfolio-review-decision-outcome-feedback-v1 Plan

## Summary

Persisted portfolio review decisions are useful only if the system can later check whether the review was directionally right. The next task adds an audit-only feedback layer that compares saved review decisions with later paper validation, recommendation outcome, thesis, and price evidence.

## Implementation Order

1. Inspect existing recommendation outcome, paper validation, thesis, and price evidence boundaries.
2. Add a backend CLI runner that reads `portfolio_review_decision_history` eval artifacts and classifies each decision as `too_early`, `validated`, `contradicted`, or `needs_more_data`.
3. Store the feedback report as `ai.eval_run` without changing recommendation weights, benchmark composition, portfolio positions, or orders.
4. Expose the latest feedback state on data-health and portfolio coverage.
5. Add tests, AWH verification, and EC2 smoke.

## Guardrails

- No recommendation weight changes.
- No automatic rebalance or broker submit.
- No benchmark definition changes.
- No portfolio position mutation.
