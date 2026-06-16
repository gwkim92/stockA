# ai-agent-registry-foundation-v1 Contract

## Task Request

- request: Agents SDK 중심 투자 운영 구조로 전환하기 위한 첫 기반을 만든다.
- context: 현재 AI prompt와 provider 호출은 `translation.py`, `ai_extract.py`, `cycle_community_ai_summary.py`, `equity_research_reporting.py`, `sec/ai_event_extract.py`에 흩어져 있고, 사이트에서 에이전트별 모델/프롬프트/상태를 제어할 수 없다.

## Goal

- goal: 에이전트 정의, 모델 정책, 전문 prompt version, tool permission, agent run state를 Postgres와 Python catalog로 표현한다.
- goal: prompt는 OpenAI managed prompt object가 아니라 repo-managed/versioned prompt로 관리한다.
- goal: 이후 Agents SDK runtime, 관리자 모델 선택 화면, backlog/replay, OAuth fallback을 붙일 수 있는 구조를 만든다.

## Research Basis

- OpenAI Agents SDK는 서버가 orchestration, tool execution, state, approvals를 소유할 때 적합하다.
- OpenAI prompt guidance는 production prompt를 application code에 두고, typed inputs, tests/evals, version control로 관리하라고 권장한다.
- Guardrails/human review는 side effect 전 pause/approval 및 input/output/tool validation에 사용한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/ai-agent-registry-foundation-v1/*`
  - `db/migrations/0032_ai_agent_registry.sql`
  - `db/seeds/0007_ai_agent_registry_seed.sql`
  - `src/stockanalysis/ai_agents/*`
  - `src/stockanalysis/operations/ai_agent_registry.py`
  - `src/stockanalysis/operations/cli.py`
  - `pyproject.toml`
  - `tests/test_ai_agent_registry.py`

## Non-Goals

- Do not migrate existing runners to Agents SDK in this slice.
- Do not call OpenAI API or Codex OAuth from tests.
- Do not change scheduler cadence.
- Do not change recommendation weights, benchmark definitions, portfolio positions, or order/broker behavior.
- Do not expose model controls to public users; this task only creates backend/catalog foundation.

## Acceptance Criteria

- DB schema supports agent definitions, prompt versions, model policies, tool permissions, and run state.
- Seed includes the initial investment-agent team and professional Korean-first prompt instructions.
- Python catalog exposes the same agent keys, prompt versions, model tiers, and safety boundaries for future runtime use.
- Tests verify the catalog, prompt specialization, no-order boundary, and SQL seed coverage.
- Handoff documents what was implemented and the next task.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_ai_agent_registry`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli ai-agent-registry-report`
- verification command: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-agent-registry-foundation-v1`
