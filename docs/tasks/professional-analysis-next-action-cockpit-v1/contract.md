# professional-analysis-next-action-cockpit-v1 Contract

## Task Request

- request: professional equity analysis 흐름도 같이 진행한다.
- context: 재무 정규화, 피어, 밸류에이션, ETF/fund source, source blocker guardrail은 이미 존재하지만 사용자는 다음에 무엇을 봐야 하는지 한눈에 알기 어렵다.

## Goal

- goal: `/api/data-health`와 `/data-health`에 professional analysis next-action summary를 추가해 source coverage, blocked symbols, outcome wait, weight review boundary를 한 화면에서 정리한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/professional-analysis-next-action-cockpit-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark, portfolio positions, or broker/order flow.
- Do not create synthetic financials for source-blocked symbols.
- Do not introduce paid external RAG/graph/vector tooling.

## Scope

- Derive a read-only professional next-action payload from existing source gap, feedback calibration, outcome maturity, and weight review readiness payloads.
- Render a Korean cockpit section that says whether to work on source remediation, outcome wait, or manual weight review preparation.
- Keep detailed source gaps in the existing section.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-analysis-next-action-cockpit-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] API exposes `professional_analysis_next_action`.
- [ ] `/data-health` renders the professional next-action section in Korean.
- [ ] The section distinguishes source-blocked symbols from managed outcome wait.
- [ ] No scoring, benchmark, portfolio, or order mutation occurs.
