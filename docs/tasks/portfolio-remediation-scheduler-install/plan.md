# Implementation Plan

- `scripts/install_portfolio_remediation_scheduler.sh`를 추가한다.
- script default는 `--dry-run`으로 두고, `--install`일 때만 host install path를 사용한다.
- launchd plist는 wrapper를 `/bin/bash <repo>/scripts/run_portfolio_remediation_daily_scheduler.sh`로 호출하게 렌더링한다.
- temp env file 기반 `scripts/verify_portfolio_remediation_scheduler_install.sh`를 추가한다.
- 기존 scheduler contract/activation verify가 repo-local installer 존재를 허용하도록 갱신한다.
- `docs/portfolio-remediation-scheduler-install.md`, README, verification plan을 갱신한다.
- task handoff/review에 verification evidence를 남긴다.
