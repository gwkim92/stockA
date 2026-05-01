# Market Price Batch Ingest

## Goal

이 문서는 여러 종목의 Alpha Vantage daily adjusted payload를 한 번에 canonical `market.daily_price_bar`에 적재하는 첫 batch 경로를 정의한다.

현재 구현 범위:

- repeatable symbol list
- optional fixture directory mode
- per-symbol existing runner 재사용
- aggregate batch summary
- fixture 기반 deterministic 검증

## Why This Step Exists

single-symbol market price ingest는 이미 열려 있다.

실제 유니버스를 적재하려면 종목 하나씩 수동으로 넣는 게 아니라, 여러 심볼을 한 번에 돌려야 한다. 즉 이 단계는 `single-symbol -> batch orchestration` 확장이다.

## Current Flow

1. CLI가 repeatable `--symbol`과 optional `--fixtures-dir`를 받는다.
2. symbol마다 existing `market-price-upsert` runner를 재사용한다.
3. `fixtures-dir`가 있으면 `alpha_vantage_daily_adjusted_<SYMBOL>.json` 규칙으로 fixture를 찾는다.
4. per-symbol success/failure를 유지하면서 batch summary를 반환한다.

## Batch Summary

현재 summary는 다음 필드를 반환한다.

- `requested_symbol_count`
- `succeeded_symbol_count`
- `failed_symbol_count`
- `total_bar_count`
- `results`

각 result는 기존 single-symbol summary를 포함하고, 실패 시 `error`를 남긴다.

## CLI

fixture directory 기반 batch 적재:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-batch-upsert \
  --symbol AAPL \
  --symbol MSFT \
  --fixtures-dir tests/fixtures
```

live path도 가능하지만, 현재 batch 검증은 fixture directory 기준이다.

## Verification

현재 검증 명령:

```bash
bash scripts/verify_market_price_batch_ingest.sh
```

이 검증은:

- docker Postgres migration + seed
- canonical Apple/Microsoft issuer/instrument insert
- 2-symbol batch upsert
- `daily_price_bar` 4건
- `AAPL`, `MSFT` bar 각 2건
- non-null `source_run_id` 4건
- succeeded `market_price_upsert` run 2건

를 확인한다.

## Current Limits

아직 구현하지 않은 것:

- default universe discovery
- parent batch pipeline run
- rate limiting/backoff
- live Alpha Vantage smoke
- turnover value / market cap enrichment

## Next Step

다음으로 자연스러운 확장:

1. `market-universe-bootstrap`
2. `sec-filings-event-retry-policy`
3. cycle snapshot bootstrap
