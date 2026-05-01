# Implementation Plan

- `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`를 추가한다.
- 기존 daily automation integration path와 동일한 prerequisite pipeline을 Docker Postgres에 만든다.
- 마지막 daily run은 `scripts/run_portfolio_remediation_daily_scheduler.sh` run mode로 실행한다.
- wrapper output artifact와 stderr artifact를 검증한다.
- JSON payload와 DB latest pipeline run status를 검증한다.
- `docs/portfolio-remediation-scheduler-runtime-smoke.md`, README, verification plan을 갱신한다.
- task handoff/review에 verification evidence를 남긴다.
