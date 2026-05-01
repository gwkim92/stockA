# Review

## Scope Reviewed

- `src/stockanalysis/ingest/portfolio/position.py`
- `src/stockanalysis/ingest/cli.py`
- `tests/test_position_snapshot_ingest.py`
- `scripts/verify_position_snapshot_ingest.sh`
- `scripts/verify_portfolio_review_bootstrap.sh`
- `docs/position-snapshot-ingest.md`
- `docs/tasks/position-snapshot-ingest/`

## Findings

- Blocking finding 없음.
- CSV loader는 `symbol`, `quantity`, `market_price`, `market_value`를 필수 컬럼으로 검증한다.
- upsert runner는 portfolio row를 생성/갱신하고 canonical instrument symbol로 `portfolio.position_snapshot`을 저장한다.
- CSV에 `linked_thesis_id`가 없으면 latest active thesis를 lateral lookup으로 연결한다.
- 기존 portfolio review Docker verify는 수동 SQL 삽입 대신 새 `portfolio-position-snapshot-upsert` CLI를 사용한다.

## Verification

- `python3 -m compileall src tests` passed.
- `PYTHONPATH=src python3 -m unittest tests.test_position_snapshot_ingest tests.test_ingest_cli -v` passed: 34 tests.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed: 171 tests.
- `bash -n scripts/verify_position_snapshot_ingest.sh` passed.
- `bash -n scripts/verify_portfolio_review_bootstrap.sh` passed.
- `bash scripts/verify_position_snapshot_ingest.sh` passed with Docker Postgres.
- `bash scripts/verify_portfolio_review_bootstrap.sh` passed with Docker Postgres.

## Residual Risk

- broker-specific export adapter는 아직 없다.
- cash position row는 아직 별도로 적재하지 않는다.
- 복수 active thesis selection은 단순 latest thesis 기준이다.
