# Implementation Plan

- `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`를 추가한다.
- runner는 `--env-file`을 source하고 기존 scheduler wrapper run mode를 실행한다.
- runner는 JSON artifact, stderr artifact, BABA open ticket, latest DB run status를 검증한다.
- `scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`를 추가한다.
- 검증 script는 Docker Postgres prerequisite pipeline을 만든 뒤 temp env file로 새 runner를 실행한다.
- `docs/portfolio-remediation-scheduler-runtime-env-smoke.md`, README, verification plan을 갱신한다.
- task handoff/review에 verification evidence를 남긴다.
