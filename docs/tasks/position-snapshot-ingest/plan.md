# Plan

- 새 schema 없이 기존 `portfolio.portfolio`와 `portfolio.position_snapshot`을 사용한다.
- `src/stockanalysis/ingest/portfolio/position.py`에 CSV loader, SQL renderer, upsert runner를 만든다.
- CSV 필수 컬럼은 `symbol`, `quantity`, `market_price`, `market_value`로 둔다.
- CSV 선택 컬럼은 `cost_basis`, `weight`, `unrealized_pnl`, `linked_thesis_id`로 둔다.
- CLI `portfolio-position-snapshot-upsert`를 추가한다.
- unit test로 CSV parsing, SQL rendering, runner summary, CLI dispatch를 고정한다.
- Docker verify로 full chain 이후 AAPL position snapshot이 active thesis와 연결되는지 확인한다.
- 기존 `portfolio-review-bootstrap` verify의 수동 SQL position 삽입을 새 CLI command로 대체한다.
- 운영 문서와 verification plan, handoff/review를 갱신한다.
