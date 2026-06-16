# agents-sdk-openai-provider-v1 Handoff

## Status

- completed: import-safe provider wrapper, fake-runner tests, compile, diff check, and AWH readiness passed.

## Current Status

- 완료:
  - Created task contract.
  - Added `src/stockanalysis/ai_agents/agents_sdk_provider.py`.
  - Added `AgentsSdkStructuredRequest` and `AgentsSdkStructuredResponse`.
  - Added prompt builder that combines agent instructions, output schema, runtime policy, and input payload.
  - Added fake-runner execution path for tests.
  - Added optional real `openai-agents` import path with a clear `AgentsSdkProviderUnavailable` error when the extra is not installed.
  - Added `tests/test_agents_sdk_provider.py`.
- 유지한 경계:
  - No real OpenAI API calls were executed.
  - No API key is required.
  - No production scheduler provider was changed.
  - No recommendation weight, portfolio, scheduler cadence, or broker/order behavior changed.

## Next Step

- exact next step: add an admin-only agent model/status API and UI surface, then wire a dry-run `agents_sdk_openai` smoke command that requires explicit env/API key and budget caps.

## Verification

- passed: `PYTHONPATH=src python3 -m unittest tests.test_ai_agent_registry tests.test_agents_sdk_provider tests.test_news_rss_translation tests.test_news_rss_ai_extract`
- passed: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task agents-sdk-openai-provider-v1`

## Risks

- The wrapper does not yet run against real OpenAI in local or EC2 smoke.
- The current news runners still accept only `fixture` and `codex_oauth`; production provider selection remains unchanged.
- Admin UI for per-agent model selection is still pending.
