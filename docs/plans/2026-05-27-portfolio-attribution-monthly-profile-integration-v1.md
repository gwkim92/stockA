# Portfolio Attribution Monthly Profile Integration V1 Plan

## Summary

The project already has deterministic portfolio attribution code and a data-health expected job, but the monthly performance profile does not execute it. This creates a false operational gap and weakens the `성과검증` leg of the professional investment system.

## Implementation

- Add a `stockanalysis-operations portfolio-attribution-run` command.
- Resolve the latest eligible attribution window from portfolio snapshots and thesis outcomes.
- Execute existing deterministic attribution bootstrap when a candidate window exists.
- Record a no-op `ops.pipeline_run` when no attribution window exists, so the scheduler state is explicit rather than missing.
- Add `portfolio-attribution-monthly` after `performance-outcome-monthly` in the `performance-monthly` profile.

## Non-Goals

- No scoring weight changes.
- No broker/order integration.
- No schema changes.
- No attribution-based allocation decision automation.

