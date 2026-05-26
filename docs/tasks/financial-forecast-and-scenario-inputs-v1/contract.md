# financial-forecast-and-scenario-inputs-v1 Contract

## Task Request

- request: DCF-lite와 시나리오 밸류에이션이 단순 고정 성장률/품질 점수만 보여주는 상태를 벗어나, 매출·마진·CAPEX·FCF forecast 입력을 명시적으로 저장하고 화면/API에서 추적 가능하게 만든다.

## Goal

- goal: `market.financial_forecast_input`에 보수/base/낙관 5년 forecast rows를 저장하고, valuation snapshot과 frontend DTO가 이 forecast evidence를 읽어 DCF/scenario 가정의 근거를 보여준다. 추천 score, score weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `db/migrations/0024_financial_forecast_inputs.sql`
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/financial-forecast-and-scenario-inputs-v1/*`
  - `docs/plans/2026-05-26-financial-forecast-and-scenario-inputs-v1.md`

## Scope

- Add a canonical forecast input table for deterministic financial forecast scenarios.
- Add backend CLI runner: `stockanalysis-operations financial-forecast-inputs-run`.
- Store scenario/year rows for revenue, revenue growth, operating margin, free-cash-flow margin, CAPEX intensity, and free cash flow.
- Extend valuation snapshot assumptions JSON so DCF/scenario methods point to available forecast inputs.
- Extend valuation DTO/UI so stock, recommendation, and thesis detail pages show forecast scenario evidence in Korean.

## Non-Goals

- Do not build a full sell-side analyst model.
- Do not change recommendation total score or component weights.
- Do not change benchmark/evaluation split.
- Do not enable automatic order creation or live broker submit.
- Do not introduce paid external data or paid model services.

## Schema Change Disclosure

- Adds table `market.financial_forecast_input`.
- This table is read-only evidence for valuation. It is not a recommendation score source in this task.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task financial-forecast-and-scenario-inputs-v1`

## Acceptance Criteria

- Migration creates `market.financial_forecast_input` with idempotent unique key.
- Forecast runner dry-run returns coverage preview without writes.
- Forecast runner execute records `ops.pipeline_run`, upserts forecast rows, and keeps `recommendation_scoring_mutated=false`.
- Valuation snapshot SQL references forecast inputs where available and records forecast evidence in `assumptions_json`.
- Frontend valuation payload exposes forecast scenario evidence without breaking older snapshots.
- Shared valuation card renders forecast scenario evidence in Korean.
- Existing order boundary remains `read_only_no_order`.
