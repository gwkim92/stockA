# Task Contract

## Task

- 이름: frontend-api-server-observability-hardening
- 요청: FastAPI read-only frontend API server를 운영에 더 가까운 경계로 강화한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: read-only FastAPI server가 request id, timeout, structured log, liveness/readiness probe를 제공하고 기존 DTO contract와 read-only/auth 경계를 유지한다.

## Why

- FastAPI server와 psycopg pool은 도입됐지만 운영 중 장애를 판별할 request id, readiness, timeout, structured access log가 아직 없다.
- write API나 UI 확장보다 먼저 API runtime failure boundary를 고정해야 이후 배포와 운영이 안전하다.

## Scope

- 포함:
  - request id 생성/전파
  - `X-Request-ID` response header
  - structured JSON access log
  - configurable request timeout
  - stable timeout error envelope
  - `/__live`, `/__ready` probe route
  - unit/ASGI/Docker smoke verification
  - docs/task handoff 갱신
- 제외:
  - write endpoint
  - full auth/RBAC/session/actor identity
  - audit write model
  - deployment manifests
  - external observability stack
  - DB schema/scoring/benchmark/evaluation split 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/api_server.py`
  - `tests/test_frontend_api_server.py`
  - `scripts/verify_frontend_api_server.sh`
  - `docs/frontend-api-server.md`
  - `docs/frontend-api-runtime-boundary.md`
  - `docs/frontend-architecture.md`
  - `docs/frontend-runtime-db-smoke.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-server-observability-hardening.md`
  - `docs/tasks/frontend-api-server-observability-hardening/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `python3 -m py_compile src/stockanalysis/frontend/api_server.py`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_server -v`
  - `bash scripts/verify_frontend_api_server.sh`
  - `bash scripts/verify_frontend_api_runtime_boundary.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-observability-hardening`
  - `git diff --check`

## Deliverables

- Request id and structured access log middleware
- Configurable API request timeout
- Liveness and readiness probes
- Extended FastAPI server smoke
- Updated docs/task handoff/review

## Completion Criteria

- [x] Responses include stable `X-Request-ID`.
- [x] Inbound `X-Request-ID` is propagated when safe.
- [x] Request timeout returns stable `{ "error": ... }` payload.
- [x] `/__live` and `/__ready` are public and do not leak secrets.
- [x] Structured access logs include request id, method, path, status, duration, profile, source mode.
- [x] Existing DTO/auth/write boundaries remain unchanged.
- [x] Verification commands pass and evidence is recorded.

## Risks

- Timeout cancellation cannot guarantee cancellation of already-running blocking DB driver work inside a thread.
- Logs are stdout JSON only; no external log sink, metrics backend, or alerting stack is added in this slice.
