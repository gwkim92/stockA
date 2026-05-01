# Scheduler Loop Contract

## Loop

- 이름: portfolio-remediation-scheduler-contract
- 대상 runner: `portfolio-remediation-daily-run`
- 목적: daily portfolio review와 remediation ticket backlog 생성을 반복 운영으로 전환하기 전 실행 정책을 고정한다.
- 실행 주체: 아직 없음. 실제 OS cron, hosted automation, app automation은 별도 승인 후 추가한다.

## Proposed Cadence

- timezone: `America/New_York`
- schedule: US market close 이후 1회 daily
- first candidate window: 18:30 New York time
- reason: 장중 noise를 줄이고 daily position/outcome data가 들어온 뒤 review를 수행한다.
- holiday handling: market holiday calendar integration 전까지 scheduler는 켜지 않는다. 수동 실행 또는 scheduler activation task에서 holiday skip rule을 추가한다.

## Required Inputs

- `STOCKANALYSIS_PSQL_COMMAND`
- `portfolio_name`
- `as_of_date`
- `strategy_name`
- `horizon_type`
- `universe_version`
- optional `coverage_measurement_end_date`
- `ticket_limit`
- `ticket_status`

## Command Template

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-daily-run \
  --portfolio-name "Long Term Paper" \
  --as-of-date "$AS_OF_DATE" \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version "$UNIVERSE_VERSION" \
  --coverage-measurement-end-date "$COVERAGE_MEASUREMENT_END_DATE" \
  --ticket-limit 50 \
  --ticket-status open
```

## Artifact Policy

- stdout JSON은 run id를 포함한 파일로 저장한다.
- stderr는 별도 log file로 저장한다.
- proposed local artifact root: `artifacts/portfolio-remediation-scheduler/`
- filename shape:
  - `YYYY-MM-DD-portfolio-remediation-daily.json`
  - `YYYY-MM-DD-portfolio-remediation-daily.stderr.log`
- retention before production: 90 days
- retention after production: 별도 storage policy 확정 전까지 미정

## Alert Policy

- alert condition:
  - command exit code non-zero
  - JSON parse failure
  - `report_name` is not `portfolio_remediation_daily_automation`
  - top-level run is missing
  - open ticket count exceeds agreed threshold
- alert destination:
  - not configured in this task
  - scheduler activation task must choose Slack, email, issue creation, or dashboard alert

## Retry Policy

- automatic retry before scheduler activation: none
- proposed activation policy:
  - max retry count: 1
  - retry delay: 30 minutes
  - no retry if failure is config/credential missing
  - no retry if previous attempt created review/ticket output but report parsing failed; inspect artifact first

## Rollback Policy

- scheduler activation rollback means disabling the scheduler job.
- DB rows created by `portfolio-remediation-daily-run` are not auto-deleted.
- incorrect review/ticket rows must be traced by `ops.pipeline_run` provenance before any manual cleanup.
- ticket status is never auto-resolved by the scheduler.

## Activation Gate

- `scripts/verify_portfolio_remediation_daily_automation.sh` passes.
- scheduler contract verify passes.
- artifact root exists and is writable.
- alert destination is configured and smoke-tested.
- secrets are available through approved runtime config.
- market holiday skip rule is explicitly accepted or deliberately deferred.
- user approves actual scheduler activation.
