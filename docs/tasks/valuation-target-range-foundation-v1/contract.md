# valuation-target-range-foundation-v1 Contract

## Task Request

- request: 기존 `market.valuation_snapshot` 데이터를 사용해 목표가 하단/기준/상단, 상승여지, 안전마진, 방법별 가정을 종목·추천·Thesis 상세에서 확인할 수 있게 만든다.

전문 주식 분석 시스템 기준으로 부족한 밸류에이션 모델 가시성을 보강한다. 기존 `market.valuation_snapshot` 데이터를 사용해 목표가 하단/기준/상단, 상승여지, 안전마진, 방법별 가정을 종목·추천·Thesis 상세에서 확인할 수 있게 만든다.

## Goal

- goal: 종목, 추천, Thesis 상세 사용자가 현재 가격이 적정한지 판단할 수 있도록 `valuation_target_range` evidence를 API와 화면에 노출한다. 추천 score, score weight, broker/order boundary는 변경하지 않는다.

종목, 추천, Thesis 상세 사용자가 현재 가격이 적정한지 판단할 수 있도록 `valuation_target_range` evidence를 API와 화면에 노출한다. 이 작업은 추천 score, score weight, broker/order boundary를 변경하지 않는 read-only 표시 계층이다.

## Purpose

전문 주식 분석 흐름에서 현재 약한 지점인 밸류에이션 목표가 범위를 종목, 추천, Thesis 상세 판단 화면에 연결한다. 목표는 기존 `market.valuation_snapshot` 산출물을 `현재가 -> 목표가 하단/기준/상단 -> 상승여지/안전마진 -> 추천/보유 검토` 흐름으로 읽을 수 있게 만드는 것이다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/valuation-target-range-foundation-v1/*`
  - `docs/plans/2026-05-26-valuation-target-range-foundation-v1.md`

## Scope

- `market.valuation_snapshot`의 최신 방법별 snapshot을 live frontend state SQL에 연결한다.
- FastAPI read-only DTO에 `valuation_target_range`를 추가한다.
- 종목 상세, 추천 상세, Thesis 상세에서 목표가 범위와 산출 방법을 한국어로 표시한다.
- 추천 professional decision waterfall의 밸류에이션 단계가 목표가 범위 evidence를 사용한다.
- 모든 결과는 읽기 전용이다. 자동 주문, broker submit, 추천 score weight 변경은 하지 않는다.

## Non-Goals

- DCF, peer multiple, scenario 산식 자체를 변경하지 않는다.
- `signal.recommendation_score_component` weight나 total score를 변경하지 않는다.
- 실거래, 주문 제출, broker credential, kill-switch unlock을 구현하지 않는다.
- 유료 데이터나 외부 valuation provider를 도입하지 않는다.

## Invariants

- `automatic_order_allowed=false`
- `broker_submit_allowed=false`
- `order_boundary=read_only_no_order`
- `score_policy=recommendation_weights_unchanged`
- DB URL, API key, provider secret은 응답과 문서에 노출하지 않는다.

## Deliverables

- API DTO: `valuation_target_range`
- Backend helper: valuation method rows를 target range payload로 정규화
- SQL: stock/recommendation/thesis detail state에서 최신 valuation snapshot rows 조회
- Frontend: `/stocks/[symbol]`, `/recommendations/[recommendationId]`, `/theses/[thesisId]`에 목표가 범위 표시
- Tests: live adapter contract, SQL read-only coverage, Next typecheck/build
- Handoff: 구현 내용, 검증 결과, 남은 위험 기록

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task valuation-target-range-foundation-v1`

## Acceptance Criteria

- 종목 상세 API가 `valuation_target_range.status=available`일 때 method count, base price, target low/base/high, upside low/base/high, margin of safety, confidence, method list를 반환한다.
- 추천 상세 API의 professional decision waterfall에서 valuation step이 목표가 범위와 상승여지를 fact로 보여준다.
- Thesis 상세 API와 화면에서 valuation sensitivity만이 아니라 target range snapshot을 별도로 확인할 수 있다.
- 추천 점수와 weight는 변경되지 않는다.
- 전체 변경은 하네스 규칙에 맞게 task 문서와 검증 증거를 남긴다.
