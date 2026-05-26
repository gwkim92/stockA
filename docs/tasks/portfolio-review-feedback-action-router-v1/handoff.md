# portfolio-review-feedback-action-router-v1 Handoff

## Status

- in progress: planned next task after `portfolio-review-feedback-cadence-v1`; implementation has not started.

## Context

- The cadence task creates a persisted read-only `ai.eval_run` artifact with statuses:
  - `wait_for_outcome_window`
  - `run_feedback_now`
  - `run_calibration_now`
  - `missing_evidence_review_required`
  - `calibration_current`
- Current scheduler profiles can compute the cadence state, but they do not yet consume the status to run the appropriate safe follow-up runner.

## Exact Next Step

- exact next step: build a read-only backend action-router runner that consumes the latest cadence artifact and executes only the safe feedback/calibration runner indicated by that artifact.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat missing evidence and immature windows as no-op states.
