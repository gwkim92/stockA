# Portfolio Remediation Scheduler Runtime Smoke

이 문서는 `scripts/run_portfolio_remediation_daily_scheduler.sh` run mode가 실제 Postgres runtime에서 daily remediation runner를 호출하고 artifact와 DB provenance를 남기는지 검증하는 smoke test를 정의한다.

## Current Status

- `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`를 추가했다.
- 검증은 Docker Postgres에서 수행한다.
- wrapper run mode를 직접 실행해 stdout JSON artifact와 stderr log artifact를 확인한다.
- latest `portfolio_remediation_daily_automation` pipeline run status가 `succeeded`인지 확인한다.
- actual host launchd install과 production DB smoke는 아직 실행하지 않는다.
- env file 기반 runtime DB smoke gate는 `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`로 분리했다.

## What It Proves

검증은 아래 흐름을 end-to-end로 확인한다.

- Docker Postgres container start
- migrations and seeds apply
- universe, price, event, theme, cycle, recommendation, thesis, outcome, position prerequisite pipeline execution
- scheduler wrapper run mode execution
- JSON artifact path creation under temp scheduler artifact root
- stderr log artifact creation
- daily remediation JSON payload validation
- BABA open remediation ticket validation
- DB latest daily automation run status validation

## Command

```bash
bash scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh
```

검증 script는 `python3 -m compileall`, 전체 `unittest`, wrapper syntax check를 먼저 수행한 뒤 Docker Postgres smoke를 실행한다.

## Expected Payload

wrapper가 생성하는 JSON artifact는 아래 핵심 값을 포함해야 한다.

- `report_name`: `portfolio_remediation_daily_automation`
- `portfolio_name`: `Long Term Paper`
- `as_of_date`: `2024-11-01`
- `coverage_measurement_end_date`: `2024-12-02`
- `steps`: `portfolio_review_bootstrap`, `portfolio_remediation_ticket_bootstrap`, `portfolio_remediation_ticket_report`
- `review.review_item_count`: `2`
- `ticket_report.ticket_count`: `1`
- open ticket: `BABA`, `thesis_remediation`, `thesis_or_position_link_review`

## Boundaries

- production DB에 연결하지 않는다.
- host `~/Library/LaunchAgents`에 쓰지 않는다.
- `launchctl bootstrap`을 실행하지 않는다.
- external alert destination은 아직 없다.
- market holiday skip은 아직 weekday schedule contract 수준이다.
- ticket auto-resolve, remediation auto-run, trade automation은 없다.

## Next Steps

1. repo 밖에 intended runtime env file을 만들고 `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`를 실제 의도한 runtime DB에서 1회 실행한다.
2. alert destination을 정한다.
3. market holiday skip rule을 확정한다.
4. 명시 승인 후 `scripts/install_portfolio_remediation_scheduler.sh --install`과 `launchctl bootstrap`을 실행한다.
