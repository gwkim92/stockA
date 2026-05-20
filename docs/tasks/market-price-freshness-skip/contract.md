# Task Contract

## Task

- 이름: market-price-freshness-skip
- 요청: Twelve Data/free provider 호출 전에 이미 최신 가격 데이터가 있는 심볼을 skip하여 무료 provider budget 낭비를 막는다.
- 담당: Codex
- 날짜: 2026-05-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: market price batch/free-backfill path가 `skip_if_fresh` 옵션으로 DB의 최신 `market.daily_price_bar.trade_date`를 확인하고, 이미 target date 이상이면 provider request count를 증가시키거나 external provider를 호출하지 않는다.

## Why

- 현재 runner는 `max_requests_per_run`과 ledger로 호출량은 제한하지만, 같은 watchlist를 다시 실행하면 이미 최신인 심볼도 다시 호출한다.
- 무료 provider quota는 실제 데이터가 stale인 심볼에만 써야 한다.

## Scope

- `market.daily_price_bar` latest trade date lookup helper를 추가한다.
- `run_market_price_batch_upsert`에 `skip_if_fresh`와 `freshness_date` 옵션을 추가한다.
- CLI와 operations free-backfill runner에 freshness 옵션을 전파한다.
- skipped result에는 reason, latest trade date, target freshness date를 남긴다.
- Unit tests로 skip 시 provider loader가 호출되지 않고 provider_request_count가 증가하지 않는 것을 검증한다.

## Boundaries

- 실제 provider call은 이 task 구현 검증에서 하지 않는다.
- DB schema, scoring, benchmark, evaluation split은 바꾸지 않는다.
- scheduler activation과 broker/order flow는 범위 밖이다.
- freshness 기준은 우선 daily bar latest date만 본다. 거래소 holiday/calendar 정교화는 다음 task로 남긴다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/market/backfill.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/operations/market_price_free_backfill.py`
  - `src/stockanalysis/operations/cli.py`
  - tests and fixtures
  - task docs

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price tests.test_market_backfill tests.test_market_price_free_backfill tests.test_data_operations_cli tests.test_ingest_cli`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-price-freshness-skip`
  - `git diff --check`

## Done Criteria

- [x] batch path가 fresh symbol을 provider call 전에 skip한다.
- [x] skipped fresh symbol은 provider_request_count를 증가시키지 않는다.
- [x] free-backfill runner가 freshness 옵션을 batch path로 전달한다.
- [x] CLI에서 freshness 옵션을 사용할 수 있다.
- [x] focused tests와 AWH가 통과한다.
