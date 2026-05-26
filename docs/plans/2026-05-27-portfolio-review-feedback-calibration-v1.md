# portfolio-review-feedback-calibration-v1 Plan

## Summary

Portfolio review decision feedback is useful only after enough histories accumulate. This task aggregates saved feedback artifacts and reports whether review decisions are still too early, contradictory, or mature enough for manual review readiness. It remains audit-only and does not change recommendation weights.

## Implementation Order

1. Read latest `portfolio_review_decision_outcome_feedback` eval artifacts over a bounded lookback.
2. Aggregate feedback counts by decision family, decision type, and symbol.
3. Classify calibration as `insufficient_history`, `collect_more_feedback`, `contradiction_review_required`, or `manual_review_ready`.
4. Store the calibration as `ai.eval_run`.
5. Expose the latest calibration on data-health and portfolio coverage.
6. Add tests, AWH verification, and EC2 smoke.

## Guardrails

- No recommendation weight changes.
- No automatic rebalance or broker submit.
- No benchmark definition changes.
- No portfolio position mutation.
