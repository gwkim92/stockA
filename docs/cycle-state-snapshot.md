# Cycle State Snapshot

이 문서는 selected strategy universe와 direct internal theme membership, deterministic market feature, recent event heat를 묶어 node-level cycle state를 만드는 첫 bootstrap 경로를 설명한다.

## Goal

- source:
  - `signal.strategy_universe_batch`
  - `signal.strategy_universe_member`
  - `ref.instrument_classification_membership`
  - `signal.instrument_feature_value`
  - `event.event_instrument_impact`
  - `event.event_classification_impact`
- target:
  - `signal.cycle_state_snapshot`

이 단계의 목적은 "어떤 종목이 어떤 노드에 연결되어 있는가"를 넘어서 "그 노드가 지금 어떤 국면인가"를 canonical state로 저장하는 것이다. 이후 recommendation과 review는 이 snapshot을 읽어야 한다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli cycle-state-snapshot \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --score-version bootstrap-v1
```

## Current Input Rule

현재 bootstrap은 아주 보수적이다.

- selected strategy universe 기준
- `internal_theme` taxonomy만 대상
- `derived_theme` membership만 대상
- direct node membership만 계산
- price feature는 existing `signal.instrument_feature_value`만 사용
- event heat는 existing `event.event_instrument_impact`, `event.event_classification_impact`만 사용

## Component Scores

### `trend_score`

- primary input: `average_return_since_first_observation_zscore`
- fallback: `average_return_since_first_observation`
- normalize range:
  - zscore 기준 `[-2, 2] -> [0, 1]`
  - return fallback 기준 `[-0.20, 0.20] -> [0, 1]`

즉 현재는 node member들의 medium-term momentum이 강할수록 trend score가 올라간다.

### `breadth_score`

```text
positive_return_1d_member_count / member_count
```

node member 중 하루 수익률이 양수인 비율이다.

### `event_heat_score`

```text
recent_event_count_basis * average_event_confidence / (member_count * 2)
```

- 30일 내 event가 있으면 그 count를 사용
- 30일 내 event가 없고 90일 내 event만 있으면 `recent_event_count_90d / 3`를 basis로 사용
- 최종 값은 `[0, 1]`로 clamp

현재는 event density를 과대평가하지 않도록 member count와 보수적 분모 2로 나눈다.

### `cycle_score`

```text
0.45 * trend_score
+ 0.35 * breadth_score
+ 0.20 * event_heat_score
```

현재 bootstrap은 trend와 breadth를 우선하고, event heat는 보조 증거로만 사용한다.

## Current State Mapping

현재 state machine은 일부 상태만 먼저 사용한다.

- `expanding`
  - `trend_score >= 0.75`
  - `breadth_score >= 0.70`
  - `event_heat_score >= 0.40`
- `confirming`
  - strong trend/breadth이나 event heat가 낮거나
  - overall `cycle_score >= 0.65`
- `forming`
  - event heat는 들어왔지만 trend/breadth confirmation이 약한 경우
- `correcting`
  - `trend_score <= 0.25`
  - `breadth_score <= 0.25`
  - 단, high event heat `forming` case가 먼저 우선한다
- `basing`
  - low score fallback state

현재 fixture chain에서는 `ANNUAL_REPORTING -> forming`이 생성된다.

## Stored Fields

`signal.cycle_state_snapshot`에 아래가 저장된다.

- `node_id`
- `as_of_date`
- `cycle_state`
- `cycle_score`
- `trend_score`
- `event_heat_score`
- `breadth_score`
- `source_run_id`
- `evidence_json`

`evidence_json`에는 최소 아래가 들어간다.

- `score_version`
- `universe_batch_id`
- `member_count`
- `positive_return_1d_count`
- `member_symbols`
- `average_return_1d`
- `average_return_since_first`
- `average_return_since_first_zscore`
- `recent_event_count_30d`
- `recent_event_count_90d`
- `average_event_confidence`
- component scores

## Current Limits

- parent theme propagation은 아직 없다.
- sector/industry cycle은 아직 없다.
- `earnings_revision_score`, `liquidity_score`, `valuation_score`는 아직 `null`이다.
- classification-level feature table은 아직 도입하지 않았다.
- state machine은 bootstrap이라 `overheating`, `reaccelerating`, `structurally_broken` 같은 고급 state를 아직 적극적으로 쓰지 않는다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_cycle_state_snapshot.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task cycle-state-snapshot`

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
```

그리고 `ANNUAL_REPORTING` cycle snapshot 1건, `cycle_state = forming`, `cycle_score = 0.2075`, latest pipeline run status 성공을 확인한다.

## Next Step

1. `thesis-bootstrap`
2. `recommendation-score-component`
3. `live OpenAI Responses provider`
