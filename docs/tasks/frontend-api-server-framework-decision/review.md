# Review

## Review Notes

- FastAPI를 production-candidate frontend API server framework로 채택했다.
- `src/stockanalysis/frontend/api_server.py`는 `/__health`, `/__endpoints`, `/api/{path:path}` read route와 write method 405 guard를 제공한다.
- `src/stockanalysis/frontend/db_pool.py`는 기존 live adapter의 `execute_scalar(sql)` interface를 psycopg pool 위에서 구현한다.
- `STOCKANALYSIS_DATABASE_URL`을 추가했고 public runtime metadata에는 DB URL이나 read token을 노출하지 않는다.
- `apps/web` fetch adapter는 server-side `STOCKANALYSIS_FRONTEND_API_READ_TOKEN`이 있을 때만 Authorization header를 붙인다.
- schema, scoring, benchmark, write API, broker/order flow는 변경하지 않았다.

## Verification Evidence

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
