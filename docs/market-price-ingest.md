# Market Price Ingest

## Goal

이 문서는 Alpha Vantage daily adjusted price JSON을 canonical `market.daily_price_bar`에 적재하는 첫 경로를 정의한다.

현재 구현 범위:

- Alpha Vantage daily adjusted JSON 정규화
- exact-match canonical instrument lookup
- `market.daily_price_bar` upsert
- fixture 기반 deterministic 검증

## Why This Step Exists

이제 macro, SEC event, companyfacts까지 모두 canonical DB에 들어간다.

다음으로 필요한 것은 종목 가격 시계열이다. 추천, cycle, 보유 검토, 성과 분석은 모두 daily price history를 기본 입력으로 사용한다.

즉 이 단계는 `market data source -> canonical daily bar table` 전환의 첫 ingest path다.

## Current Flow

1. CLI가 symbol과 optional daily adjusted fixture path를 받는다.
2. Alpha Vantage payload의 `Time Series (Daily)`를 읽는다.
3. symbol 기준으로 canonical instrument exact-match lookup을 수행한다.
4. normalized daily bars를 `market.daily_price_bar`에 upsert한다.
5. run 결과를 `ops.pipeline_run`에 기록한다.

## Current Mapping

현재 canonical mapping은 다음과 같다.

- `1. open` -> `open`
- `2. high` -> `high`
- `3. low` -> `low`
- `4. close` -> `close`
- `5. adjusted close` -> `adjusted_close`
- `6. volume` -> `volume`
- `turnover_value`, `market_cap` -> 현재 `null`
- `source_run_id` -> `ops.pipeline_run.run_id`

현재 instrument resolution은 `ref.instrument.primary_symbol` case-insensitive exact match만 지원한다.

## CLI

canonical DB에 적재:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-upsert \
  --symbol AAPL
```

fixture 기반 적재:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-upsert \
  --symbol AAPL \
  --prices-json tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json
```

## Verification

현재 검증 명령:

```bash
bash scripts/verify_market_price_ingest.sh
```

이 검증은:

- docker Postgres migration + seed
- canonical Apple issuer/instrument insert
- fixture 기반 market price upsert
- `daily_price_bar` 2건
- latest adjusted close와 volume 값 확인
- non-null `source_run_id` 2건
- latest `market_price_upsert` run status

를 확인한다.

## Current Limits

아직 구현하지 않은 것:

- multi-symbol batch ingest
- turnover value / market cap enrichment
- dividends / split history 별도 적재
- intraday bars
- live Alpha Vantage smoke를 포함한 기본 검증

## Next Step

다음으로 자연스러운 확장:

1. `market-price-batch-ingest`
2. `sec-filings-event-retry-policy`
3. cycle snapshot bootstrap
