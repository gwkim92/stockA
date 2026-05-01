# Plan

- 실제 migration에 `performance.recommendation_outcome`과 `performance.thesis_outcome`을 추가한다.
- `src/stockanalysis/performance/outcome.py`에 candidate lookup, outcome 계산, upsert, runner를 만든다.
- entry price는 recommendation batch `as_of_date` 이하의 최신 adjusted close로 둔다.
- exit price는 `measurement_end_date` 이하의 최신 adjusted close로 둔다.
- benchmark instrument와 price가 있으면 benchmark return과 alpha를 계산하고, 없으면 null로 둔다.
- CLI `performance-outcome-bootstrap`을 추가한다.
- unit test로 lookup SQL, return 계산, SQL rendering, runner summary, CLI dispatch를 고정한다.
- Docker verify로 AAPL recommendation/thesis outcome 1건과 absolute return `0.010000`을 확인한다.
- 운영 문서와 verification plan, handoff/review를 갱신한다.
