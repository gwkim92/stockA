# news-agents-runtime-migration-v1 Handoff

## Status

- completed: local runner migration seam, tests, compile, diff check, and AWH readiness passed.

## Current Status

- 완료:
  - Created task contract.
  - Added `src/stockanalysis/ai_agents/runtime_policy.py`.
  - Threaded `news_translator_agent` runtime policy through `run_news_rss_translation`.
  - Threaded `news_structuring_agent` runtime policy through `run_news_rss_ai_extract`.
  - Added agent runtime policy to runner reports and pipeline config JSON.
  - Added agent prompt version into news translation and news AI request hashes so prompt changes do not reuse stale cached artifacts.
  - Existing `fixture` and `codex_oauth` provider behavior remains unchanged.
- 유지한 경계:
  - No OpenAI API calls.
  - No Agents SDK production execution yet.
  - No recommendation weight changes.
  - No scheduler cadence changes.
  - No broker/order behavior changes.

## Next Step

- exact next step: implement `agents-sdk-openai-provider-v1` for a dry-run/smoke path using the agent registry, then add admin-only model/prompt status visibility before enabling production fallback.

## Verification

- passed: `PYTHONPATH=src python3 -m unittest tests.test_ai_agent_registry tests.test_news_rss_translation tests.test_news_rss_ai_extract`
- passed: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-agents-runtime-migration-v1`

## Risks

- This task is a metadata/runtime-boundary migration only. It does not fix the current EC2 Codex OAuth invalid refresh token.
- `agents_sdk_openai` is cataloged but not executable from the news runners yet; provider selection remains `fixture` or `codex_oauth`.
- Admin UI for per-agent model selection is not implemented yet.
