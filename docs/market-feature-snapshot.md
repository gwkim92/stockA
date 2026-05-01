# Market Feature Snapshot

이 문서는 strategy universe members에 대해 recommendation 이전의 deterministic market feature snapshot을 만드는 경로를 설명한다.

## Goal

- source: `signal.strategy_universe_batch`, `signal.strategy_universe_member`, `market.daily_price_bar`
- target: `signal.feature_definition`, `signal.instrument_feature_value`

strategy universe가 "무엇을 평가할 것인가"를 고정한다면, market feature snapshot은 "그 universe를 어떤 deterministic 수치로 볼 것인가"를 고정한다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-feature-snapshot \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --feature-set-version bootstrap-v1
```

## Current Feature Set

- `latest_adjusted_close`
- `return_1d`
- `return_since_first_observation`
- `realized_volatility_bootstrap`
- `observation_count`

현재 feature set은 bootstrap deterministic baseline이다. recommendation score나 cycle score가 아니다.

## Formulas

### `latest_adjusted_close`

```text
latest adjusted close on or before as_of_date
```

### `return_1d`

```text
latest_adjusted_close / previous_adjusted_close - 1
```

### `return_since_first_observation`

```text
latest_adjusted_close / first_adjusted_close - 1
```

### `realized_volatility_bootstrap`

```text
population stddev of available daily returns
```

bootstrap 예외:

- available return이 1개뿐이면 그 절대값을 volatility proxy로 사용한다.

### `observation_count`

```text
number of adjusted close observations used
```

## Zscore

각 feature는 snapshot 내 instruments 기준 cross-sectional population zscore를 계산한다.

- 분산이 0이면 `zscore = null`
- 현재 fixture universe는 2종목이라 `observation_count`는 zscore가 `null`

## Evidence

각 `signal.instrument_feature_value.evidence_json`에는 최소 아래가 들어간다.

- `feature_set_version`
- `universe_batch_id`
- `rank_position`
- `observation_count`
- `first_trade_date`
- `latest_trade_date`
- `as_of_date`

## Boundary

- AI는 이 단계에 개입하지 않는다.
- feature snapshot은 strategy universe 다음의 deterministic boundary다.
- AI path는 `event-intelligence-llm-extract`로 따로 진행되며, 이후 recommendation/thesis 단계에서 합쳐질 수 있다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_market_feature_snapshot.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-feature-snapshot`

fixture verify는 아래를 이어 실행한다.

```text
market-universe-bootstrap
-> market-price-universe-backfill
-> strategy-universe-slice
-> market-feature-snapshot
```

그리고 feature definition 5건, feature row 10건, latest run status 성공을 확인한다.

## Next Step

1. `instrument-theme-enrichment`
2. `cycle-state-snapshot`
3. `live OpenAI Responses provider`
