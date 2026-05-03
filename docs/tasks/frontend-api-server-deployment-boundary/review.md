# Review

## Review Notes

- FastAPI frontend API server의 deployment boundary를 repo 안에 안전하게 남겼다.
- Env template renderer는 repo 내부 output을 거부하고, repo 밖 shell env template을 mode `600`으로 생성한다.
- Runtime env checker는 repo 내부 env file을 거부하고 placeholder, production profile, read-token auth, explicit HTTPS origin, loopback host, DB URL shape, token length, port/pool/timeout 값을 검증한다.
- Run wrapper는 checker를 먼저 실행하고 `--preflight-only`를 지원한다.
- Preflight JSON은 DB URL과 read token을 출력하지 않는다.
- Deployment doc은 loopback FastAPI server 뒤에 TLS reverse proxy를 두는 topology와 forwarded header/cache assumptions를 명시한다.
- 실제 launchd/systemd/Docker/Kubernetes manifest, reverse proxy config, TLS material, production secret은 생성하지 않았다.

## Verification Evidence

- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_server_deployment_boundary.sh`: 통과.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `bash -n scripts/render_frontend_api_server_env_template.sh && bash -n scripts/check_frontend_api_server_runtime_env.sh && bash -n scripts/run_frontend_api_server.sh && bash -n scripts/verify_frontend_api_server_deployment_boundary.sh`: 통과.
- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_server.sh`: 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`: 통과, 299 tests.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /tmp/stockanalysis-fastapi-venv/bin/python -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-deployment-boundary`: 통과.
- `git diff --check`: 통과.
- `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`: 결과 없음.
- `rg -n "(BEGIN .*PRIVATE|PRIVATE KEY|AKIA|ghp_|github_pat_|sk-[A-Za-z0-9]|password\s*=|api[_-]?key\s*=|secret\s*=|token\s*=|DATABASE_URL=.*://|postgresql://|READ_TOKEN)" scripts/render_frontend_api_server_env_template.sh scripts/check_frontend_api_server_runtime_env.sh scripts/run_frontend_api_server.sh scripts/verify_frontend_api_server_deployment_boundary.sh docs/frontend-api-server-deployment-boundary.md docs/plans/2026-05-03-frontend-api-server-deployment-boundary.md docs/tasks/frontend-api-server-deployment-boundary README.md docs/frontend-api-server.md docs/frontend-api-runtime-boundary.md -S`: 실제 secret 없음. env var names, placeholder URL, `replace-me`, and verification-only dummy values만 false positive로 확인.
