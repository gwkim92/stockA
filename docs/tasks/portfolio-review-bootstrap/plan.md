# Plan

- 실제 migration에 `portfolio.review`와 `portfolio.review_item`을 추가한다.
- 기존 `portfolio.portfolio`, `portfolio.position_snapshot`, `signal.recommendation`, `signal.investment_thesis`, `signal.thesis_review`를 입력으로 사용한다.
- `src/stockanalysis/signal/portfolio_review.py`에 candidate lookup, deterministic action rule, upsert, runner를 만든다.
- CLI `portfolio-review-bootstrap`을 추가한다.
- unit test로 lookup SQL, action rule, upsert SQL, runner summary, CLI dispatch를 고정한다.
- Docker verify로 AAPL paper position 1건이 review item `monitor`로 저장되는지 확인한다.
- 운영 문서와 verification plan, handoff/review를 갱신한다.
