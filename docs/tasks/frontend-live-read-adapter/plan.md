# Implementation Plan

- `src/stockanalysis/frontend/live_adapter.py`를 추가한다.
- live adapter는 exact frontend API path를 parse하고, 지원 endpoint만 canonical read report 함수로 위임한다.
- remediation tickets는 `stockanalysis.signal.portfolio_remediation_ticket.load_portfolio_remediation_ticket_report`를 frontend DTO로 변환한다.
- portfolio coverage는 `stockanalysis.performance.coverage.load_portfolio_outcome_coverage_report`를 frontend DTO로 변환한다.
- `src/stockanalysis/frontend/api_adapter.py`에 `get --source fixture|live|auto`를 추가한다.
- 기존 report payload에 frontend 변환에 필요한 `instrument_id`를 additive field로 포함한다.
- `tests/test_frontend_live_adapter.py`와 adapter CLI regression test를 추가한다.
- `scripts/verify_frontend_live_read_adapter.sh`를 추가한다.
- frontend adapter/contract/architecture/verification docs를 갱신한다.
- task handoff/review에 verification evidence와 남은 위험을 기록한다.
