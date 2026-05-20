# Local Market Universe Live Bootstrap

## Decision

- 로컬 live MVP의 다음 blocker는 가격 수집기가 아니라 canonical market universe 부재다.
- `MSFT/NVDA`를 수동으로 넣지 않고 기존 SEC `company_tickers_exchange` data collector를 사용해 `ref.issuer/ref.instrument`를 채운다.
- Alpha Vantage quota는 이미 2026-05-17 1회를 소비했으므로 이번 작업에서는 추가 provider call을 하지 않는다.

## Work Plan

1. CIK가 필요 없는 SEC dataset 요청이 `params["cik"]`를 읽는 버그를 수정한다.
2. unit test로 `company_tickers_exchange`가 CIK 없이 request URL을 생성함을 고정한다.
3. `market-universe-weekly` cadence를 등록해 artifact runner가 universe bootstrap을 정식 job으로 다루게 한다.
4. repo-outside runtime env와 data operations artifact runner를 통해 live SEC universe bootstrap을 실행한다.
5. local Postgres에서 `MSFT`, `NVDA`, `AAPL` canonical instrument lookup을 검증한다.
6. task handoff/review에 결과와 다음 가격 backfill 조건을 남긴다.

## Out Of Scope

- DB schema 변경
- scoring/benchmark/evaluation 변경
- scheduler host activation
- 추가 Alpha Vantage 호출
- paper trading 또는 실거래
