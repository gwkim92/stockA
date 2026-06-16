# openai-provider-health-visibility-v1 Contract

## Task Request

- request: 사용자가 직접 env를 수정하지 않아도 OpenAI 잔액/쿼터 문제를 자동으로 감지하고, 사이트에서 잔액·쿼터 상태와 fallback 상태를 볼 수 있게 한다.
- context: 일반 OpenAI API key는 모델 호출에는 사용할 수 있지만, 조직 비용/usage 관리 API는 Admin API key 권한이 필요하다. 따라서 남은 잔액을 항상 직접 확정 조회할 수 없고, provider failure cache와 optional Admin Costs API가 필요하다.

## Goal

- goal: `agents_sdk_openai` 호출 실패가 `openai_insufficient_quota` 또는 `openai_billing_unavailable`이면 repo 밖 provider health artifact에 기록하고, TTL 동안 자동으로 `codex_oauth`/`local_rules` fallback을 유도하며, `/admin/ai-agents`가 이 상태를 한국어로 보여준다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ai_agents/provider_health.py`
  - `src/stockanalysis/ai_agents/agents_sdk_provider.py`
  - `src/stockanalysis/operations/openai_provider_health.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/admin/ai-agents/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_agents_sdk_provider.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/openai-provider-health-visibility-v1/*`

## Invariants

- Do not expose API keys.
- Do not make live OpenAI calls from FastAPI/Next request rendering.
- Do not require manual billing env flags for normal fallback.
- Do not enable broker submit, automatic orders, or recommendation weight changes.
- Admin Costs API support is optional and requires separate `OPENAI_ADMIN_API_KEY`.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_agents_sdk_provider tests.test_frontend_live_adapter tests.test_ai_agent_registry`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_agents_sdk_provider tests.test_frontend_live_adapter tests.test_ai_agent_registry tests.test_data_operations_cli`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli openai-provider-health-report`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task openai-provider-health-visibility-v1`
