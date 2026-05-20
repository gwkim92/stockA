# Local Market Universe Live Bootstrap Plan

## Steps

1. SEC source request builder의 CIK 없는 dataset 처리 버그를 수정한다.
2. 해당 regression unit test를 추가한다.
3. artifact runner가 universe bootstrap을 정식 job으로 받을 수 있도록 `market-universe-weekly` cadence를 등록한다.
4. data operations artifact runner를 통해 live SEC `market-universe-bootstrap`을 로컬 Postgres에 실행한다.
5. `MSFT`, `NVDA`, `AAPL`이 `ref.instrument`에서 resolve되는지 확인한다.
6. handoff/review에 결과와 다음 가격 backfill 조건을 남긴다.

## Non-Goals

- Alpha Vantage 추가 호출
- schema 변경
- 추천/스코어링 변경
- scheduler 설치 또는 host activation
- paper trading 또는 실거래 구현
