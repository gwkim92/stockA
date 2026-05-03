# Session Handoff

## Active Task

- 이름: frontend-api-server-framework-decision
- 담당: Codex
- 날짜: 2026-05-03

## Current Status

- 진행 중:
  - task contract와 plan을 만들었다.
  - runtime config와 runtime policy에 `STOCKANALYSIS_DATABASE_URL`을 추가했다.
  - `PsycopgPoolExecutor`와 FastAPI app factory를 추가했다.
  - Next server-side fetch adapter가 `STOCKANALYSIS_FRONTEND_API_READ_TOKEN`을 bearer token으로 전달하도록 했다.
  - FastAPI/db pool unit tests와 Docker Postgres + Uvicorn + Next smoke script를 추가했다.
  - API server 문서, roadmap, verification plan을 갱신했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-05-03-frontend-api-server-framework-decision.md`
  - `docs/tasks/frontend-api-server-framework-decision/contract.md`
  - `docs/tasks/frontend-api-server-framework-decision/plan.md`
  - `docs/tasks/frontend-api-server-framework-decision/handoff.md`
  - `docs/tasks/frontend-api-server-framework-decision/review.md`
- 예정:
  - `src/stockanalysis/frontend/api_server.py`
  - `src/stockanalysis/frontend/db_pool.py`
  - `tests/test_frontend_api_server.py`
  - `tests/test_frontend_db_pool.py`
  - `scripts/verify_frontend_api_server.sh`
  - `docs/frontend-api-server.md`
- 수정:
  - `pyproject.toml`
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/frontend/runtime_policy.py`
  - `apps/web/src/lib/frontend-api.ts`
  - `AGENTS.md`
  - `README.md`
  - `docs/frontend-api-runtime-boundary.md`
  - `docs/frontend-architecture.md`
  - `docs/frontend-runtime-db-smoke.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `scripts/verify_project_execution_roadmap.sh`

## Decisions

- FastAPI를 production-candidate frontend API server framework로 채택한다.
- stdlib fixture server는 local fixture/smoke 용도로 보존한다.
- write endpoint, full auth/RBAC, broker/order flow, schema/scoring 변경은 제외한다.

## Verification Already Run

- `python3 -m pip install -e .`: 시스템 Python PEP 668로 실패. `/tmp/stockanalysis-fastapi-venv`를 생성해 설치로 대체.
- `/tmp/stockanalysis-fastapi-venv/bin/python -m py_compile src/stockanalysis/frontend/api_server.py src/stockanalysis/frontend/db_pool.py src/stockanalysis/frontend/runtime_policy.py src/stockanalysis/ingest/config.py`: 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest tests.test_frontend_api_server tests.test_frontend_db_pool -v`: 통과, 10 tests.
- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_server.sh`: 통과.
- `bash scripts/verify_frontend_api_runtime_boundary.sh`: 통과.
- `bash scripts/verify_frontend_runtime_db_smoke.sh`: 통과.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /tmp/stockanalysis-fastapi-venv/bin/python -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-framework-decision`: 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`: 통과, 294 tests.
- `cd apps/web && npm run typecheck`: 통과.
- `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
- `git diff | rg -n "(BEGIN .*PRIVATE|PRIVATE KEY|AKIA|ghp_|github_pat_|sk-[A-Za-z0-9]|password\s*=|api[_-]?key\s*=|secret\s*=|token\s*=|DATABASE_URL=.*://)" -S`: 실제 secret 없음. `read_token`, API key env field names만 false positive로 확인.

## Exact Next Step

- exact next step: 변경분을 stage/commit/push하고 PR을 생성/머지한다.

## Risks

- 외부 Python dependency가 새로 필요하다.
- Docker smoke는 local Docker runtime에 의존한다.
- full auth/RBAC, request id, structured logs, readiness probes, deployment manifests는 후속 작업이다.
