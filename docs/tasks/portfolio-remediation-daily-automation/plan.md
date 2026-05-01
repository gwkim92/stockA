# Implementation Plan

- `docs/tasks/portfolio-remediation-daily-automation/loop_contract.md`에 반복 실행 정책과 boundary를 남긴다.
- `src/stockanalysis/signal/portfolio_remediation_daily.py`에 daily orchestration runner를 추가한다.
- `tests/test_portfolio_remediation_daily.py`에서 성공, invalid limit, 실패 provenance를 검증한다.
- `src/stockanalysis/ingest/cli.py`에 `portfolio-remediation-daily-run` command와 handler를 추가한다.
- `tests/test_ingest_cli.py`에 CLI argument forwarding test를 추가한다.
- `scripts/verify_portfolio_remediation_daily_automation.sh`로 Docker Postgres integration path를 검증한다.
- `docs/portfolio-remediation-daily-automation.md`, README, verification plan, handoff/review를 갱신한다.
