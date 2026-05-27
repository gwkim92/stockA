# data-operations-artifact-runner-gate-evidence-v1 Handoff

## Status

- current status: local verification passed; EC2 deploy/smoke pending.
- in progress: API payload, frontend visibility, tests, and local verification are complete; EC2 smoke remains.

## Context

- EC2 `/api/data-health` still reports `data_operations_artifact_runner` as an open operational blocker.
- The codebase already has `stockanalysis.operations.artifact_runner`, artifact policies in the cadence registry, DB `ops.pipeline_run` evidence, and active profile scheduler timers.
- This task separates “artifact runner is operational” from “some individual job may be degraded.”

## Implemented Locally

- Added `data_operations_artifact_runner` payload to `/api/data-health`.
- Added evidence counts:
  - expected job count
  - artifact policy count
  - latest run count
  - failed/missing count
  - degraded count
  - profile scheduler timer count
  - artifact root fallback from manual smoke
- Added gate policy:
  - close when pipeline evidence and artifact policy evidence exist.
  - keep open when evidence is missing, partial, or failed/stale.
- Updated `/data-health` automation summary and scheduler detail to show artifact-runner evidence.

## Exact Next Step

- exact next step: run local verification, then deploy to EC2 and confirm `/api/data-health.open_gates` no longer includes `data_operations_artifact_runner` while the new payload reports operational evidence.

## Local Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` (`77 tests`).
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- Passed: `cd apps/web && npm run build`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`.
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-operations-artifact-runner-gate-evidence-v1`.

## Guardrails

- Recommendation weights remain unchanged.
- Scheduler timers and commands remain unchanged.
- Broker submit and automatic orders remain blocked.
