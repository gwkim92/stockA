# Review

## Review Notes

- `src/stockanalysis/frontend/runtime_policy.py`에 local/production runtime policy를 추가했다.
- fixture server는 기본 local fixture behavior를 유지하면서 non-loopback unauthenticated startup을 차단한다.
- `read-token` mode는 `/api/...`와 `/__endpoints`를 bearer token으로 보호하고, `/__health`와 `OPTIONS`는 public boundary로 유지한다.
- production profile은 fixture source, wildcard CORS, disabled auth, missing DB command를 거부한다.
- `stockanalysis-frontend-runtime-server` console alias를 추가했다.
- full auth/RBAC, connection pooling, write endpoint는 구현하지 않았다.

## Verification Evidence

- `python3 -m py_compile src/stockanalysis/frontend/runtime_policy.py src/stockanalysis/frontend/fixture_server.py tests/test_frontend_fixture_server.py`: 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_fixture_server -v`: 통과, 15 tests.
- `bash scripts/verify_frontend_api_runtime_boundary.sh`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 284 tests.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-runtime-boundary`: 통과.
- `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
