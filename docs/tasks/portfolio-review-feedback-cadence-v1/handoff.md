# portfolio-review-feedback-cadence-v1 Handoff

## Status

- in progress: planned next task after `portfolio-review-feedback-calibration-v1`; implementation has not started.

## Context

- Portfolio review decision history, single-run outcome feedback, and accumulated calibration now exist as read-only audit artifacts.
- The system still needs a cadence policy that tells operators and scheduler profiles when feedback and calibration should be rerun.
- The cadence policy must not change recommendation weights, portfolio positions, benchmark composition, or orders.

## Exact Next Step

- exact next step: inspect latest review history, feedback, calibration, recommendation outcome maturity, paper validation, and price evidence states; design a read-only cadence decision report with statuses such as `wait_for_outcome_window`, `run_feedback_now`, `run_calibration_now`, and `missing_evidence_review_required`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat insufficient evidence as a blocker, not as readiness.
