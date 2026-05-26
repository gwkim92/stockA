# Session Handoff

## Current Status

- 진행 중: task contract를 만들었고, full SPY benchmark drift에서 리밸런싱 검토 후보를 만드는 backend DTO/UI 작업을 시작한다.

## Implementation Notes

- authoritative source는 `ai.eval_run`의 latest `portfolio_risk_budget_guardrail.score_json.benchmark_drift.top_active_positions`이다.
- 이번 작업은 주문 목표나 수량을 계산하지 않는다.
- 후보는 active weight의 절대값과 방향만 사용해 검토 우선순위를 만든다.
- overweight는 `trim_active_overweight_review`, underweight는 `review_active_underweight_gap`으로 노출한다.
- 모든 후보는 `order_boundary=read_only_no_order`를 유지한다.

## Verification

- 아직 실행 전.

## Guardrails

- 추천 weight 변경 금지.
- broker submit/live order 금지.
- benchmark/evaluation split 변경 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: `src/stockanalysis/frontend/live_adapter.py`에 benchmark drift candidate builder를 추가하고 `tests/test_frontend_live_adapter.py`에 contract test를 작성한다.
