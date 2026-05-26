# Session Handoff

## Current Status

- 진행 중: task contract를 만들었고, data-health에 benchmark drift 품질을 노출하는 backend/frontend 변경을 진행한다.

## Implementation Notes

- data-health는 최신 `portfolio_risk_budget_guardrail` eval의 `benchmark_drift`를 읽어야 한다.
- 품질 판정은 사용자 판단 보조 정보이며 추천 점수나 주문 가능 여부를 바꾸지 않는다.
- partial benchmark composition은 full benchmark drift로 표현하면 안 된다.

## Verification

- 아직 실행 전.

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: `/api/data-health` payload에 `benchmark_drift_quality`를 추가하고, `/data-health` 화면에 품질 카드를 노출한다.
