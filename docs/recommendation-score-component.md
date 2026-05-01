# Recommendation Score Component

이 문서는 recommendation total score를 구성하는 component score와 weight를 DB에 저장하는 경로를 설명한다.

## Goal

- source:
  - `signal.strategy_universe_batch`
  - `signal.strategy_universe_member`
  - `signal.instrument_feature_value`
  - `signal.cycle_state_snapshot`
  - `signal.recommendation`
- target:
  - `signal.recommendation_score_component`

이 단계의 목적은 recommendation의 total score만 남기는 것이 아니라 어떤 component가 어떤 weight로 점수에 기여했는지 저장하는 것이다.

## Current Components

현재 component는 네 개다.

- `cycle_score`: linked internal theme의 current cycle score
- `momentum_score`: `return_since_first_observation` 기반 medium-term momentum
- `short_term_score`: `return_1d` 기반 short-term price movement
- `rank_score`: selected strategy universe 내부 상대 rank

## Current Weights

```text
cycle_score      0.45
momentum_score   0.25
short_term_score 0.15
rank_score       0.15
```

weighted sum은 `signal.recommendation.total_score`와 일치해야 한다.

현재 fixture chain에서는 AAPL component가 아래처럼 저장된다.

```text
cycle_score      0.2075 * 0.45
momentum_score   0.2500 * 0.25
short_term_score 0.3672 * 0.15
rank_score       1.0000 * 0.15
= total_score    0.3610
```

## Boundary

- score formula는 이번 단계에서 바꾸지 않는다.
- AI는 component score를 만들거나 rank를 결정하지 않는다.
- explanation은 deterministic text다.
- thesis, review, portfolio action은 변경하지 않는다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_recommendation_score_component.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task recommendation-score-component`

현재 Docker verify는 아래를 이어 실행한다.

```text
market-universe-bootstrap
-> market-price-universe-backfill
-> strategy-universe-slice
-> market-feature-snapshot
-> sec-filings-upsert
-> sec-filing-raw-fetch
-> sec-filings-event-extract
-> event-classification-impact-bootstrap
-> event-instrument-impact-bootstrap
-> instrument-theme-enrichment
-> cycle-state-snapshot
-> recommendation-bootstrap
```

그리고 `signal.recommendation_score_component` table 존재, recommendation 1건, score component 4건, AAPL weighted sum `0.3610`, latest `recommendation_bootstrap` pipeline run status 성공을 확인한다.

## Next Step

1. `portfolio-review-bootstrap`
2. `live OpenAI Responses provider`
3. `live-data score distribution report`
