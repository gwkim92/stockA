# Task Contract

## Task

- 이름: local-ingest-worker-data-health-visibility
- 요청: local ingest worker 실행 상태를 `/api/data-health`와 `/data-health`에서 별도 카드로 확인할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: repo-outside worker report가 설정되면 data-health DTO와 화면이 worker 상태, 실행 여부, cycle 수, 실패 cycle 수, 최신 smoke summary 경로를 secret 없이 보여준다.

## Why

- `local-ingest-worker-run`은 생겼지만 현재 화면은 worker 자체가 아니라 worker가 갱신한 manual smoke summary만 보여준다.
- 운영자는 “반복 worker가 실행됐는지”와 “그 worker 안의 smoke cycle이 성공했는지”를 분리해서 봐야 한다.
- scheduler activation 전 단계에서는 이 로컬 worker 상태가 실제 반복 실행 가능성의 가장 가까운 증거다.

## Scope

- 포함:
  - repo-outside local worker report visibility loader
  - `/api/data-health` additive DTO field
  - Next.js `/data-health` Korean worker status card
  - tests, verify script, task handoff/review
- 제외:
  - Mac LaunchAgents/`launchctl` actual mutation
  - external server scheduler deployment
  - DB schema 변경
  - recommendation scoring/evaluation 변경
  - paid LLM/OpenAI call 도입
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/local_ingest_worker.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/api/frontend/examples/data-health.json`
  - `docs/frontend-api-contract.md`
  - `tests/test_local_ingest_worker.py`
  - `tests/test_frontend_live_adapter.py`
  - task docs and verify script
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring
  - benchmark/evaluation split
  - host scheduler install files

## Boundaries

- API/화면에는 DB URL, API key, bearer token, raw env values를 노출하지 않는다.
- worker report 경로는 repo 밖 파일만 허용한다.
- DTO 변경은 additive로 제한한다.
- 실제 `launchctl`이나 LaunchAgents write/delete는 하지 않는다.

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_local_ingest_worker tests.test_frontend_live_adapter`
  - `bash scripts/verify_local_ingest_worker_data_health_visibility.sh`
  - `cd apps/web && npm run typecheck`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-ingest-worker-data-health-visibility`
  - `git diff --check`

## Done Criteria

- [x] Missing/invalid worker report paths degrade safely in data-health.
- [x] `/api/data-health` includes sanitized `local_ingest_worker`.
- [x] `/data-health` renders latest local worker evidence in Korean.
- [x] Verification evidence is recorded in handoff/review.
