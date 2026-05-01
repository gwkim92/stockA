# Plan

- `src/stockanalysis/signal/portfolio_review_report.py`에 read-only run history lookup을 추가한다.
- report는 `portfolio.review`, `portfolio.review_item`, `portfolio.portfolio`, `ref.instrument`, `ops.pipeline_run`을 조합한다.
- CLI `portfolio-review-run-history`를 추가한다.
- unit test로 SQL filter, limit validation, CLI dispatch를 검증한다.
- Docker verify로 coverage-gated review 후 AAPL monitor와 BABA needs thesis review를 report에서 확인한다.
- README, portfolio review docs, verification plan, task handoff/review를 갱신한다.
