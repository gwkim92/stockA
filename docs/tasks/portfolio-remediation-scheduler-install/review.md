# Review

## Review Notes

- launchd install artifact를 추가했다.
- install script 기본값은 `--dry-run`이다.
- 검증은 temp artifact root에 rendered plist를 만들고, host `~/Library/LaunchAgents`에는 쓰지 않는다.
- rendered plist는 wrapper, env file, working directory, stdout/stderr log path, Monday-Friday 18:30 schedule을 포함한다.
- actual `launchctl bootstrap`은 자동 실행하지 않는다.
- market holiday skip과 external alert destination은 아직 없다.

## Verification Evidence

- `bash -n scripts/install_portfolio_remediation_scheduler.sh`: 통과
- `bash -n scripts/verify_portfolio_remediation_scheduler_install.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_install.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_contract.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_activation.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-install`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: placeholder 없음
