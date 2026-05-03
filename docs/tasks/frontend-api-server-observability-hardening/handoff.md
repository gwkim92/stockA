# Session Handoff

## Active Task

- 이름: frontend-api-server-observability-hardening
- 담당: Codex
- 날짜: 2026-05-03

## Current Status

- 완료:
  - task contract와 plan을 만들었다.
  - FastAPI middleware에 request id 생성/전파, `X-Request-ID`, structured JSON access log를 추가했다.
  - `STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS`와 `--request-timeout-seconds`로 configurable timeout을 추가했다.
  - timeout 시 `FrontendApiRequestTimeout` stable error envelope와 request id를 반환하도록 했다.
  - public `/__live`, `/__ready` probe를 추가했다.
  - `/__ready`는 contract load와 psycopg pool check를 확인하되 DB URL, token, exception detail은 노출하지 않는다.
  - Docker-backed FastAPI smoke가 probes와 request id propagation을 검증하도록 확장했다.
  - docs, roadmap, verification plan, AGENTS를 갱신했고 다음 고정 task를 `frontend-api-server-deployment-boundary`로 이동했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-05-03-frontend-api-server-observability-hardening.md`
  - `docs/tasks/frontend-api-server-observability-hardening/contract.md`
  - `docs/tasks/frontend-api-server-observability-hardening/plan.md`
  - `docs/tasks/frontend-api-server-observability-hardening/handoff.md`
  - `docs/tasks/frontend-api-server-observability-hardening/review.md`
- 수정:
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

## Decisions

- 이번 slice는 read-only API runtime 관측성과 readiness만 다룬다.
- write endpoint, full auth/RBAC, schema/scoring/benchmark 변경, deployment manifest는 제외한다.
- request id는 `^[A-Za-z0-9._:-]{1,128}$` 형식만 inbound propagation하고, 나머지는 server-generated UUID hex로 대체한다.
- access log는 query string을 제외한 path만 기록해 token/secret이 query에 들어오는 경우 로그 노출 위험을 낮춘다.
- timeout은 HTTP response boundary를 제한하지만 threadpool 내부 DB 작업의 즉시 중단까지 보장하지는 않는다.

## Verification Already Run

- `/tmp/stockanalysis-fastapi-venv/bin/python -m py_compile src/stockanalysis/frontend/api_server.py`: 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest tests.test_frontend_api_server tests.test_frontend_db_pool -v`: 통과, 15 tests.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_server.sh`: 통과.
- `bash scripts/verify_frontend_api_runtime_boundary.sh`: 통과.
- `bash scripts/verify_frontend_runtime_db_smoke.sh`: 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`: 통과, 299 tests.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /tmp/stockanalysis-fastapi-venv/bin/python -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-observability-hardening`: 통과.
- `git diff --check`: 통과.
- `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff | rg -n "(BEGIN .*PRIVATE|PRIVATE KEY|AKIA|ghp_|github_pat_|sk-[A-Za-z0-9]|password\s*=|api[_-]?key\s*=|secret\s*=|token\s*=|DATABASE_URL=.*://)" -S`: 실제 secret 없음. `read_token="secret"` test literal만 false positive로 확인.

## Exact Next Step

- exact next step: AWH verify, diff check, secret scan을 실행한 뒤 commit/push/PR을 만든다.

## Risks

- Timeout은 HTTP response boundary를 제한하지만 threadpool 내부 DB 호출의 즉시 중단을 보장하지 않는다.
- 외부 metrics/log backend는 아직 없다.
- deployment topology, reverse proxy/TLS assumptions, runtime env template은 다음 task로 남았다.
