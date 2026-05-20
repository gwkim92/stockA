# Session Handoff

## Active Task

- 이름: manual-local-ingest-data-health-visibility
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract and implementation plan created.
  - `manual-local-ingest-smoke --output` added for repo-outside summary files.
  - sanitized visibility loader added for `STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT`.
  - `/api/data-health` now includes additive `manual_local_ingest_smoke`.
  - Next `/data-health` renders a Korean “수동 단발 실행 증거” section.
  - API contract example and Korean labels updated.
  - focused verification script added.
  - repo-outside preview summary created at `/private/tmp/stockanalysis-runtime/manual-local-ingest-smoke.json`.
  - `/private/tmp/stockanalysis-runtime/frontend-api.env` now points `STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT` at that summary.
  - FastAPI is running on `http://127.0.0.1:8787`.
  - Next dev is running on `http://127.0.0.1:3001`.
  - Full `manual-local-ingest-smoke --execute` completed successfully after adding a repo-outside market watchlist and Twelve Data market env to `/private/tmp/stockanalysis-runtime/data-operations.env`.
  - Final summary status is `passed` with 3 succeeded artifact runs: `market-price-daily`, `news-rss-daily`, `event-intelligence-weekly`.
  - `/data-health` now shows Twelve Data budget `795/800`, latest market price observation `2026-05-19`, and manual smoke artifact count `3`.
- 막힌 점:
  - `bash scripts/verify_frontend_api_contract.sh` currently fails on an unrelated `recommendation-detail` example assertion, not on the new data-health field.

## Exact Next Step

- 다음 세션은 이것부터 시작: turn the now-proven manual smoke into a safe repeatable local operations runner decision, or improve `/data-health` wording for the remaining scheduler/manual approval gate.
- 금지: 명시 승인 전까지 `launchctl bootstrap/kickstart`, `~/Library/LaunchAgents` write/delete, external scheduler deployment는 하지 않는다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_manual_local_ingest_smoke tests.test_data_operations_cli tests.test_frontend_live_adapter`
- `bash scripts/verify_manual_local_ingest_data_health_visibility.sh`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task manual-local-ingest-data-health-visibility`
- `git diff --check`
- Runtime API check: authorized `GET http://127.0.0.1:8787/api/data-health` returned `manual_local_ingest_smoke.status=preview_not_executed`, `runtime_status=ready`, planned jobs `market-price-daily`, `news-rss-daily`, `event-intelligence-weekly`.
- Runtime page check: `GET http://127.0.0.1:3001/data-health` rendered `수동 단발 실행 증거`, `수동 수집 계획만 확인됨`, `미리보기만 생성됨`.
- Runtime execute check: full `manual-local-ingest-smoke --execute` returned `passed`, 3 artifact runs succeeded, and `/api/data-health` returned `manual_local_ingest_smoke.status=passed`, `execute=true`, `failed_job_count=0`, provider budget `used=5`, `remaining=795`.
- Runtime page after execute: `GET http://127.0.0.1:3001/data-health` rendered `최근 수동 수집 smoke 성공`, `통과`, `실제 실행`, `실행 artifact 3개`, and `Twelve Data 795/800`.

## Risks

- full `--execute` consumed 5 Twelve Data free-tier calls on 2026-05-20.
- 기존 FastAPI process는 env/code reload가 필요할 수 있다.
