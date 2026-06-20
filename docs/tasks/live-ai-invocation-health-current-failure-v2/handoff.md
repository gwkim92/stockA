# live-ai-invocation-health-current-failure-v2 Handoff

## Status

- blocked on OpenAI API quota/credits, not blocked on Codex OAuth-only coupling.

## Current Status

- 상태: root cause identified; `agents_sdk_openai` support deployed to EC2 and selected by runtime env.
- 기준일: 2026-06-19
- 완료:
  - task contract created.
  - EC2 `/api/data-health` inspected.
  - latest `ai.model_invocation` rows inspected from EC2 Postgres.
  - confirmed OpenAI API key and Admin API key are configured in EC2 runtime env without printing secrets.
  - confirmed OpenAI Admin Costs API succeeds and reports zero recent cost; remaining balance is not exposed by official API.
  - implemented `agents_sdk_openai` provider support for `news-rss-translation-run` and `news-rss-ai-extract-run`.
  - updated CLI provider resolution so omitted `--provider` reads `STOCKANALYSIS_LLM_PROVIDER`.
  - updated `news-intraday` operating profile to pass configured LLM provider instead of hard-coded `codex_oauth`.
  - updated `/api/data-health` live AI health to count both `codex_oauth` and `agents_sdk_openai` invocations.
  - deployed commit `1ec213f6` to EC2 with `git pull --ff-only origin develop`.
  - set `/opt/stockanalysis/runtime/data-operations.env` `STOCKANALYSIS_LLM_PROVIDER="agents_sdk_openai"`.
  - restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
  - reopened local SSH tunnel `127.0.0.1:13000 -> EC2 127.0.0.1:3000`.
- 현재 증거:
  - EC2 Python imports `agents`, `openai`, and `fastapi`.
  - dry-run `news-rss-translation-run` resolves `provider=agents_sdk_openai`, `model_name=gpt-5.5`.
  - dry-run `news-rss-ai-extract-run` resolves `provider=agents_sdk_openai`, `model_name=gpt-5.5`.
  - execute `news-rss-translation-run --limit 1` created `run_id=6437`, status `completed_with_fallback`, error `OpenAI quota is exhausted. Falling back to the configured offline provider.`
  - execute `news-rss-ai-extract-run --limit 1` created `run_id=6438`, status `completed_with_fallback`, same quota error.
  - `/api/data-health` now reports latest error code `openai_insufficient_quota`, not `codex_oauth_auth_invalid`.
  - `/api/admin/ai-agents.runtime_policy.openai_provider_health.status=openai_insufficient_quota`.
  - EC2 internal routes `/`, `/data-health`, `/admin/ai-agents`, `/ai-evidence` return `200` on port `3000`.
  - local tunnel routes `/`, `/data-health`, `/admin/ai-agents` return `200` on `http://127.0.0.1:13000`.
  - EC2 `open_gates` still includes `live_ai_invocation_health_attention` because actual LLM invocations cannot succeed without usable OpenAI quota or fresh Codex OAuth.
  - `live_ai_invocation_health.status=critical_ai_failed`
  - 48h recent invocations: `754`, successes `0`, failures `754`.
  - latest failed task `news-rss-ai-extract`
  - latest error code after deployment is `openai_insufficient_quota`.
  - latest failed critical tasks are `news-rss-korean-translation` and `news-rss-ai-extract`.
  - previous failed rows contain `token_invalidated`, `refresh_token_invalidated`, and `401 Unauthorized`; new failed rows contain OpenAI quota exhaustion.
  - root cause was not missing OpenAI key. The root cause had two layers:
    - old layer: Codex OAuth token invalidation plus hard-coded OAuth-only news runners.
    - current layer: OpenAI API key is configured but has no usable quota/credits.
- 남은 점:
  - add usable OpenAI API credits/quota, or refresh EC2 Codex OAuth if API billing will remain unavailable.
  - rerun bounded news translation and news AI extraction smoke after quota/auth is usable.
  - then verify `/api/data-health.open_gates` no longer includes `live_ai_invocation_health_attention`.

## Next Step

- exact next step: add usable OpenAI API credits/quota, or refresh EC2 Codex OAuth if API billing will remain unavailable.
- exact follow-up after OpenAI quota/credits are available:
  - rerun:
    - `stockanalysis-operations news-rss-translation-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-20 --limit 1 --execute`
    - `stockanalysis-operations news-rss-ai-extract-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-20 --limit 1 --execute`
  - verify both latest critical task statuses are `succeeded`.
  - verify `/api/data-health.open_gates` no longer includes `live_ai_invocation_health_attention`.
  - if quota remains unavailable, keep gate open and show `openai_insufficient_quota`; do not hide the failure.
