# Review

## Review Notes

- scheduler runtime wrapper를 추가했지만 실제 scheduler install은 수행하지 않았다.
- wrapper `--preflight-only`는 DB를 호출하지 않고 required env, artifact root, `python3` 존재만 확인한다.
- run mode는 `portfolio-remediation-daily-run`을 호출하고 stdout JSON/stderr log를 artifact로 저장한다.
- alert destination과 market holiday skip rule은 아직 없다.
- 실거래, ticket auto-resolve, remediation auto-run은 추가하지 않았다.

## Verification Evidence

- `bash -n scripts/run_portfolio_remediation_daily_scheduler.sh`: 통과
- `bash -n scripts/verify_portfolio_remediation_scheduler_activation.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_activation.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-activation`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: placeholder 없음
