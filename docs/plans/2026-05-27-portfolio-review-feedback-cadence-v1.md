# portfolio-review-feedback-cadence-v1 Plan

## Summary

- Goal: keep portfolio review feedback and calibration current without mutating weights, positions, benchmark composition, or orders.
- Rationale: a single manual or ad-hoc run is not enough for a professional investment operating system. The system needs to know when outcome windows have matured and which audit runner should be executed next.

## Implementation Order

1. Read latest portfolio review decision history, outcome feedback, feedback calibration, recommendation outcome maturity, paper validation, and price evidence availability.
2. Classify cadence state as `wait_for_outcome_window`, `run_feedback_now`, `run_calibration_now`, `missing_evidence_review_required`, or `calibration_current`.
3. Store the cadence decision as read-only `ai.eval_run` evidence.
4. Expose latest cadence state on `/api/data-health` and `/api/portfolio/{portfolio}/coverage`.
5. Add user-facing Korean copy explaining what should run next and why no automatic weight/order action is allowed.
6. Add focused unit tests, frontend live adapter tests, Next typecheck, roadmap verify, AWH verify, and EC2 smoke.

## Guardrails

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No portfolio position mutation.
- No benchmark composition mutation.
