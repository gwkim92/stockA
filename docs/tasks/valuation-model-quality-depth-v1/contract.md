# valuation-model-quality-depth-v1 Contract

## Task Request

- request: DCF-lite, 상대 배수, 시나리오 범위 밸류에이션을 단순 목표가 카드가 아니라 전문가식 가정·민감도·데이터 품질 근거로 읽을 수 있게 만든다.

현재 `valuation_target_range`는 목표가 하단/기준/상단과 안전마진을 보여주지만, 어떤 입력과 가정이 가격 범위를 만들었는지, 어떤 지점이 약한지, 어떤 변수에 민감한지 부족하다.

## Goal

- goal: 종목, 추천, Thesis 상세의 `valuation_target_range`가 method별 가정, 민감도 case, confidence/data-quality, model limitation을 반환하고 화면에 한국어로 표시한다. 추천 score, score weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_professional_equity_analysis.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/valuation-model-quality-depth-v1/*`
  - `docs/plans/2026-05-26-valuation-model-quality-depth-v1.md`

## Scope

- Add method-level derived fields to valuation DTO: upside by band, valuation gap, Korean evidence summary, assumption items, sensitivity cases, data quality, and limitations.
- Add overall valuation quality summary to `valuation_target_range`.
- Improve future `valuation_snapshot` runner assumptions JSON with explicit assumption, sensitivity, input-quality, and limitation fields.
- Upgrade shared `ValuationTargetRangeCard` so stock/recommendation/thesis pages all show the richer evidence.

## Non-Goals

- Do not change valuation table schema.
- Do not change recommendation total score or component weights.
- Do not change benchmark/evaluation splits.
- Do not enable live broker submit, automatic order creation, or kill-switch unlock.
- Do not claim full DCF/analyst forecast quality; this is still DCF-lite and relative/scenario evidence.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_professional_equity_analysis`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task valuation-model-quality-depth-v1`

## Acceptance Criteria

- `valuation_target_range.methods[]` includes method-level assumptions, sensitivity cases, data quality, limitations, and upside values.
- `valuation_target_range.valuation_quality` summarizes method coverage, confidence, data gaps, warnings, and order boundary.
- Shared valuation card renders the new evidence in Korean on stock/recommendation/thesis detail pages.
- `valuation_snapshot` upsert SQL persists richer `assumptions_json` for future runs.
- Existing `recommendation_weights_unchanged`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order` remain true.
