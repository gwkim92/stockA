# recommendation-outcome-maturity-monitor-v1 Contract

## Task Request

- request: Turn the current `no_due_outcome_window` state into an operational monitor so the system knows when recommendation outcomes become measurable and reruns calibration without opening weight review early.
- context: `recommendation-weight-review-horizon-gate-v1` correctly blocks manual weight review because 30/90/180/365-day recommendation horizons are not due yet.

## Goal

- goal: The system should expose the next due outcome windows, stale/missing outcome jobs, and the exact next calibration action before any manual/pilot recommendation weight review can be considered.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/recommendation-outcome-maturity-monitor-v1/*`
  - `docs/plans/2026-05-27-recommendation-outcome-maturity-monitor-v1.md`

## Scope

- Add a read-only outcome maturity monitor that reports next due horizon dates and overdue outcome windows.
- Keep using existing `performance.recommendation_outcome` and `recommendation_outcome_calibration_sample_expansion` outputs.
- Expose the monitor on `/data-health` next to outcome calibration and weight review readiness.
- Preserve the rule that recommendation weights stay unchanged until a later explicit pilot-weight task.

## Non-Goals

- No recommendation weight changes.
- No synthetic outcomes.
- No broker/order submit.
- No benchmark split changes.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-outcome-maturity-monitor-v1`

## Acceptance Criteria

- `/data-health` shows whether recommendation outcome windows are not due, due, overdue, or blocked by price gaps.
- The monitor identifies the next due horizon date and count of currently due candidates.
- Manual/pilot weight review remains blocked unless outcome calibration later reports `ready_for_manual_weight_review`.
