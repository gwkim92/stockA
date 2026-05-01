# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: position-snapshot-ingest
- 담당: Codex
- 날짜: 2026-04-26

## Current Status

- 완료:
  - CSV position snapshot을 canonical portfolio tables에 업서트한다.
  - `portfolio-position-snapshot-upsert` CLI, CSV loader, upsert SQL, tests, Docker verify, 운영 문서를 추가했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-26-position-snapshot-ingest.md`
  - `docs/position-snapshot-ingest.md`
  - `docs/tasks/position-snapshot-ingest/contract.md`
  - `docs/tasks/position-snapshot-ingest/plan.md`
  - `docs/tasks/position-snapshot-ingest/handoff.md`
  - `docs/tasks/position-snapshot-ingest/review.md`
  - `scripts/verify_position_snapshot_ingest.sh`
  - `src/stockanalysis/ingest/portfolio/__init__.py`
  - `src/stockanalysis/ingest/portfolio/position.py`
  - `tests/fixtures/portfolio_positions_long_term_paper.csv`
  - `tests/test_position_snapshot_ingest.py`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/portfolio-review-bootstrap.md`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_review_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`

## Decisions

- 결정:
  - broker adapter 전 단계로 CSV upsert를 먼저 만든다.
  - 새 schema 없이 기존 position snapshot table을 사용한다.
  - CSV에 `linked_thesis_id`가 없으면 latest active thesis를 자동 연결한다.
  - 실거래, 주문, broker credentials는 범위 밖으로 둔다.
- 이유:
  - 수동 SQL 삽입을 제거하면서도 live 계좌 연동 위험을 도입하지 않기 위해서다.

## Verification Already Run

- `python3 -m compileall src tests` passed.
- `PYTHONPATH=src python3 -m unittest tests.test_position_snapshot_ingest tests.test_ingest_cli -v` passed: 34 tests.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed: 171 tests.
- `bash -n scripts/verify_position_snapshot_ingest.sh` passed.
- `bash -n scripts/verify_portfolio_review_bootstrap.sh` passed.
- `bash scripts/verify_position_snapshot_ingest.sh` passed with Docker Postgres.
- `bash scripts/verify_portfolio_review_bootstrap.sh` passed with Docker Postgres.

## Still Unverified

- 항목: broker-specific export adapter
- 왜 중요한가: 현재는 표준 CSV schema만 지원한다.
- 항목: cash position row
- 왜 중요한가: 현재 cash는 portfolio review의 cash weight로 계산하며 별도 position row로 저장하지 않는다.
- 항목: 복수 active thesis 선택 정책
- 왜 중요한가: 현재는 latest active thesis를 단순 선택한다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `performance-outcome-bootstrap`으로 추천/thesis/portfolio review 이후의 사후 성과를 측정하거나, broker-specific position adapter를 추가한다.

## Risks

- 위험:
  - CSV schema는 broker별 export 형식과 다를 수 있다.
  - cash position은 아직 별도 row로 다루지 않는다.
  - latest active thesis 자동 연결은 복수 thesis 환경에서 단순하다.
- 대응:
  - broker-specific adapter는 후속 task로 분리한다.
  - cash는 portfolio review header의 cash_weight로 우선 계산한다.
  - thesis selection policy는 live 다종목 운영 전에 별도 확장한다.

## Useful Context

- 파일:
  - `src/stockanalysis/signal/portfolio_review.py`
  - `scripts/verify_portfolio_review_bootstrap.sh`
  - `db/migrations/0002_priority_1_tables.sql`
- 다시 찾기 싫은 배경지식:
  - `portfolio.position_snapshot` primary key는 `(portfolio_id, instrument_id, snapshot_date)`다.
  - portfolio review는 `position_snapshot.linked_thesis_id` 또는 recommendation의 `thesis_id`를 사용한다.
  - 기존 portfolio review Docker verify는 수동 SQL 삽입 대신 `portfolio-position-snapshot-upsert`를 사용하도록 변경했다.
