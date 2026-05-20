# Session Handoff

## Active Task

- 이름: local-ingest-worker-data-health-visibility
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract and implementation plan created.
  - `STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT` visibility loader added.
  - `/api/data-health` now includes additive `local_ingest_worker`.
  - Next `/data-health` renders a Korean “로컬 worker 실행 증거” section.
  - API contract example and Korean labels updated.
  - focused verification script added.
  - repo-outside `/private/tmp/stockanalysis-runtime/frontend-api.env` now points `STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT` at `/private/tmp/stockanalysis-runtime/local-ingest-worker.json`.
  - FastAPI restarted and is running on `http://127.0.0.1:8787`.
  - Next dev is running on `http://127.0.0.1:3001`.
  - Runtime API check returned `local_ingest_worker.status=completed`, `completed_cycle_count=1`, `failed_cycle_count=0`.
  - Runtime page check rendered `로컬 worker 최근 실행 성공`, `로컬 worker 실행 증거`, and `최근 수동 수집 smoke 성공`.
- 막힌 점:
  - `bash scripts/verify_frontend_api_contract.sh` still fails on the pre-existing unrelated `recommendation-detail` example assertion.

## Exact Next Step

- 다음 세션은 이것부터 시작: server-side scheduler packaging boundary를 정리해서 어떤 scheduler가 `stockanalysis-operations local-ingest-worker-run`을 호출할지 결정한다. 후보는 repo 안 product code가 아니라 배포 환경의 cron/systemd timer/Kubernetes CronJob/managed scheduler다.
- 금지: 명시 승인 전까지 `launchctl bootstrap/kickstart`, `~/Library/LaunchAgents` write/delete, external scheduler deployment는 하지 않는다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_local_ingest_worker tests.test_frontend_live_adapter`
- `bash scripts/verify_local_ingest_worker_data_health_visibility.sh`
- `cd apps/web && npm run typecheck`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-ingest-worker-data-health-visibility`
- `git diff --check`
- Runtime API check: authorized `GET http://127.0.0.1:8787/api/data-health` returned `local_ingest_worker.status=completed`, `execute=true`, `completed_cycle_count=1`, `failed_cycle_count=0`, `source=local_ingest_worker_report`.
- Runtime page check: `GET http://127.0.0.1:3001/data-health` rendered the Korean local worker evidence section.

## Risks

- This is visibility only. It does not activate a durable scheduler.
- The worker report path is repo-outside runtime state; if FastAPI env is restarted without `STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT`, the UI falls back to `not_configured`.
- Existing `verify_frontend_api_contract.sh` failure is unrelated to this task and remains to be fixed separately.
