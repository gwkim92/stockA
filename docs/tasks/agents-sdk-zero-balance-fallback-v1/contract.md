# agents-sdk-zero-balance-fallback-v1 Contract

## Task Request

- request: 사용자가 OpenAI API key를 로컬 `.env`에 저장했지만 잔액이 없으므로, Agents SDK OpenAI provider가 잔액/쿼터 실패를 서비스 장애로 만들지 않고 fallback 가능한 상태로 분류하게 한다.
- context: `agents_sdk_openai`는 1차 provider로 등록됐지만 실제 운영에서는 결제/잔액/쿼터 부족이 자주 발생할 수 있다. AI 실패는 뉴스/리서치 배치를 멈추면 안 되고 `codex_oauth` 또는 `local_rules`로 내려가야 한다.

## Goal

- goal: OpenAI API key가 있어도 billing/insufficient quota/disabled 상태면 OpenAI 호출을 안전하게 차단하거나 `openai_insufficient_quota`로 분류하고, caller가 `codex_oauth` 또는 `local_rules` fallback을 선택할 수 있는 구조를 제공한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ai_agents/agents_sdk_provider.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/admin/ai-agents/page.tsx`
  - `tests/test_agents_sdk_provider.py`
  - `docs/tasks/agents-sdk-zero-balance-fallback-v1/*`

## Invariants

- Do not print or persist the API key.
- Do not make a live OpenAI request in tests.
- Do not enable broker submit, automatic orders, or recommendation weight changes.
- Do not call OpenAI from FastAPI/Next request rendering.
- Keep `codex_oauth` and `local_rules` as fallback paths.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_agents_sdk_provider tests.test_frontend_live_adapter tests.test_ai_agent_registry`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task agents-sdk-zero-balance-fallback-v1`
