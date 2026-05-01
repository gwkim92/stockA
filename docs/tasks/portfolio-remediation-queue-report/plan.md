# Plan

- `src/stockanalysis/signal/portfolio_remediation_queue.py`에 read-only queue lookup을 추가한다.
- queue는 `portfolio.review_item` action을 remediation type과 suggested runner로 매핑한다.
- CLI `portfolio-remediation-queue`를 추가한다.
- unit test로 SQL filter, limit validation, CLI dispatch를 검증한다.
- Docker verify로 coverage-gated review 후 BABA thesis remediation item을 확인한다.
- README, run history docs, verification plan, task handoff/review를 갱신한다.
