# data-operations-artifact-runner-gate-evidence-v1 Handoff

## Status

- current status: completed.
- completed: API payload, frontend visibility, tests, local verification, GitHub push, EC2 deploy, service restart, API smoke, and route smoke are complete.

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

- exact next step: continue with the remaining operational gates: `production_api_server`, `auth_rbac`, and `alert_destination`. Keep `portfolio_review_feedback_calibration_attention` open until outcome feedback matures around `2026-06-24`.

## Local Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` (`77 tests`).
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- Passed: `cd apps/web && npm run build`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`.
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-operations-artifact-runner-gate-evidence-v1`.

## EC2 Evidence

- EC2 commit: `2bdb739`.
- EC2 services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- EC2 focused tests: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter` passed (`77 tests`).
- EC2 compile: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests` passed.
- EC2 frontend: `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build` passed.
- EC2 roadmap verify: `bash scripts/verify_project_execution_roadmap.sh` passed.
- `/api/data-health`: `data_operations_artifact_runner.status=operational_profile_scheduler_active`, `attention_required=false`, `job_count=33`, `artifact_policy_count=33`, `latest_run_count=33`, `profile_scheduler_installed=true`, `active_timer_count=7`, `timer_count=7`.
- `/api/data-health.open_gates`: `data_operations_artifact_runner` removed; remaining gates are `production_api_server`, `auth_rbac`, `alert_destination`, and `portfolio_review_feedback_calibration_attention`.
- `/data-health`: route returned `200` and rendered `운영 증거 확인됨`, `artifact 정책`, and `33/33개`.

## Guardrails

- Recommendation weights remain unchanged.
- Scheduler timers and commands remain unchanged.
- Broker submit and automatic orders remain blocked.
