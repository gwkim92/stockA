# Review

## Review Notes

- `scripts/run_portfolio_remediation_daily_scheduler.sh`가 `PORTFOLIO_REMEDIATION_RUN_DATE`, `PORTFOLIO_REMEDIATION_SKIP_DATES`, `PORTFOLIO_REMEDIATION_SKIP_REASON`을 지원한다.
- skip date hit에서는 DB runner를 호출하지 않고 JSON/stderr artifact를 생성한다.
- preflight output은 `run_date`, `skip_dates`, `would_skip`, `skip_reason`을 포함한다.
- 이 작업은 external holiday calendar sync, actual scheduler install, actual runtime DB smoke를 수행하지 않는다.

## Verification Evidence

- `bash -n scripts/run_portfolio_remediation_daily_scheduler.sh`: 통과
- `bash -n scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_activation.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-holiday-skip`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
