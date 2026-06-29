# codex-oauth-force-relogin-code-v1 Handoff

## Current Status

- status: completed; deployed to EC2 and browser-confirmed.
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
- commit: `9b2e78a1 fix(frontend): force codex oauth relogin code issuance`
- EC2 deploy:
  - `git pull --ff-only origin develop` fast-forwarded to `9b2e78a1`.
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
  - `stockanalysis-frontend-api.service` active; `stockanalysis-web.service` active.
  - `http://127.0.0.1:8787/__health` returned `200`.
  - `http://127.0.0.1:3000/admin/ai-agents` returned `200`.
- browser QA:
  - route: `http://127.0.0.1:13000/admin/ai-agents`.
  - clicked `새 로그인 코드 받기`.
  - confirmed page shows `코드 입력 대기`, `브라우저에 입력할 코드`, and a fresh user code.
  - screenshot artifact: `/tmp/codex-oauth-relogin-after-fix.png` (not committed).

## Exact Next Step

- exact next step: user should open the auth page from `/admin/ai-agents`, enter the displayed code, then click `로그인 확인` and `AI 응답 확인`.
