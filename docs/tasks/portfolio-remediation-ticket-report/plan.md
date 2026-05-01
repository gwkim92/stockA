# Plan

- `src/stockanalysis/signal/portfolio_remediation_ticket.py`에 read-only ticket report lookup을 추가한다.
- report는 `portfolio.remediation_ticket`, `portfolio.review`, `portfolio.portfolio`, `ref.instrument`, `ops.pipeline_run`을 join한다.
- CLI `portfolio-remediation-ticket-report`를 추가한다.
- unit test로 SQL filter, limit validation, CLI dispatch를 검증한다.
- Docker verify로 ticket bootstrap 후 BABA open ticket report를 확인한다.
- README, ticket bootstrap docs, verification plan, task handoff/review를 갱신한다.
