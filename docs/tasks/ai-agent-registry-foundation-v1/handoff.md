# ai-agent-registry-foundation-v1 Handoff

## Status

- completed: local catalog, schema, seed, CLI report, focused tests, compile, diff check, and AWH readiness passed.

## Current Status

- 기준일: 2026-06-16
- 완료:
  - task contract created.
  - OpenAI Agents SDK and prompt guidance checked.
  - Added `db/migrations/0032_ai_agent_registry.sql`.
  - Added `db/seeds/0007_ai_agent_registry_seed.sql`.
  - Added `src/stockanalysis/ai_agents/registry.py` and package exports.
  - Added `src/stockanalysis/operations/ai_agent_registry.py`.
  - Added `stockanalysis-operations ai-agent-registry-report`.
  - Added optional `agents` dependency extra with `openai-agents>=0.17.5,<0.18`.
  - Added `tests/test_ai_agent_registry.py`.
- 현재 판단:
  - Agents SDK 도입 방향은 맞다.
  - prompt는 OpenAI managed prompt object가 아니라 repo-managed/versioned prompt catalog로 관리한다.
  - AI agent가 분석을 주도하되 canonical write, recommendation weight, broker/order boundary는 deterministic guardrail이 강제한다.
  - 첫 agent team은 13개다: supervisor, news translation, news structuring, ontology mapping, macro regime, cycle analysis, equity research, valuation, recommendation review, portfolio risk, paper trading, data quality, ops alert.
  - 모든 agent는 `can_trigger_order=false`, `can_write_canonical=false`, `read_only_no_order` 경계를 기본으로 갖는다.
  - 모델 정책 기본 primary provider는 `agents_sdk_openai`, fallback은 `codex_oauth`, local fallback은 `local_rules`다.

## Next Step

- exact next step: migrate the existing news translation and news structuring runners behind the new agent registry/runtime boundary without changing recommendation weights, scheduler cadence, or broker/order behavior.

## Verification

- passed: `PYTHONPATH=src python3 -m unittest tests.test_ai_agent_registry`
- passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli ai-agent-registry-report`
- passed: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-agent-registry-foundation-v1`

## Risks

- This task does not execute Agents SDK yet. It creates the registry/model/prompt foundation only.
- Existing news/cycle/equity runners still use their current provider paths until the next migration task.
- API key, Codex OAuth reauth, backlog replay, and admin UI are still separate follow-up tasks.
