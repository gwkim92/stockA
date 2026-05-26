# recommendation-outcome-due-action-router-v1 Contract

## Task Request

- request: Consume recommendation outcome maturity/sample state and route due windows to the existing calibration runner without relying on ad-hoc manual commands.
- context: `recommendation-outcome-maturity-monitor-v1` and `recommendation-outcome-due-cadence-automation-v1` expose when recommendation outcome windows are due, overdue, blocked by price gaps, or not yet due. The remaining gap is a backend action router that safely turns that state into an executable outcome calibration run only when appropriate.

## Goal

- goal: Add a `stockanalysis-operations recommendation-outcome-due-action-router-run` CLI/service that records an auditable router artifact, executes `recommendation-outcome-calibration-sample-expansion-run` only for due/ready windows, blocks price-gap states, and preserves all read-only recommendation/order guardrails.

## Invariants

- Recommendation score weights must not change.
- Broker submit and live order flow remain out of scope.
- Portfolio positions, benchmark definitions, and rebalance actions must not be mutated.
- Router writes are limited to `ops.pipeline_run` and `ai.eval_run`; the child calibration runner may write price-based outcome/eval artifacts through its existing boundary.
- The router must be deterministic and runnable by `stockanalysis-operations`.

## Files In Scope

- mutable surface:
  - `src/stockanalysis/operations/recommendation_outcome_due_action_router.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/recommendation-outcome-due-action-router-v1/*`

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: focused unit tests for the new router, CLI, cadence, orchestrator, and live adapter visibility
- verification command: `cd apps/web && npm run typecheck && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-outcome-due-action-router-v1`
