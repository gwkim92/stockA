# codex-oauth-admin-action-async-v1 Contract

## Task Request

- request: Codex OAuth 운영 콘솔의 긴 AI 확인 작업을 동기 HTTP 요청으로 기다리지 않게 하고, 전체 서비스 장애 지점과 원인을 파악해 해결한다.
- context: `뉴스 AI 확인`은 실제 Codex OAuth batch를 호출하므로 30초 이상 걸릴 수 있다. 이전 구현은 HTTP 요청 안에서 끝까지 기다려 브라우저와 FastAPI timeout에 취약했다.

## Goal

- goal: `/__admin/codex-oauth/smoke/news`가 즉시 background job을 시작하고 `news_smoke_running` 상태를 반환하며, 실제 완료/실패 결과는 기존 Codex OAuth status artifact에 기록된다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/codex_oauth_operator.py`
  - `src/stockanalysis/frontend/api_server.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/admin/ai-agents/CodexOauthOperatorPanel.tsx`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_codex_oauth_operator.py`
  - `tests/test_frontend_api_server.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/codex-oauth-admin-action-async-v1/*`

## Invariants

- Do not expose OpenAI API keys, Admin API keys, Codex OAuth token files, DB URLs, read tokens, or admin action tokens.
- Admin action endpoints still require read auth and `STOCKANALYSIS_FRONTEND_API_ADMIN_ACTION_TOKEN`.
- No broker submit, automatic order, recommendation weight change, or portfolio mutation.
- FastAPI request rendering must not call LLMs; AI calls remain explicit admin/batch actions only.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_codex_oauth_operator tests.test_frontend_api_server`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task codex-oauth-admin-action-async-v1`
- verification command: `EC2 POST /__admin/codex-oauth/smoke/news` returns immediately with `news_smoke_running`, then status becomes `healthy` after background completion.

## Done Criteria

- `뉴스 AI 확인` button no longer blocks until full Codex OAuth batch completes.
- UI shows `뉴스 AI 확인 중` and disables duplicate news smoke execution while the background job is active.
- EC2 service health and key pages remain healthy.
- Remaining open gates are classified as real issue, managed wait, or follow-up.
