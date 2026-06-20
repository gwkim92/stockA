# codex-oauth-relogin-operator-console-v1 Contract

## Task Request

- request: Codex OAuth 상태를 정상/만료/미확인/재로그인 필요로 표시하고, 사이트에서 재로그인 시작, device code/auth URL 확인, 재로그인 후 smoke 재실행까지 이어지게 한다.
- context: OpenAI API quota가 없을 수 있으므로 `codex_oauth` fallback은 운영상 필요하다. 지금은 상태와 재로그인 동선이 `/data-health`와 `/admin/ai-agents`에서 연결되지 않아 사용자가 무엇을 해야 하는지 알 수 없다.

## Goal

- goal: `/admin/ai-agents`에서 Codex OAuth 운영 상태, device auth 정보, 직접 smoke, 뉴스 번역/구조화 smoke를 실행할 수 있고, `/data-health`에서 해당 운영 콘솔로 이동할 수 있다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/codex_oauth_operator.py`
  - `src/stockanalysis/frontend/api_server.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/app/admin/ai-agents/page.tsx`
  - `apps/web/src/app/admin/ai-agents/actions.ts`
  - `apps/web/src/app/admin/ai-agents/CodexOauthOperatorPanel.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_codex_oauth_operator.py`
  - `tests/test_frontend_api_server.py`
  - `docs/tasks/codex-oauth-relogin-operator-console-v1/*`

## Invariants

- Do not expose OpenAI API keys, Admin API keys, DB URLs, read tokens, or admin action tokens.
- Do not read or copy Codex OAuth token files.
- Do not run LLM calls during normal FastAPI/Next page rendering.
- Admin action endpoints require read auth and a separate server-side admin action token.
- This task must not enable broker submit, automatic orders, recommendation weight changes, or portfolio writes.
- Device code/auth URL may be shown only in the admin operator console after an explicit admin action.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_codex_oauth_operator tests.test_frontend_api_server`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m compileall src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task codex-oauth-relogin-operator-console-v1`
