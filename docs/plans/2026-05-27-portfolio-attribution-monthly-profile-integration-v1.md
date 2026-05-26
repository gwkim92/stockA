# Portfolio Attribution Monthly Profile Integration V1 Plan

## Summary

The project already has deterministic portfolio attribution code and a data-health expected job, but the monthly performance profile does not execute it. This creates a false operational gap and weakens the `성과검증` leg of the professional investment system.

## Implementation

- Done: added a `stockanalysis-operations portfolio-attribution-run` command.
- Done: the runner resolves the latest eligible attribution window from portfolio snapshots and thesis outcomes.
- Done: the runner executes the existing deterministic attribution bootstrap when a candidate window exists.
- Done: the runner records a no-op `ops.pipeline_run` when no attribution window exists, so the scheduler state is explicit rather than missing.
- Done: `portfolio-attribution-monthly` runs after `performance-outcome-monthly` in the `performance-monthly` profile.

## Verification Evidence

- Local focused tests passed for portfolio attribution, cadence, orchestrator, CLI, and attribution bootstrap.
- Local full Python unittest discovery passed with `1103 tests`.
- Local Next.js `typecheck` and `build` passed.
- Local roadmap verify and AWH task verify passed.
- EC2 direct runner smoke selected snapshot `2026-05-22`, measurement end `2026-05-22`, covered `NVDA`, and wrote `run_id=1704`, `attribution_run_id=1`.
- EC2 `performance-monthly` profile smoke completed with `failed_step_count=0`.
- EC2 `/api/data-health` reports `portfolio-attribution-monthly` as `latest_status=succeeded`, `health_status=ok`, `latest_run_id=pipeline-run-1706`.

## Non-Goals

- No scoring weight changes.
- No broker/order integration.
- No schema changes.
- No attribution-based allocation decision automation.
