# professional-analysis-depth-v2 Contract

## Task Request

- request: active 추천/보유 종목별 professional analysis depth를 점검하고 부족한 종목을 보강할 수 있게 한다.
- context: 운영 gate는 닫혔고, 다음 병목은 투자 판단 품질이다. 사용자는 전문가식 기업분석, 밸류에이션, 피어 비교, 포트폴리오 리스크를 더 깊게 녹여내길 원한다.

## Goal

- goal: `/api/data-health`와 `/data-health`가 active 추천/보유 후보별 재무·피어·밸류에이션·산업·리서치·thesis·fund source coverage 깊이를 보여준다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/professional-analysis-depth-v2/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark, portfolio positions, or broker/order flow.
- Do not synthesize financials for source-blocked symbols.
- Do not introduce paid external data/RAG/vector/graph tooling.

## Scope

- Add a read-only professional analysis depth payload to data-health.
- Compute active candidate count, complete candidate count, source-blocked count, average coverage ratio, layer coverage, and weakest candidate examples.
- Render the depth on `/data-health` in Korean.
- Keep EROK-like blockers visible but excluded from professional decision inputs.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-analysis-depth-v2`
- verification command: `git diff --check`

## Done Criteria

- [x] Data-health API exposes `professional_analysis_depth`.
- [x] Data-health page shows professional coverage depth and weakest candidates.
- [x] Tests cover SQL and DTO shape.
- [x] EC2 smoke confirms live data renders.
