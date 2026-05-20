# Task Contract

## Task

- 이름: local-market-universe-live-bootstrap
- 요청: 로컬 live MVP에서 가격 수집이 실패한 원인인 canonical instrument 부재를 해결하기 위해 SEC 상장 유니버스를 실제 Postgres에 부트스트랩한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 로컬 Postgres `ref.instrument`에 `MSFT`와 `NVDA`가 canonical listed security로 등록되어 다음 무료 market price backfill이 instrument lookup에서 막히지 않는다.

## Why

- 2026-05-17 positive-budget Alpha Vantage run은 provider 호출 1회를 사용했지만 `MSFT` canonical instrument가 없어 가격 row를 적재하지 못했다.
- 새 수동 fixture를 넣는 방식은 프로젝트 방향과 맞지 않는다. 이미 구현된 SEC `company_tickers_exchange` universe bootstrap을 실제 data collector 경계로 사용해야 한다.

## Scope

- SEC `company_tickers_exchange` live request가 CIK 없이 동작하도록 SEC source request builder를 수정한다.
- 기존 `market-universe-bootstrap` CLI를 사용해 로컬 live Postgres에 Nasdaq/NYSE universe를 upsert한다.
- data operations artifact runner가 universe bootstrap을 정식 job으로 실행할 수 있도록 `market-universe-weekly` cadence를 등록한다.
- `MSFT`, `NVDA`, `AAPL` canonical instrument lookup을 검증한다.
- Alpha Vantage 가격 provider 호출은 이번 작업에서 수행하지 않는다.

## Boundaries

- `.env`와 repo-outside runtime env의 secret 값은 문서나 로그에 남기지 않는다.
- 실제 host scheduler activation, `launchctl bootstrap`, LaunchAgents 쓰기는 하지 않는다.
- DB schema, scoring, benchmark, evaluation split, broker/order flow는 바꾸지 않는다.
- 추가 Alpha Vantage quota 소비는 명시 승인 전까지 하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/operations/cadence.py`
  - `tests/test_ingest_sources.py`
  - `tests/test_market_price.py`
  - `tests/test_data_operations_cadence.py`
  - `docs/tasks/local-market-universe-live-bootstrap/`
  - `docs/plans/2026-05-17-local-market-universe-live-bootstrap.md`
  - `docs/tasks/local-live-mvp-runtime/handoff.md`
- 수정 금지 파일:
  - `.env`
  - `/private/tmp/stockanalysis-runtime/*.env` secret values
  - `db/migrations/`
  - backend scoring/schema/evaluation logic
  - broker/order flow
  - host scheduler activation files

## Verification Commands

- 검증에 사용할 명령:
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_sources tests.test_market_universe`
  - `scripts/smoke_data_operations_runtime.sh --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env --job-id market-universe-weekly --timeout-seconds 240 -- /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.ingest.cli market-universe-bootstrap --exchange Nasdaq --exchange NYSE`
  - local Postgres lookup for `MSFT`, `NVDA`, `AAPL`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-market-universe-live-bootstrap`
  - `git diff --check`

## Done Criteria

- [x] SEC `company_tickers_exchange` request builder가 CIK 없이 URL을 만든다.
- [x] `market-universe-weekly` data operations cadence가 등록된다.
- [x] price lookup이 psql 실행 실패를 instrument 부재로 오인하지 않는다.
- [x] focused unit tests가 통과한다.
- [x] live SEC universe bootstrap이 로컬 Postgres에 성공 상태로 기록된다.
- [x] `MSFT`, `NVDA`, `AAPL` lookup이 canonical instrument를 반환한다.
- [x] task handoff에 남은 blocker와 다음 작업을 기록한다.
