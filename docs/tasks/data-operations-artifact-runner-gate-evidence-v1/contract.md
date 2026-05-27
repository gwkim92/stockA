# data-operations-artifact-runner-gate-evidence-v1 Contract

## Task Request

- request: Replace the stale static `data_operations_artifact_runner` open gate with evidence-based readiness.
- context: EC2 already has artifact-runner-backed profile runs and active systemd timers, but `/api/data-health` still reports `data_operations_artifact_runner` as a generic unmet condition.

## Goal

- goal: Keep the artifact runner gate open only when runner evidence is missing or incomplete; close it when artifact policies, latest run evidence, and scheduler profile evidence prove it is operational.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/data-operations-artifact-runner-gate-evidence-v1/*`
  - `docs/plans/2026-05-27-data-operations-artifact-runner-gate-evidence-v1.md`

## Invariants

- Do not hide failed, stale, or degraded pipeline runs.
- Do not change scheduler timers or data operation commands.
- Do not mutate recommendation scores, benchmark composition, portfolio positions, outcomes, paper validation, or orders.
- Do not enable broker submit, automatic order, or automatic rebalancing.

## Scope

- Add `data_operations_artifact_runner` payload to data-health.
- Use pipeline run artifact policies, latest run ids, manual smoke artifact root, local worker status, and profile scheduler status as evidence.
- Remove `data_operations_artifact_runner` from open gates when the runner is operational.
- Keep it open when pipeline evidence or artifact policy evidence is missing.
- Show the runner evidence in `/data-health` scheduler/automation section.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-operations-artifact-runner-gate-evidence-v1`
