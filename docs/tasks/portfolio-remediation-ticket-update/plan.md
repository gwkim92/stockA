# Plan

- `src/stockanalysis/signal/portfolio_remediation_ticket.py`에 ticket lifecycle update runner를 추가한다.
- update는 target portfolio와 ticket id가 모두 맞을 때만 status를 변경한다.
- CLI `portfolio-remediation-ticket-update`를 추가한다.
- unit test로 status validation, SQL shape, CLI dispatch를 검증한다.
- Docker verify로 BABA open ticket을 resolved로 바꾸고 report에서 확인한다.
- README, ticket report docs, verification plan, task handoff/review를 갱신한다.
