# Review

## Review Notes

- `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`가 Docker Postgres에서 prerequisite pipeline을 만들고 scheduler wrapper run mode를 실행한다.
- wrapper stdout JSON artifact, stderr log artifact, BABA open remediation ticket, latest `portfolio_remediation_daily_automation` run status `succeeded`를 확인한다.
- 이 작업은 실제 host scheduler install, production DB smoke, `launchctl bootstrap`을 수행하지 않는다.

## Verification Evidence

- `bash -n scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`: 통과
- `bash -n scripts/run_portfolio_remediation_daily_scheduler.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`: sandbox Docker socket permission denied 확인 후 sandbox 밖 재실행 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-runtime-smoke`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
