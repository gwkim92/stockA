# Market Universe Bootstrap

이 문서는 미국 상장 universe를 canonical reference layer에 올리는 첫 bootstrap 경로를 설명한다.

## Goal

- source: `SEC company_tickers_exchange.json`
- target: `ref.issuer`, `ref.instrument`
- current supported exchange: `Nasdaq`, `NYSE`

이 단계의 목적은 전략용 curated watchlist를 만드는 것이 아니라, 이후 market price/SEC companyfacts/event pipeline이 공통으로 참조할 canonical 미국 상장 universe를 먼저 세우는 것이다.

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli market-universe-bootstrap \
  --company-tickers-json tests/fixtures/sec_company_tickers_exchange_sample.json \
  --exchange Nasdaq \
  --exchange NYSE
```

live SEC source를 쓸 때는 `STOCKANALYSIS_SEC_USER_AGENT`가 필요하다.

## What It Does

1. SEC `company_tickers_exchange` payload를 읽는다.
2. `[cik, name, ticker, exchange]` row를 정규화한다.
3. 현재 seed exchange와 매핑 가능한 `Nasdaq -> XNAS`, `NYSE -> XNYS`만 남긴다.
4. distinct 회사명을 `ref.issuer`에 넣는다.
5. `(exchange_id, primary_symbol)` 기준으로 `ref.instrument`를 upsert한다.
6. `ops.pipeline_run`에 `market_universe_bootstrap` run을 남긴다.

## Summary Shape

- `run_id`
- `total_record_count`
- `selected_record_count`
- `selected_company_count`
- `requested_exchanges`
- `skipped_unsupported_exchange_count`
- `skipped_missing_exchange_count`
- `selected_exchange_counts`
- `selected_symbol_preview`

## Current Assumptions

- canonical issuer name은 SEC company name을 그대로 사용한다.
- `issuer_type`는 `listed_entity`, `instrument_type`는 `listed_security`로 일단 고정한다.
- existing issuer dedupe는 `lower(legal_name) + country_code + issuer_type` 기준으로만 수행한다.
- existing instrument dedupe는 schema unique key인 `(exchange_id, primary_symbol)`를 따른다.

## Current Limits

- `OTC`, `CBOE`, missing exchange row는 skip한다.
- `ETF`, `ADR`, `common stock`를 세부 타입으로 분리하지 않는다.
- issuer CIK를 canonical ref table에 아직 저장하지 않는다.
- delisted propagation과 universe versioning은 아직 없다.

## Why This Shape

현재 목적은 perfect security master가 아니라, SEC와 market ingest가 공통으로 붙을 수 있는 최소 canonical identity layer를 만드는 것이다. 이 단계에서 회사명과 symbol, exchange를 안정적으로 올려야 이후 price batch backfill과 SEC companyfacts/event linkage가 커질 수 있다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-universe-bootstrap`

fixture verify는 sample SEC payload에서 `AAPL -> XNAS`, `BABA -> XNYS` 2건이 canonical instrument로 생성되고 unsupported `BAESY`는 skip되는지 확인한다.

## Next Step

1. `market-price-universe-backfill`
2. `identity-mapping-enrichment`
3. `strategy-universe-slicing`
