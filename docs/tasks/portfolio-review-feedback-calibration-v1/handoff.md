# portfolio-review-feedback-calibration-v1 Handoff

## Status

- in progress: pending implementation; this is the next task after `portfolio-review-decision-outcome-feedback-v1`.

## Context

- Single-run feedback can say whether one saved review history is too early, validated, contradicted, or needs more data.
- The next step is not to change weights. It is to aggregate feedback over enough histories to decide whether a future manual pilot review is even eligible.

## Exact Next Step

- exact next step: inspect `portfolio_review_decision_outcome_feedback` eval artifacts and design a calibration summary that groups feedback by decision family and decision type without mutating recommendations, benchmark composition, portfolio positions, or orders.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat sparse histories as `insufficient_history`, not readiness.
