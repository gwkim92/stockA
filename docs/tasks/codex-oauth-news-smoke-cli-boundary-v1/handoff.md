# codex-oauth-news-smoke-cli-boundary-v1 handoff

## Status

- status: completed

## Current Status

- 상태: implemented, pushed to `develop`, deployed to EC2, and verified.
- 기준일: 2026-06-20.
- 완료:
  - 뉴스 smoke command boundary를 `sys.executable -m stockanalysis.operations.cli` 기본값으로 변경했다.
  - `STOCKANALYSIS_OPERATIONS_COMMAND` override를 추가했다.
  - 관련 unit test를 추가했다.
  - EC2 `/opt/stockanalysis/runtime/data-operations.env`의 `STOCKANALYSIS_PSQL_COMMAND`에서 `sudo`를 제거했다. FastAPI service는 `NoNewPrivileges=true`라 `sudo docker exec`가 막히지만, `ec2-user`는 docker group에 있어 `docker exec`는 가능하다.
  - EC2 `/opt/stockanalysis/runtime/frontend-api.env`의 `STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS`를 `300`으로 올렸다. 뉴스 AI smoke가 30초를 넘으면 HTTP 504가 발생했기 때문이다.
- 미완료:
  - Long-running admin actions should eventually become async jobs instead of synchronous HTTP requests.

## Findings

- Codex OAuth direct smoke succeeded and status became `healthy`.
- News smoke failed because FastAPI could not resolve `stockanalysis-operations` from the service PATH.
- EC2 service uses `/opt/stockanalysis/venv/bin/python`; the reliable boundary is module invocation through the active interpreter.

## Changes

- `run_codex_oauth_news_smoke` now builds operations commands from `sys.executable -m stockanalysis.operations.cli` by default.
- Added `STOCKANALYSIS_OPERATIONS_COMMAND` override for deployments that need an explicit command.
- Added regression coverage for the default Python module command.

## Verification

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_codex_oauth_operator tests.test_frontend_api_server`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task codex-oauth-news-smoke-cli-boundary-v1`
- passed: EC2 `git pull --ff-only origin develop`, `sudo systemctl restart stockanalysis-frontend-api.service`, service `active`, commit `6c4acb1e`.
- passed: EC2 `POST /__admin/codex-oauth/smoke/news` returned `status=healthy`, `last_smoke_status=succeeded`, `last_error_code=''`, `next_action='성공한 smoke를 확인했다.'`.
- passed: EC2 pipeline rows show `news_rss_korean_translation|succeeded` and `event_intelligence_llm_extract|succeeded` for 2026-06-20 06:37 UTC.

## Exact Next Step

- next: Run local tests, commit/push to `develop`, deploy on EC2, restart FastAPI, and rerun `/__admin/codex-oauth/smoke/news`.

## Next Step

- exact next step: improve `/admin/ai-agents` admin action UX so long-running smoke actions are shown as queued/running/completed rather than blocking the page on a synchronous HTTP request.
