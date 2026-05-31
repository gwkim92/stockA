# live-ai-invocation-health-gate-v1 Handoff

## Status

- completed: live AI invocation health gate is implemented, deployed to EC2, and API/UI smoke confirms the existing Codex OAuth failure is now visible.
- 기준일: 2026-06-01
- root cause:
  - EC2 최신 `news-intraday`는 systemd와 profile runner 관점에서는 성공했지만, 실제 Codex OAuth 호출은 `token_invalidated`/`refresh_token_reused`/`401 Unauthorized`로 실패했다.
  - 최근 48시간 `ai.model_invocation` 기준 Codex OAuth 호출은 성공 0건, 실패 다수였고, AI artifact는 local rule cluster만 생성됐다.
  - 기존 `news_ai_eval_quality`는 fixture/gold 회귀평가라 실제 운영 LLM 호출 실패를 대체하지 못한다.

## Implemented

- `/api/data-health` live SQL에 `live_ai_invocation_health`를 추가했다.
- 최근 48시간 `ai.model_invocation`에서 다음 Codex OAuth task를 집계한다.
  - `news-rss-korean-translation`
  - `news-rss-ai-extract`
  - `cycle-community-ai-summary-v2`
  - `ai-equity-research-reporting`
- 인증 오류를 `codex_oauth_auth_invalid` error code로 분리한다.
- 실제 AI 호출 상태가 `critical_ai_failed`, `degraded`, `missing_recent_invocations`이면 `open_gates`에 `live_ai_invocation_health_attention`을 추가한다.
- `/data-health`에 “실제 AI 호출 상태” 섹션을 추가해 fixture 회귀평가와 운영 LLM 호출 상태를 분리해서 보여준다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: local SQL rendered against EC2 DB returned `live_ai_invocation_health.status=critical_ai_failed`, `recent_failed_count=737`, `latest_failed_task_name=news-rss-ai-extract`, `latest_error_code=codex_oauth_auth_invalid`.
- PASS: AWH readiness passed for `live-ai-invocation-health-gate-v1`.
- PASS: EC2 deployed commit `e61c33d`, backend focused tests passed, Next typecheck/build passed, `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active.
- PASS: EC2 `/api/data-health` returns `open_gates=['data_operations_artifact_runner', 'live_ai_invocation_health_attention']`, `live_ai_invocation_health.status=critical_ai_failed`, `recent_success_count=0`, `recent_failed_count=737`, `latest_error_code=codex_oauth_auth_invalid`.
- PASS: EC2 `/data-health` renders `실제 AI 호출 상태`, `실제 AI 호출 확인 필요`, `실제 AI 실패 737건`, and `Codex OAuth 분석 실패`.
- FAIL-EXPECTED: limited `news-rss-translation-run --provider codex_oauth --limit 1 --execute` still returns `completed_with_fallback`; direct `codex exec` smoke exits 1 with `token_invalidated` and `refresh_token_reused`.

## Remaining

- Actual Codex OAuth authentication is still broken on EC2. `codex login status` reports ChatGPT login, but real `codex exec` returns 401. The stored refresh token must be replaced by a fresh login.
- After re-login, rerun limited translation and news AI extract smoke, then run `news-intraday` once.

## Exact Next Step

- exact next step: refresh EC2 Codex OAuth credentials with `codex logout` and `codex login --device-auth` or equivalent browser login, then run `news-rss-translation-run --provider codex_oauth --limit 1 --execute`.
