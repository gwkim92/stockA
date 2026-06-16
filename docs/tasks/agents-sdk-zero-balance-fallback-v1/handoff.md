# agents-sdk-zero-balance-fallback-v1 Handoff

## Status

- status: implemented_local_verified
current status: provider failure classification, zero-balance runtime guard, and AI 운영 visibility are implemented and locally verified.
- completed: code changes, tests, build, compileall, and AWH verify.

## Current Decision

- A known zero-balance OpenAI key must not be treated as a fatal service condition.
- The provider must classify insufficient quota/billing failures as fallbackable.
- The UI should show that a key is configured but billing may be unavailable without exposing the key.

## Next Step

- exact next step: wire `agents_sdk_openai` into the concrete news/research batch runners with `codex_oauth` and `local_rules` fallback. Keep `STOCKANALYSIS_DISABLE_OPENAI_API=1` until the OpenAI account has balance.

## Boundaries

- No live broker/order flow.
- No recommendation scoring weight mutation.
- No live OpenAI call during tests or frontend request rendering.

## Implemented

- `AgentsSdkProviderError` now carries `error_code`, `fallback_provider`, `local_fallback_provider`, and `retryable`.
- OpenAI quota/billing/auth/rate-limit/timeout/provider errors are classified into stable codes.
- `STOCKANALYSIS_OPENAI_BILLING_STATUS=known_zero_balance` blocks direct OpenAI calls with `openai_billing_unavailable`.
- `STOCKANALYSIS_DISABLE_OPENAI_API=1` blocks direct OpenAI calls with `openai_provider_disabled`.
- `/api/admin/ai-agents` and `/admin/ai-agents` expose sanitized primary provider status and fallback reason without leaking keys.
- Local `.env` has `STOCKANALYSIS_OPENAI_BILLING_STATUS="known_zero_balance"` and `STOCKANALYSIS_DISABLE_OPENAI_API="1"` because the user reported the key has no balance.

## Verification

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_agents_sdk_provider tests.test_frontend_live_adapter tests.test_ai_agent_registry`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- passed: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task agents-sdk-zero-balance-fallback-v1`

## Re-enable OpenAI Later

- When the OpenAI account has usable balance, change local/runtime env to:
  - `STOCKANALYSIS_OPENAI_BILLING_STATUS="available"`
  - `STOCKANALYSIS_DISABLE_OPENAI_API="0"`
- Keep fallback providers configured even after balance is restored.
