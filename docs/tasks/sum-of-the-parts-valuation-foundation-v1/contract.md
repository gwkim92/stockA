# sum-of-the-parts-valuation-foundation-v1 Contract

## Task Request

- request: 전문가식 밸류에이션 부족분 중 하나인 sum-of-the-parts 관점을 기존 valuation evidence layer에 추가한다.

현재 valuation은 DCF-lite, 상대 배수, 시나리오 범위가 있지만, 사업 가치와 재무상태 조정이 어떻게 합쳐져 목표가가 되는지 분리해서 보여주지 못한다.

## Goal

- goal: `market.sum_of_parts_component`에 보수적인 SOTP 구성요소를 저장하고, `market.valuation_snapshot.method='sum_of_parts'`가 이 구성요소를 합산해 valuation evidence로 노출된다. 추천 score, score weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `db/migrations/0025_sum_of_parts_valuation.sql`
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/professional_coverage_expansion.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_professional_coverage_expansion.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/sum-of-the-parts-valuation-foundation-v1/*`
  - `docs/plans/2026-05-26-sum-of-the-parts-valuation-foundation-v1.md`

## Scope

- Add `market.sum_of_parts_component` as canonical SOTP evidence rows.
- Extend `market.valuation_snapshot.method` check to include `sum_of_parts`.
- Add backend CLI runner: `stockanalysis-operations sum-of-parts-valuation-run`.
- Generate conservative SOTP components from available public financial metrics:
  - operating business value from forecast/free-cash-flow evidence.
  - balance-sheet adjustment from assets/liabilities/share count when available.
  - data-gap reserve to avoid overclaiming when segment-level data is missing.
- Extend valuation snapshot SQL so `sum_of_parts` is included only when component evidence exists.
- Extend frontend DTO/UI so stock, recommendation, and thesis detail pages show SOTP component evidence in Korean.

## Non-Goals

- Do not build a full segment-level sell-side SOTP model.
- Do not parse business segment footnotes in this task.
- Do not change recommendation total score or component weights.
- Do not change benchmark/evaluation split.
- Do not enable automatic order creation or live broker submit.
- Do not introduce paid external data or paid model services.

## Schema Change Disclosure

- Adds table `market.sum_of_parts_component`.
- Alters `market.valuation_snapshot.method` validation to allow `sum_of_parts`.
- The new table and valuation method are read-only evidence. They are not recommendation score sources in this task.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_frontend_live_adapter tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `bash scripts/verify_migrations.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task sum-of-the-parts-valuation-foundation-v1`

## Acceptance Criteria

- Migration creates `market.sum_of_parts_component` and allows `sum_of_parts` in `market.valuation_snapshot.method`.
- SOTP runner dry-run returns coverage preview without writes.
- SOTP runner execute records `ops.pipeline_run`, upserts component rows, and keeps `recommendation_scoring_mutated=false`.
- Valuation snapshot SQL references SOTP components where available and records component evidence in `assumptions_json`.
- Frontend valuation payload exposes SOTP component evidence without breaking older snapshots.
- Shared valuation card renders SOTP component evidence in Korean.
- Existing order boundary remains `read_only_no_order`.
