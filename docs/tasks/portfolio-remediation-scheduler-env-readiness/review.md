# Review

## Review Notes

- `scripts/render_portfolio_remediation_scheduler_env_template.sh`가 repo 밖 path에 scheduler env template을 생성한다.
- `scripts/check_portfolio_remediation_scheduler_runtime_env.sh`가 trusted env file을 source해 placeholder, required env, date format, ticket limit, artifact root, psql argv0, wrapper preflight를 검증한다.
- `scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`가 repo 내부 output 거부, unedited template failure, valid env success, install dry-run compatibility를 확인한다.
- 이 작업은 actual DB smoke, host scheduler install, `launchctl bootstrap`을 수행하지 않는다.

## Verification Evidence

- `bash -n scripts/render_portfolio_remediation_scheduler_env_template.sh`: 통과
- `bash -n scripts/check_portfolio_remediation_scheduler_runtime_env.sh`: 통과
- `bash -n scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-env-readiness`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
