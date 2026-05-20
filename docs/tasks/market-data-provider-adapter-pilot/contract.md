# Task Contract

## Task

- 이름: market-data-provider-adapter-pilot
- 요청: broad universe 가격 수집을 위해 Alpha Vantage 외 무료 provider pilot을 시작한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 기존 `market.daily_price_bar` upsert 경로가 provider-neutral daily OHLCV normalization을 지원하고, Twelve Data `time_series` fixture를 통해 같은 canonical table upsert path를 검증할 수 있다.

## Why

- Alpha Vantage 공식 무료 한도 25 requests/day는 하루 1회는 아니지만 broad universe 운영에는 부족하다.
- Twelve Data는 free/basic plan에서 800 API credits/day를 문서화하고 있어 첫 no-cost broad-market pilot 후보로 가장 현실적이다.

## Scope

- `STOCKANALYSIS_TWELVE_DATA_API_KEY` runtime config를 추가한다.
- `twelve_data` ingest source adapter와 `time_series_daily` request builder를 추가한다.
- market price loader/upsert/batch/free-backfill runner에 `provider` 파라미터를 추가한다.
- provider alias를 canonical provider name으로 정규화한다.
- `/api/data-health` provider budget lookup이 `STOCKANALYSIS_MARKET_PRICE_PROVIDER`를 따르게 한다.
- Twelve Data daily OHLCV fixture normalization과 upsert path unit tests를 추가한다.
- 실제 Twelve Data provider call은 API key 존재와 명시 승인 전까지 하지 않는다.

## Boundaries

- `.env` secret 값은 읽더라도 출력하거나 문서에 남기지 않는다.
- DB schema, scoring, benchmark, evaluation split은 바꾸지 않는다.
- broker/order flow, paper trading, real trading은 범위 밖이다.
- Twelve Data adjusted-price 품질은 fixture normalization까지만 보고, 실제 provider drift는 다음 live smoke에서 검증한다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/ingest/registry.py`
  - `src/stockanalysis/ingest/sources/twelve_data.py`
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/market/backfill.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/operations/market_price_free_backfill.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - tests and fixtures
  - task docs

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_sources tests.test_market_price tests.test_market_backfill tests.test_market_price_free_backfill tests.test_data_operations_cli tests.test_ingest_cli`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-data-provider-adapter-pilot`
  - `git diff --check`

## Done Criteria

- [x] Twelve Data source adapter가 존재한다.
- [x] Twelve Data daily fixture가 canonical price bars로 normalize된다.
- [x] `market-price-upsert`와 free-backfill path가 provider를 전달한다.
- [x] provider별 ledger 분리가 가능하다.
- [x] focused tests와 AWH가 통과한다.
- [x] data-health가 configured market price provider의 ledger를 표시한다.
