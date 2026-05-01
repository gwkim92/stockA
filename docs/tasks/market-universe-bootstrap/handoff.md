# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: market-universe-bootstrap
- 담당: Codex
- 날짜: 2026-04-23

## Current Status

- 완료:
  - task 범위와 검증 계획을 문서로 고정했다.
  - source adapter, runner, CLI, tests, verify, 운영 문서를 구현했다.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-23-market-universe-bootstrap.md`
  - `docs/market-universe-bootstrap.md`
  - `docs/tasks/market-universe-bootstrap/contract.md`
  - `docs/tasks/market-universe-bootstrap/plan.md`
  - `docs/tasks/market-universe-bootstrap/handoff.md`
  - `docs/tasks/market-universe-bootstrap/review.md`
  - `scripts/verify_market_universe_bootstrap.sh`
  - `src/stockanalysis/ingest/market/universe.py`
  - `tests/test_market_universe.py`
  - `tests/fixtures/sec_company_tickers_exchange_sample.json`
- 수정:
  - `AGENTS.md`
  - `README.md`
  - `docs/verification-plan.md`
  - `docs/tasks/market-price-batch-ingest/handoff.md`
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - thesis/recommendation tables

## Decisions

- 결정:
  - source는 SEC `company_tickers_exchange`를 사용한다.
  - supported exchange는 `Nasdaq`, `NYSE`만 우선 지원한다.
  - canonical upsert는 `ref.issuer`, `ref.instrument`까지만 다룬다.
- 이유:
  - 현재 seed exchange와 SEC exact company name matching을 가장 단순하게 재사용할 수 있기 때문이다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: 성공

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 85개 테스트 통과

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
- 관찰한 결과: 성공

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
- 관찰한 결과: 성공. Docker Postgres에서 `ref.issuer=2`, `ref.instrument=2`, `AAPL -> XNAS=1`, `BABA -> XNYS=1`, `BAESY=0`, latest `market_universe_bootstrap` run status `succeeded`를 확인했다.

- 명령: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-universe-bootstrap`
- 관찰한 결과: 성공

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력 없음

## Still Unverified

- 항목: live SEC `company_tickers_exchange` smoke
- 왜 중요한가: 현재 검증은 fixture 기준이라 실제 live payload 다운로드와 헤더 정책은 별도 확인이 필요하다.

- 항목: CIK identity persistence
- 왜 중요한가: 현재 canonical ref tables에 CIK가 없어 future exact issuer identity enrichment이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `market-price-universe-backfill`을 만들어 canonical universe에서 symbol list를 읽어 batch price ingest를 자동화한다.

## Risks

- 위험:
  - issuer CIK를 canonical ref tables에 아직 저장하지 않는다.
  - `OTC`, `CBOE`는 skip된다.
  - ETF/common stock 세부 타입을 아직 구분하지 않는다.
- 대응:
  - 현재는 exact company name + symbol bootstrap만 먼저 열고 richer identity mapping은 후속 task로 분리한다.

## Useful Context

- 파일:
  - `db/seeds/0001_reference_seed.sql`
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/market/universe.py`
  - `scripts/verify_market_universe_bootstrap.sh`
- 다시 찾기 싫은 배경지식:
  - SEC `company_tickers_exchange.json` fields는 `[cik, name, ticker, exchange]` 순서다.
  - 현재 sample live exchange 값은 `Nasdaq`, `NYSE`, `OTC`, `CBOE`, `None` 정도다.
