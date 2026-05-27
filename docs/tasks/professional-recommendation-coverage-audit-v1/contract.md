# professional-recommendation-coverage-audit-v1 Contract

## Task Request

- request: active 추천 각각에 대해 재무, 피어, 밸류에이션, 산업 포지션, AI 리서치, thesis, paper validation, source blocker가 제대로 붙었는지 감사한다.

## Goal

- goal: `/api/data-health`와 `/data-health`가 추천별 professional evidence coverage를 보여주고, source-blocked/coverage-gap/paper-pending 후보를 추천 weight와 주문 변경 없이 구분한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/professional-recommendation-coverage-audit-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper trade execution behavior.
- Do not synthesize missing financial facts for source-blocked symbols.
- Do not introduce paid external services.

## Scope

- Add a read-only `professional_recommendation_coverage_audit` data-health payload.
- Include recommendation-level rows with layer checks and paper validation state.
- Render a Korean audit section in `/data-health`.
- Preserve all order and weight boundaries as blocked/read-only.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-recommendation-coverage-audit-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] `/api/data-health` includes `professional_recommendation_coverage_audit`.
- [x] Audit rows show recommendation id, symbol, layer checks, source blocker, thesis, paper validation, and read-only boundary.
- [x] `/data-health` renders the recommendation-level audit.
- [x] Local verification passes.
- [x] EC2 route smoke confirms live rendering.
