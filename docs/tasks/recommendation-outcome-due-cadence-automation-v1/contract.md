# recommendation-outcome-due-cadence-automation-v1 Contract

## Task Request

- request: Make outcome calibration cadence react to the maturity monitor so due or overdue recommendation outcomes are backfilled and calibrated without opening weight review early.
- context: `recommendation-outcome-maturity-monitor-v1` shows the next measurable recommendation outcome window and currently reports `next_due_date=2026-06-20`, `next_due_count=19`.

## Goal

- goal: When recommendation outcome windows become due or overdue, the data operations cadence should run or clearly request the correct outcome backfill/calibration job before any manual/pilot weight review can proceed.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/recommendation-outcome-due-cadence-automation-v1/*`
  - `docs/plans/2026-05-27-recommendation-outcome-due-cadence-automation-v1.md`

## Scope

- Decide whether this belongs in the existing profile scheduler, data-health cadence logic, or an operations runner.
- Use the maturity monitor output to classify due/overdue calibration work.
- Expose the next command/action in `/data-health`.
- Keep weight review gated by `recommendation-weight-review-horizon-gate-v1`.

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
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-outcome-due-cadence-automation-v1`

## Acceptance Criteria

- Due or overdue outcome windows produce a clear scheduler/cadence action.
- `not_due` windows produce a wait-until date rather than a false failure.
- Weight review remains blocked until outcome calibration later reports `ready_for_manual_weight_review`.
