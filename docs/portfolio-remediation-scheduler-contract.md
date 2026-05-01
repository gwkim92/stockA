# Portfolio Remediation Scheduler Contract

이 문서는 `portfolio-remediation-daily-run`을 실제 반복 실행으로 전환하기 전 필요한 scheduler contract를 정의한다.

## Current Status

- scheduler-ready contract만 정의한다.
- 실제 OS cron, launchd, hosted automation, app automation은 활성화하지 않았다.
- secrets, deployment config, broker/trading integration은 변경하지 않았다.

## Target Runner

반복 실행 대상은 이미 검증된 daily runner다.

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

`STOCKANALYSIS_PSQL_COMMAND`는 scheduler runtime에서 명시적으로 주입되어야 한다. 이 문서는 credential 주입 방식을 결정하지 않는다.

## Proposed Cadence

- timezone: `America/New_York`
- cadence: US market close 이후 1회 daily
- candidate time: 18:30 New York time
- 이유: 장중 noise를 피하고 daily price, position, outcome data가 준비된 뒤 review를 수행하기 위해서다.

Market holiday skip은 현재 explicit `PORTFOLIO_REMEDIATION_SKIP_DATES` 방식으로 지원한다. external holiday calendar 자동 수집은 아직 없으므로 운영자가 repo 밖 env file에 skip dates를 최신 상태로 관리해야 한다.

## Artifact Policy

반복 실행은 결과를 DB에만 남기면 운영자가 실패 원인을 추적하기 어렵다. scheduler activation 시 아래 artifact를 남긴다.

- stdout JSON: `artifacts/portfolio-remediation-scheduler/YYYY-MM-DD-portfolio-remediation-daily.json`
- stderr log: `artifacts/portfolio-remediation-scheduler/YYYY-MM-DD-portfolio-remediation-daily.stderr.log`
- retention before production: 90 days
- production retention: object storage 또는 log backend 결정 전까지 미정

Artifact root는 scheduler runtime user가 쓸 수 있어야 한다.

## Alert Policy

activation 전에는 alert destination을 결정해야 한다.

필수 alert condition:

- command exit code non-zero
- stdout JSON parse failure
- `report_name`이 `portfolio_remediation_daily_automation`이 아님
- top-level `run_id` 없음
- `ticket_report.ticket_count`가 threshold 초과
- same portfolio에서 이전 성공 이후 연속 실패

destination 후보:

- Slack webhook
- email
- GitHub issue
- dashboard alert

이 작업에서는 destination을 설정하지 않는다.

## Retry Policy

activation 전 기본값:

- automatic retry: disabled

activation 시 제안값:

- max retry count: 1
- retry delay: 30 minutes
- retry 금지 조건:
  - missing credential
  - invalid config
  - JSON parse failure but DB run was created
  - prerequisite data missing

재시도는 idempotent runner 위주로만 허용한다. 생성된 review/ticket row가 있으면 artifact와 `ops.pipeline_run`을 먼저 확인한다.

## Rollback Policy

rollback은 scheduler job을 비활성화하는 것이다.

- DB rows는 자동 삭제하지 않는다.
- 잘못 생성된 review/ticket row는 `ops.pipeline_run` provenance로 추적한다.
- ticket status는 scheduler가 자동으로 `resolved` 또는 `ignored`로 바꾸지 않는다.
- 실거래 주문/체결은 이 loop에 존재하지 않는다.

## Activation Gate

실제 scheduler를 켜려면 아래를 모두 충족해야 한다.

- `bash scripts/verify_portfolio_remediation_daily_automation.sh` 통과
- `bash scripts/verify_portfolio_remediation_scheduler_contract.sh` 통과
- artifact root writable 확인
- alert destination smoke test 통과
- `STOCKANALYSIS_PSQL_COMMAND` runtime 주입 방식 확정
- market holiday skip dates 설정 또는 deliberate empty 설정 기록
- 사용자 승인

## Boundaries

- scheduler activation은 이번 작업 범위 밖이다.
- DB schema를 변경하지 않는다.
- LLM 호출을 추가하지 않는다.
- remediation을 자동 실행하지 않는다.
- ticket lifecycle status를 자동 변경하지 않는다.
- 실거래 자동화와 무관하다.
- recommendation, thesis, review, attribution, performance outcome 산식을 변경하지 않는다.

## Next Steps

1. `scripts/run_portfolio_remediation_daily_scheduler.sh --preflight-only`로 runtime env와 artifact root를 확인한다.
2. alert destination을 결정한다.
3. `PORTFOLIO_REMEDIATION_SKIP_DATES` 운영 방식을 확정한다.
4. run mode를 intended runtime DB에서 smoke test한다.
5. `docs/portfolio-remediation-scheduler-install.md`의 dry-run install artifact를 확인한다.
6. 별도 승인 후 실제 install mode와 `launchctl bootstrap`을 실행한다.
