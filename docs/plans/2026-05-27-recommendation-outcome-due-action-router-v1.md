# Recommendation Outcome Due Action Router V1 Plan

## Summary

Create a backend action router for recommendation outcome maturity. It reads deterministic outcome sample status, executes outcome calibration only when due/ready, blocks price-gap cases, records an audit artifact, and exposes the result through operations and data-health without changing scoring weights or orders.

## Implementation

- Add `stockanalysis.operations.recommendation_outcome_due_action_router`.
- Add CLI command `recommendation-outcome-due-action-router-run`.
- Add daily cadence and decision/full-recovery orchestrator step after `recommendation-outcome-backfill` and before `recommendation-quality-eval`.
- Expose the latest router artifact on data-health API/UI.
- Add unit tests and harness documentation.

## Non-Goals

- No recommendation weight mutation.
- No live broker order submission.
- No automatic price repair in this router.
- No scoring formula changes.

