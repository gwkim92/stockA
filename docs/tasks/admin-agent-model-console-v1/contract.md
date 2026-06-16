# admin-agent-model-console-v1 Contract

## Task Request

- request: AI 에이전트 도입 후 운영자가 어떤 에이전트가 어떤 모델 정책으로 동작하는지 확인할 수 있는 읽기 전용 관리자 화면과 API를 만든다.
- context: Agents SDK, Codex OAuth fallback, local rules fallback 정책은 생겼지만 사용자가 사이트에서 에이전트별 모델, 프롬프트 버전, 안전 경계를 확인할 화면이 없다.

## Goal

- goal: `/api/admin/ai-agents`와 `/admin/ai-agents`에서 에이전트별 모델 정책, fallback, prompt version, output schema, 실행 한도, 주문 차단 경계를 읽기 전용으로 확인한다.

## Scope

- Add read-only frontend API route `/api/admin/ai-agents`.
- Add Next.js page `/admin/ai-agents`.
- Show agent key, role, domain, prompt version, output schema, primary provider/model, fallback provider/model, local fallback, per-run/request budget, and safety boundary.
- Explicitly show that model editing, canonical writes, broker submit, and real orders are disabled.
- Add a short nav entry for the page.

## Out Of Scope

- No model update form.
- No write API.
- No broker/order flow.
- No scheduler cadence change.
- No recommendation scoring weight change.
- No real OpenAI/Agents SDK invocation from this page.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/app/admin/ai-agents/page.tsx`
  - `apps/web/src/app/layout.tsx`
  - `docs/tasks/admin-agent-model-console-v1/*`

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_ai_agent_registry tests.test_agents_sdk_provider`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli ai-agent-registry-report`
- verification command: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task admin-agent-model-console-v1`

## Safety

This task is visibility-only. It must not create any canonical writes, model mutations, prompt edits, order simulation, broker submission, or scoring changes.
