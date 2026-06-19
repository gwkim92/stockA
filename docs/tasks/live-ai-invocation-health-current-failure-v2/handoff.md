# live-ai-invocation-health-current-failure-v2 Handoff

## Status

- in progress: OAuth-only coupling remediation implemented locally; EC2 smoke pending.

## Current Status

- 상태: root cause identified; local code now supports `agents_sdk_openai` for critical news translation/extraction runners.
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
- 현재 증거:
  - EC2 `open_gates` includes `live_ai_invocation_health_attention`.
  - `live_ai_invocation_health.status=critical_ai_failed`
  - 48h recent invocations: `754`, successes `0`, failures `754`.
  - latest failed task `news-rss-ai-extract`
  - latest error code `codex_oauth_auth_invalid`
  - latest failed critical tasks are `news-rss-korean-translation` and `news-rss-ai-extract`.
  - latest failed rows contain `token_invalidated`, `refresh_token_invalidated`, and `401 Unauthorized`.
  - root cause is not missing OpenAI key; root cause is Codex OAuth token invalidation plus hard-coded OAuth-only news runners.
- 남은 점:
  - deploy to EC2.
  - set EC2 `STOCKANALYSIS_LLM_PROVIDER=agents_sdk_openai` in repo-outside runtime env.
  - run bounded news translation and news AI extraction smoke.
  - verify whether OpenAI API key has usable billing/quota. If it fails, the failure should be recorded as `openai_auth_invalid`, `openai_billing_unavailable`, or `openai_insufficient_quota` instead of OAuth token failure.

## Next Step

- exact next step:
  - run local unit/integration verification.
  - commit and push to `develop`.
  - EC2 `git pull --ff-only origin develop`.
  - set `STOCKANALYSIS_LLM_PROVIDER=agents_sdk_openai` in `/opt/stockanalysis/runtime/data-operations.env`.
  - run bounded `news-rss-korean-translation` and `news-rss-ai-extract` executions or `news-intraday` profile if candidates must be created first.
  - verify `/api/data-health.open_gates` no longer includes `live_ai_invocation_health_attention`.
  - run `git diff --check` and AWH verify for this task.
