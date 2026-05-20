# Task Contract

## Task

- 이름: free-market-backfill-throttle
- 요청: Alpha Vantage 무료 제한에 맞춘 throttled market price backfill job을 구현한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `market-price-batch-upsert`와 `market-price-universe-backfill`이 무료 provider 운영에 필요한 request budget과 call spacing을 지원하고, 하루 25회 무료 제한을 넘기지 않는 small watchlist smoke를 실행할 수 있다.

## Why

- Alpha Vantage adjusted endpoint는 premium이므로 무료 `TIME_SERIES_DAILY` fallback을 사용한다.
- 무료 key는 일일 호출 수와 burst 제한이 있으므로 연속 호출을 막아야 한다.
- 무제한 backfill은 비용 없이 운영한다는 프로젝트 조건과 맞지 않는다.

## Scope

- 포함:
  - batch/universe market price backfill throttle 옵션
  - request budget 초과 symbol skip 결과 기록
  - unit tests
  - small watchlist smoke
  - task handoff/review
- 제외:
  - 새로운 유료 provider 도입
  - DB schema 변경
  - split/dividend adjusted price 복원
  - scheduler actual activation
  - paper trading/real trading

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/market/backfill.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_price.py`
  - `tests/test_ingest_cli.py`
  - task docs
- 수정 금지 파일:
  - `db/migrations/`
  - provider API key values
  - broker/order flow

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price tests.test_ingest_cli tests.test_data_operations_cadence -v`
  - `STOCKANALYSIS_ALPHA_VANTAGE_PRICE_MODE=daily PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.ingest.cli market-price-batch-upsert --symbol AAPL --symbol MSFT --max-requests-per-run 1 --throttle-seconds 1 --outputsize compact`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-market-backfill-throttle`

## Completion Criteria

- [x] batch CLI accepts throttle and max request options.
- [x] request budget skip is explicit and non-secret.
- [x] tests prove throttle sleeps between provider-backed calls.
- [x] real small watchlist smoke runs without exceeding free budget.

## Risks

- Alpha Vantage free daily limit is account-side and can already be exhausted before a run starts.
- Free `TIME_SERIES_DAILY` remains unadjusted; downstream quality must keep this caveat visible.
