# Implementation Plan

- `scripts/run_portfolio_remediation_daily_scheduler.sh`에 run date와 skip dates parsing을 추가한다.
- skip date hit면 daily runner를 호출하지 않고 skip JSON/stderr artifact를 남긴다.
- preflight JSON에 `run_date`, `skip_dates`, `would_skip`을 추가한다.
- `scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`를 추가한다.
- activation verify script를 새 preflight payload field까지 검증하도록 갱신한다.
- `docs/portfolio-remediation-scheduler-holiday-skip.md`, README, scheduler docs, verification plan을 갱신한다.
- task handoff/review에 verification evidence를 남긴다.
