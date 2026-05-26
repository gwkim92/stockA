# Session Handoff

## Current Status

- 진행 중: task contract를 만들었고, benchmark composition storage와 risk guardrail drift 계산을 구현한다.

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- external paid data provider 금지.

## Exact Next Step

- exact next step: `db/migrations/0023_benchmark_composition.sql`과 `db/seeds/0006_benchmark_composition_seed.sql`을 추가하고 `portfolio_risk_budget_guardrail`이 composition을 읽도록 수정한다.
