# portfolio-review-feedback-action-router-v1 Plan

## Summary

- Goal: remove ad-hoc manual follow-up after cadence calculation by routing safe feedback/calibration actions through a backend service boundary.
- Rationale: professional portfolio review cannot depend on a person remembering which command to run after outcome windows mature. The system should still remain read-only and audit-first.

## Implementation Order

1. Load the latest `portfolio_review_feedback_cadence` artifact for a portfolio.
2. Classify action as `execute_feedback`, `execute_calibration`, or `no_op`.
3. Invoke the existing feedback/calibration runners only for the two safe execute actions.
4. Persist an action-router audit artifact showing what ran or why it did not run.
5. Add focused unit and CLI tests.
6. Keep frontend changes out of the first slice unless the API needs to expose the router artifact.

## Guardrails

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No portfolio position mutation.
- No benchmark composition mutation.
