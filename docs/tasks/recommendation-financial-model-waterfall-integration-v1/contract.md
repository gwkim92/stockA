# recommendation-financial-model-waterfall-integration-v1 Contract

## Task Request

- request: 추천 상세가 `financial_statement_model`을 직접 읽고 professional decision waterfall의 재무 품질 단계가 실제 재무제표 모델 근거를 보여주게 만든다.

현재 종목 상세에는 재무제표 모델이 보이지만 추천 상세는 아직 zero-weight fundamental score component 중심이다. 전문 주식 분석 시스템에서는 추천서가 실제 매출, 마진, 현금흐름, 부채, 이익 품질, 희석 근거를 함께 보여줘야 한다.

## Goal

- goal: `/api/recommendations/{id}`와 `/recommendations/[recommendationId]`에서 추천의 재무 품질 판단이 full financial statement model과 연결되어 보이게 한다. 추천 score, score weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/recommendation-financial-model-waterfall-integration-v1/*`
  - `docs/plans/2026-05-26-recommendation-financial-model-waterfall-integration-v1.md`

## Scope

- Add `financial_statement_model` to recommendation detail live SQL and DTO.
- Reuse the same financial model semantics as stock detail: growth, profitability, cash flow, balance sheet, capital intensity, earnings quality, dilution/share count.
- Upgrade `professional_decision_waterfall.steps[].financial_quality` to cite metric counts, data gaps, latest period, and zero-weight policy.
- Render a Korean financial model section on recommendation detail.

## Non-Goals

- Do not add new financial formulas.
- Do not change recommendation total score or component weights.
- Do not change benchmark/evaluation splits.
- Do not enable live broker submit, automatic order creation, or kill-switch unlock.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-financial-model-waterfall-integration-v1`

## Acceptance Criteria

- Recommendation detail API returns `financial_statement_model`.
- Recommendation professional waterfall financial step uses the model, not only the score component.
- Recommendation detail screen shows the model in user-facing Korean.
- The response keeps `score_policy=recommendation_weights_unchanged`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order`.
- Handoff records local and EC2 verification evidence.
