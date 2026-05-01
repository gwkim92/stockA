# Plan

- `db/migrations/0012_portfolio_remediation_ticket.sql`에 persistent ticket table을 추가한다.
- `src/stockanalysis/signal/portfolio_remediation_ticket.py`에 ticket bootstrap SQL/runner를 추가한다.
- CLI `portfolio-remediation-ticket-bootstrap`을 추가한다.
- unit test로 SQL shape, limit validation, CLI dispatch를 검증한다.
- Docker verify로 coverage-gated review 후 BABA thesis remediation ticket 생성과 idempotency를 확인한다.
- README, schema docs, queue docs, verification plan, task handoff/review를 갱신한다.
