# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: portfolio-review-bootstrap
- 담당: Codex
- 날짜: 2026-04-26

## Current Status

- 완료:
  - position snapshot을 thesis review와 recommendation evidence에 연결해 portfolio review rows로 저장한다.
  - `portfolio.review`/`portfolio.review_item` migration, runner, CLI, tests, Docker verify, 운영 문서를 추가했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `db/migrations/0009_portfolio_review.sql`
  - `docs/plans/2026-04-26-portfolio-review-bootstrap.md`
  - `docs/portfolio-review-bootstrap.md`
  - `docs/tasks/portfolio-review-bootstrap/contract.md`
  - `docs/tasks/portfolio-review-bootstrap/plan.md`
  - `docs/tasks/portfolio-review-bootstrap/handoff.md`
  - `docs/tasks/portfolio-review-bootstrap/review.md`
  - `scripts/verify_portfolio_review_bootstrap.sh`
  - `src/stockanalysis/signal/portfolio_review.py`
  - `tests/test_portfolio_review_bootstrap.py`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`

## Decisions

- 결정:
  - 기존 `portfolio.position_snapshot`을 입력으로 사용한다.
  - portfolio-level header는 `portfolio.review`, position별 판단은 `portfolio.review_item`에 저장한다.
  - action은 thesis review action을 우선하고, keep 상태에서만 current weight와 recommended weight gap을 본다.
  - trade/order 생성은 하지 않는다.
- 이유:
  - 보유 검토 이력을 만들되, 실거래 자동화 위험을 도입하지 않기 위해서다.

## Verification Already Run

- `python3 -m compileall src tests` passed.
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_review_bootstrap tests.test_ingest_cli -v` passed: 35 tests.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed: 164 tests.
- `bash -n scripts/verify_portfolio_review_bootstrap.sh` passed.
- `bash scripts/verify_portfolio_review_bootstrap.sh` passed with Docker Postgres.

## Still Unverified

- 항목: live portfolio adapter
- 왜 중요한가: 현재는 paper portfolio와 fixture position snapshot insert로 검증한다.
- 항목: 다종목 portfolio weight distribution
- 왜 중요한가: AAPL 1건으로는 sector/theme concentration이나 cash/position 합산 edge case를 충분히 검증할 수 없다.
- 항목: order/trade execution
- 왜 중요한가: 이번 작업은 review 기록만 만들고 실거래 자동화는 의도적으로 제외했다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `position-snapshot-ingest`로 paper/live portfolio snapshot 적재기를 만들거나, `performance-outcome-bootstrap`으로 추천과 thesis의 사후 성과를 측정한다.

## Risks

- 위험:
  - fixture paper portfolio 1건만 검증하면 실제 다종목 portfolio의 weight 분포 문제는 드러나지 않는다.
  - current action rule은 deterministic bootstrap이라 optimizer가 아니다.
  - broker-specific `position_snapshot` adapter는 아직 없다.
- 대응:
  - live portfolio adapter와 portfolio weight distribution report를 후속 task로 분리한다.
  - 이번 단계는 audit 가능한 보유 검토 row 저장에 집중한다.

## Useful Context

- 파일:
  - `src/stockanalysis/signal/thesis_review.py`
  - `src/stockanalysis/signal/recommendation.py`
  - `tests/test_thesis_review_bootstrap.py`
  - `scripts/verify_thesis_review_bootstrap.sh`
- 다시 찾기 싫은 배경지식:
  - current fixture chain에서 AAPL thesis review는 action `watch`, health score `0.3610`이다.
  - portfolio review는 이 action을 보유 관점의 `monitor`로 변환한다.
  - Docker verify는 paper portfolio `Long Term Paper`와 AAPL position snapshot 1건을 삽입한 뒤 review header 1건, review item 1건을 확인한다.
