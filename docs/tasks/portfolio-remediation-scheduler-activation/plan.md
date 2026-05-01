# Implementation Plan

- `scripts/run_portfolio_remediation_daily_scheduler.sh`를 추가한다.
- wrapper에서 required env, artifact root, Python availability를 검증한다.
- wrapper `--preflight-only` mode를 구현한다.
- wrapper run mode에서 stdout JSON/stderr log artifact를 저장하고 JSON `report_name`을 검증한다.
- `scripts/verify_portfolio_remediation_scheduler_activation.sh`를 추가해 wrapper preflight와 no-install boundary를 검증한다.
- `docs/portfolio-remediation-scheduler-activation.md`, README, verification plan을 갱신한다.
- task handoff/review에 verification evidence를 남긴다.
