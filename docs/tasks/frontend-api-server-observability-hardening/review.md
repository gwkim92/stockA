# Review

## Review Notes

- FastAPI read-only frontend API server에 request id propagation과 `X-Request-ID` response header를 추가했다.
- Safe inbound request id만 전파하고, 공백 등 unsafe 값은 generated UUID hex로 대체한다.
- 모든 request는 `stockanalysis.frontend.api_server` logger로 JSON access log를 남긴다.
- `STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS`와 `--request-timeout-seconds`를 추가했다.
- timeout은 `FrontendApiRequestTimeout` error envelope와 top-level `request_id`를 반환한다.
- public `/__live`와 `/__ready`를 추가했다.
- `/__ready`는 contract와 psycopg pool readiness만 확인하고 DB URL, token, exception detail을 노출하지 않는다.
- 기존 `/api/...` DTO shape, read-token auth, write 405 boundary, Next token forwarding, DB schema/scoring/benchmark는 변경하지 않았다.

## Verification Evidence

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
