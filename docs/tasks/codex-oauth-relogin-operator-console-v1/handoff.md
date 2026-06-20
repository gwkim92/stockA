# codex-oauth-relogin-operator-console-v1 Handoff

## Status

- status: implemented locally; EC2 deployment pending.

## Current Status

- 상태: local implementation and verification completed.
- 기준일: 2026-06-20.
- 완료:
  - Codex OAuth status artifact loader and smoke/relogin operator functions implemented.
  - FastAPI admin status/action routes implemented with read auth plus separate admin action token.
  - `/admin/ai-agents` Codex OAuth operator panel implemented.
  - `/data-health` live AI section links to the operator console.
  - Python tests, full unit test discovery, compileall, Next typecheck/build, and diff check passed locally.
  - Fixed Codex CLI device-auth output parsing so ANSI color codes and the phrase `command-line` do not corrupt `auth_url` or `user_code`.
- 미완료:
  - EC2 deployment and smoke are still pending.

## What Changed

- Added a repo-outside Codex OAuth operator status artifact boundary.
- Added FastAPI admin endpoints:
  - `GET /__admin/codex-oauth/status`
  - `POST /__admin/codex-oauth/relogin/start`
  - `POST /__admin/codex-oauth/smoke/direct`
  - `POST /__admin/codex-oauth/smoke/news`
- Admin POST actions require both read auth and `STOCKANALYSIS_FRONTEND_API_ADMIN_ACTION_TOKEN`.
- Added `/admin/ai-agents#codex-oauth-operator` UI with:
  - 상태: 정상/로그인 대기/코드 만료/재로그인 필요/미확인
  - 재로그인 시작 버튼
  - auth URL/user code/expires-at display
  - direct smoke button
  - news translation/extract smoke button
- Linked `/data-health` live AI failure guidance to the AI operator console.
- Kept broker submit, automatic order, portfolio writes, and recommendation weight changes disabled.

## Runtime Env

- Recommended EC2 env:
  - `STOCKANALYSIS_FRONTEND_API_ADMIN_ACTION_TOKEN=<repo-outside secret>`
  - `STOCKANALYSIS_CODEX_OAUTH_STATUS_PATH=/opt/stockanalysis/artifacts/codex-oauth/status.json`
  - `STOCKANALYSIS_CODEX_OAUTH_SMOKE_ENV_FILE=/opt/stockanalysis/runtime/data-operations.env`

## Verification

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_codex_oauth_operator tests.test_frontend_api_server`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m compileall src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed after parser fix: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_codex_oauth_operator tests.test_frontend_api_server`
- passed after parser fix: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m py_compile src/stockanalysis/frontend/codex_oauth_operator.py tests/test_codex_oauth_operator.py`
- passed after parser fix: `git diff --check`

## Remaining Work

- Deploy to EC2 by merging/pushing to `develop`, pulling on EC2, setting repo-outside env, and restarting FastAPI/Next services.
- Run EC2 route smoke for `/data-health` and `/admin/ai-agents`.
- Do not trigger real Codex OAuth relogin unless the operator is ready to complete the device auth flow.

## Next Step

- exact next step: commit and push this task to `develop`, deploy it on EC2 with `git pull --ff-only origin develop`, set `STOCKANALYSIS_FRONTEND_API_ADMIN_ACTION_TOKEN`, `STOCKANALYSIS_CODEX_OAUTH_STATUS_PATH`, and `STOCKANALYSIS_CODEX_OAUTH_SMOKE_ENV_FILE` in repo-outside runtime env, then restart FastAPI/Next and smoke `/data-health` plus `/admin/ai-agents`.
