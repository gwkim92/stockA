# agents-sdk-openai-provider-v1 Contract

## Task Request

- request: Agents SDK 기반 OpenAI provider를 추가하되, 기본 테스트/서버가 SDK 미설치나 API key 부재로 깨지지 않게 만든다.
- context: `ai-agent-registry-foundation-v1`과 `news-agents-runtime-migration-v1`으로 agent catalog와 news runner metadata seam이 생겼다. 다음 단계는 실제 Agents SDK 호출을 감쌀 provider boundary다.

## Goal

- goal: `openai-agents` optional dependency를 사용하는 import-safe provider wrapper를 만든다.
- goal: 테스트는 fake runner로 수행하고 실제 OpenAI/Codex 호출은 하지 않는다.
- goal: provider wrapper는 agent instructions, model policy, output schema, input payload를 받아 structured JSON candidate를 반환한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/agents-sdk-openai-provider-v1/*`
  - `src/stockanalysis/ai_agents/*`
  - `tests/test_agents_sdk_provider.py`

## Non-Goals

- Do not execute real OpenAI API calls.
- Do not set or require `OPENAI_API_KEY`.
- Do not switch production scheduler provider to Agents SDK yet.
- Do not change recommendation scoring weights, portfolio positions, scheduler cadence, or broker/order flow.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_ai_agent_registry tests.test_agents_sdk_provider tests.test_news_rss_translation tests.test_news_rss_ai_extract`
- verification command: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task agents-sdk-openai-provider-v1`
