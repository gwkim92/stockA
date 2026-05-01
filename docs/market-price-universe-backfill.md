# Market Price Universe Backfill

이 문서는 canonical universe를 읽어 batch daily price ingest를 자동화하는 경로를 설명한다.

## Goal

- source of symbol selection: canonical `ref.instrument`
- execution engine: existing `market-price-batch-upsert`
- current supported exchange filter: `Nasdaq`, `NYSE`

즉 이 경로는 새 price upsert 로직을 만드는 것이 아니라, 이미 bootstrap된 canonical universe와 기존 batch price runner를 연결하는 orchestration layer다.

## CLI

```bash
STOCKANALYSIS_PSQL_COMMAND="psql -U postgres -d stockanalysis" \
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-price-universe-backfill \
  --fixtures-dir tests/fixtures \
  --exchange Nasdaq \
  --exchange NYSE
```

live mode에서는 `STOCKANALYSIS_ALPHA_VANTAGE_API_KEY`와 `STOCKANALYSIS_PSQL_COMMAND`가 필요하다.

## What It Does

1. canonical active instrument를 `ref.instrument`에서 조회한다.
2. optional exchange filter와 limit를 적용한다.
3. 선택된 symbol list를 existing `run_market_price_batch_upsert`에 넘긴다.
4. 각 symbol은 기존과 동일하게 개별 `market_price_upsert` run을 남긴다.

## Selection Rule

- `ref.instrument.is_active = true`
- `ref.instrument.delisted_at is null`
- `ref.exchange.mic_code in ('XNAS', 'XNYS')` by default
- order by `primary_symbol`

## Summary Shape

- `selected_symbol_count`
- `requested_exchanges`
- `selected_exchange_counts`
- `selected_symbol_preview`
- `requested_symbol_count`
- `succeeded_symbol_count`
- `failed_symbol_count`
- `total_bar_count`
- `results`

## Current Assumptions

- canonical universe bootstrap이 먼저 실행되어 있어야 한다.
- explicit symbol batch runner가 canonical selection 이후 단계에서 그대로 재사용된다.
- exchange filter semantics는 universe bootstrap과 동일하게 유지한다.

## Current Limits

- parent backfill run abstraction은 없다.
- retry, backoff, live rate limit handling은 없다.
- canonical universe 전체가 곧 전략 universe는 아니다.
- selection은 `classification`이나 `signal` score를 아직 사용하지 않는다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_universe_backfill.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-universe-backfill`

fixture verify는 `market-universe-bootstrap`으로 canonical `AAPL`, `BABA`를 먼저 만들고, 그 universe를 읽어 daily bar 4건이 생성되는지 확인한다.

## Next Step

1. `market-price-live-smoke`
2. `strategy-universe-slicing`
3. `market-feature-snapshot`
