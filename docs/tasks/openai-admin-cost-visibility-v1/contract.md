# openai-admin-cost-visibility-v1 Contract

## Task Request

- request: 사용자가 넣은 `OPENAI_ADMIN_API_KEY`로 OpenAI 비용 상태를 화면에서 볼 수 있게 한다.
- context: 일반 `OPENAI_API_KEY`는 모델 호출용이고, OpenAI Admin Costs API는 Admin API key가 필요하다. 공식 Costs API는 사용 비용을 반환하지만 남은 prepaid balance를 직접 반환하지 않는다.

## Goal

- goal: `stockanalysis-operations openai-admin-cost-refresh-run --execute`가 Admin Costs API를 호출해 repo 밖 status artifact를 만들고, `/data-health`와 `/admin/ai-agents`가 최근 비용, 조회 시각, 오류 상태, fallback 경계를 한국어로 보여준다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ai_agents/openai_costs.py`
  - `src/stockanalysis/ai_agents/provider_health.py`
  - `src/stockanalysis/operations/openai_provider_health.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/admin/ai-agents/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_data_operations_cli.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/openai-admin-cost-visibility-v1/*`

## Invariants

- Do not expose `OPENAI_API_KEY` or `OPENAI_ADMIN_API_KEY` in stdout, frontend JSON, logs, git, or task docs.
- Do not call OpenAI from FastAPI/Next.js request rendering.
- Do not use undocumented dashboard/session billing endpoints.
- Do not claim official remaining balance unless an official endpoint returns it.
- Do not change recommendation weights, broker submit, orders, or portfolio positions.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_cli tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task openai-admin-cost-visibility-v1`
