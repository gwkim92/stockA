# professional-analysis-quality-v1 Contract

## Task Request

- request: 재무/밸류에이션/피어/산업분석 결과가 추천 근거로 제대로 붙는지 품질 점검한다. 단, 추천 weight 변경은 outcome 표본이 충분해질 때까지 계속 금지한다.

## Goal

- goal: `/api/data-health`와 `/data-health`가 active 추천 후보의 전문 분석 품질을 재무 지표, 피어 비교, 밸류에이션, 산업 포지션, AI 리서치, source blocker, weight/order boundary로 분리해 보여준다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/professional-analysis-quality-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper trade execution behavior.
- Do not synthesize missing financial facts for source-blocked symbols.
- Do not introduce paid external services.

## Scope

- Add a read-only `professional_analysis_quality` data-health payload derived from existing professional coverage, source gap, outcome calibration, and weight-readiness evidence.
- Add Korean data-health visibility so the user can see which professional-analysis layer is attached and which layer is missing.
- Keep the quality result as evidence and gate visibility only.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-analysis-quality-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] `/api/data-health` includes `professional_analysis_quality`.
- [x] `/data-health` renders a user-facing professional quality section.
- [x] Tests assert source-limited professional analysis remains visible but does not allow weight/order changes.
- [x] Local verification passes.
- [x] EC2 route smoke confirms live rendering.
