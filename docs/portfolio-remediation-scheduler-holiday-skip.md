# Portfolio Remediation Scheduler Holiday Skip

이 문서는 scheduler wrapper의 explicit skip date gate를 정의한다.

## Current Status

- `scripts/run_portfolio_remediation_daily_scheduler.sh`가 `PORTFOLIO_REMEDIATION_SKIP_DATES`를 지원한다.
- run date가 skip list에 포함되면 `portfolio-remediation-daily-run`을 호출하지 않는다.
- skip hit에서는 JSON artifact와 stderr log artifact를 생성하고 artifact path를 stdout으로 출력한다.
- external holiday calendar 자동 수집은 아직 없다.

## Environment

Optional values:

- `PORTFOLIO_REMEDIATION_RUN_DATE`: scheduler run date. 비워두면 `America/New_York` 기준 today를 사용한다.
- `PORTFOLIO_REMEDIATION_SKIP_DATES`: comma 또는 whitespace separated ISO date list.
- `PORTFOLIO_REMEDIATION_SKIP_REASON`: skip artifact에 남길 reason. default는 `configured_market_holiday`.

Example:

```bash
PORTFOLIO_REMEDIATION_RUN_DATE="2026-01-01"
PORTFOLIO_REMEDIATION_SKIP_DATES="2026-01-01,2026-01-19 2026-02-16"
PORTFOLIO_REMEDIATION_SKIP_REASON="nyse_holiday"
```

## Skip Artifact

skip hit에서는 stdout JSON path가 출력되고, 해당 JSON은 아래 핵심 값을 가진다.

```json
{
  "report_name": "portfolio_remediation_scheduler_skip",
  "status": "skipped",
  "skip_type": "configured_skip_date",
  "skip_reason": "nyse_holiday",
  "run_date": "2026-01-01",
  "skip_dates": ["2026-01-01", "2026-01-19"],
  "as_of_date": "2024-11-01"
}
```

## Verification

```bash
bash scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh
```

검증은 아래를 확인한다.

- wrapper syntax
- invalid DB command에서도 skip date hit는 성공
- JSON artifact 생성
- stderr log artifact 생성
- skip payload의 report/status/reason/run date/as-of date 검증
- preflight payload의 `run_date`, `skip_dates`, `would_skip`, `skip_reason` 검증

## Boundaries

- external holiday calendar를 자동 수집하지 않는다.
- skip artifact는 DB provenance를 만들지 않는다.
- actual host launchd install을 실행하지 않는다.
- actual runtime DB smoke를 실행하지 않는다.
- ticket auto-resolve, remediation auto-run, trade automation은 없다.

## Next Steps

1. repo 밖 runtime env file의 `PORTFOLIO_REMEDIATION_SKIP_DATES`를 운영 calendar에 맞춰 채운다.
2. `scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`로 preflight를 확인한다.
3. actual runtime DB smoke를 실행한다.
4. external holiday calendar sync를 도입할지 별도 task에서 결정한다.
