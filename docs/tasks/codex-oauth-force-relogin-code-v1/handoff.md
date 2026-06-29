# codex-oauth-force-relogin-code-v1 Handoff

## Current Status

- status: implementation verified locally; commit/deploy/browser confirmation pending.
- completed: browser reproduction showed `새 로그인 코드 받기` calls the action but backend returns existing `healthy` status without a code.
- completed: added regression coverage for explicit relogin from healthy Codex OAuth state.
- completed: fixed backend relogin behavior so explicit relogin starts a fresh device-auth flow instead of returning existing healthy state.
- completed: fixed public status precedence so a latest device-auth pending event is not hidden by an older successful smoke event.
- local verification:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_codex_oauth_operator -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_server.FrontendApiServerTests.test_codex_oauth_admin_action_allows_explicit_operator_token -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task codex-oauth-force-relogin-code-v1`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `bash scripts/verify_frontend_api_contract.sh`

## Exact Next Step

- exact next step: commit, push `develop`, deploy to EC2, and confirm `/admin/ai-agents` displays a fresh code after clicking `새 로그인 코드 받기`.
