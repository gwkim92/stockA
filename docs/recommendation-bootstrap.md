# Recommendation Bootstrap

이 문서는 selected strategy universe, deterministic market feature, direct theme membership, cycle state snapshot을 이용해 첫 recommendation batch를 만드는 경로를 설명한다.

## Goal

- source:
  - `signal.strategy_universe_batch`
  - `signal.strategy_universe_member`
  - `signal.instrument_feature_value`
  - `ref.instrument_classification_membership`
  - `signal.cycle_state_snapshot`
- target:
  - `signal.recommendation_batch`
  - `signal.recommendation`

이 단계의 목적은 지금까지 만든 universe, feature, theme, cycle evidence를 하나의 추천 시점으로 묶어 rank, bucket, action, score를 저장하는 것이다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli recommendation-bootstrap \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --score-version bootstrap-v1
```

## Current Input Rule

현재 bootstrap은 보수적이다.

- selected strategy universe 기준
- `internal_theme` taxonomy만 대상
- `derived_theme` membership만 대상
- matching `cycle_state_snapshot`이 있는 instrument-node candidate만 대상
- instrument마다 가장 높은 total score candidate만 recommendation row로 저장
- 초기 생성 시 `thesis_id`는 `null`이며, 후속 `thesis-bootstrap`에서 채운다.

## Component Scores

### `cycle_score`

`signal.cycle_state_snapshot.cycle_score`를 그대로 사용한다.

### `momentum_score`

- primary input: `return_since_first_observation.zscore`
- fallback: `return_since_first_observation`
- normalize range:
  - zscore 기준 `[-2, 2] -> [0, 1]`
  - return fallback 기준 `[-0.20, 0.20] -> [0, 1]`

### `short_term_score`

```text
return_1d normalized from [-0.05, 0.05] to [0, 1]
```

### `rank_score`

```text
(universe_member_count - universe_rank_position) / (universe_member_count - 1)
```

universe member가 1개면 `1.0`으로 처리한다.

## Total Score

```text
0.45 * cycle_score
+ 0.25 * momentum_score
+ 0.15 * short_term_score
+ 0.15 * rank_score
```

## Bucket And Action

- `total_score >= 0.7500`: bucket `core`, action `buy_candidate`, recommended weight `0.0800`
- `total_score >= 0.5500`: bucket `cycle`, action `accumulate_candidate`, recommended weight `0.0400`
- `total_score >= 0.3500`: bucket `watch`, action `watch`
- otherwise: bucket `avoid`, action `exclude`

현재 fixture chain에서는 `AAPL -> watch`, `total_score = 0.3610`이 생성된다.

## Boundary

- AI는 추천 rank를 직접 결정하지 않는다.
- thesis는 이 단계에서 만들지 않고 `thesis-bootstrap`이 recommendation 이후에 연결한다.
- portfolio execution 또는 실거래는 범위 밖이다.
- score component detail은 `signal.recommendation_score_component`에 저장한다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_recommendation_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task recommendation-bootstrap`

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

그리고 recommendation batch 1건, AAPL recommendation 1건, bucket `watch`, action `watch`, total score `0.3610`, latest pipeline run status 성공을 확인한다.

## Next Step

1. `portfolio-review-bootstrap`
2. `live OpenAI Responses provider`
3. `live-data score distribution report`
