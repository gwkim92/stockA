# Strategy Universe Slicing

이 문서는 canonical market universe와 daily price bars를 이용해 중장기 전략용 universe snapshot을 만드는 첫 signal-layer 경로를 설명한다.

## Goal

- source: `ref.instrument`, `ref.exchange`, `market.daily_price_bar`
- target: `signal.strategy_universe_batch`, `signal.strategy_universe_member`
- current strategy example: `long_term_core`

canonical universe는 상장 종목의 기준 identity layer다. strategy universe는 그중 실제 전략이 평가할 수 있는 후보군이다. 이 둘을 분리해야 추천, thesis, 성과 분석이 같은 입력 universe를 재현할 수 있다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli strategy-universe-slice \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --exchange Nasdaq \
  --exchange NYSE \
  --min-observation-count 2 \
  --min-adjusted-close 50 \
  --limit 10
```

## What It Does

1. active canonical instruments를 조회한다.
2. exchange, market, delisted status를 필터링한다.
3. `as_of_date` 이하 latest price bar와 observation count를 계산한다.
4. minimum observation count와 minimum adjusted close를 적용한다.
5. deterministic rank를 만든다.
6. `signal.strategy_universe_batch`에 snapshot metadata를 저장한다.
7. `signal.strategy_universe_member`에 selected instruments를 저장한다.

## Selection Rule

- `instrument.market_code = 'US'`
- `instrument.is_active = true`
- `instrument.delisted_at is null`
- default exchange: `Nasdaq`, `NYSE`
- latest price bar exists on or before `as_of_date`
- observation count is at least `min_observation_count`
- latest adjusted close is at least `min_adjusted_close`

현재 ranking은 임시 deterministic rule이다.

```text
observation_count + latest_adjusted_close / 1000, then symbol
```

이 ranking은 투자 점수가 아니다. 동일한 fixture/input에서 항상 같은 snapshot을 만들기 위한 bootstrap용 ordering이다.

## AI Boundary

이 단계에는 AI를 넣지 않는다. strategy universe slicing은 재현 가능한 deterministic filter여야 한다. AI-derived theme, event, thesis signals는 후속 feature/cycle/thesis layer에서 evidence로 붙이고, 이 deterministic universe boundary를 대체하지 않는다.

## Current Limits

- liquidity, market cap, turnover filter가 아직 없다.
- sector/theme/cycle score를 아직 사용하지 않는다.
- recommendation batch와 직접 연결하지 않는다.
- AI-based ranking을 하지 않는다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_strategy_universe_slicing.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task strategy-universe-slicing`

fixture verify는 `market-universe-bootstrap -> market-price-universe-backfill -> strategy-universe-slice`를 이어 실행하고 `AAPL`, `BABA` 2개 member가 생성되는지 확인한다.

## Next Step

1. `market-feature-snapshot`
2. `instrument-theme-enrichment`
3. `cycle-state-snapshot`
