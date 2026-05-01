# Portfolio Remediation Scheduler Activation Preflight

이 문서는 실제 scheduler가 호출할 repo-local wrapper인 `scripts/run_portfolio_remediation_daily_scheduler.sh`를 정의한다.

## Current Status

- runtime wrapper와 preflight 검증만 추가했다.
- 실제 OS cron, launchd, hosted automation, app automation은 설치하지 않았다.
- alert destination, secrets management는 아직 연결하지 않았다.
- market holiday skip은 explicit `PORTFOLIO_REMEDIATION_SKIP_DATES`로 지원한다.
- Docker Postgres runtime smoke는 `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`에서 별도 검증한다.

## Wrapper

preflight:

```bash
STOCKANALYSIS_PSQL_COMMAND="psql postgresql://example.invalid/stockanalysis" \
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01" \
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1" \
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02" \
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="/tmp/stockanalysis-remediation-scheduler" \
bash scripts/run_portfolio_remediation_daily_scheduler.sh --preflight-only
```

run mode:

```bash
STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis" \
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01" \
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1" \
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02" \
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="artifacts/portfolio-remediation-scheduler" \
bash scripts/run_portfolio_remediation_daily_scheduler.sh
```

## Required Environment

- `STOCKANALYSIS_PSQL_COMMAND`
- `PORTFOLIO_REMEDIATION_AS_OF_DATE`
- `PORTFOLIO_REMEDIATION_UNIVERSE_VERSION`
- `PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE`

## Optional Environment

- `PORTFOLIO_REMEDIATION_PORTFOLIO_NAME`, default `Long Term Paper`
- `PORTFOLIO_REMEDIATION_STRATEGY_NAME`, default `long_term_core`
- `PORTFOLIO_REMEDIATION_HORIZON_TYPE`, default `long_term`
- `PORTFOLIO_REMEDIATION_TICKET_LIMIT`, default `50`
- `PORTFOLIO_REMEDIATION_TICKET_STATUS`, default `open`
- `PORTFOLIO_REMEDIATION_ARTIFACT_ROOT`, default `artifacts/portfolio-remediation-scheduler`
- `PORTFOLIO_REMEDIATION_RUN_DATE`, default current `America/New_York` date
- `PORTFOLIO_REMEDIATION_SKIP_DATES`, comma or whitespace separated ISO dates
- `PORTFOLIO_REMEDIATION_SKIP_REASON`, default `configured_market_holiday`

## Artifact Behavior

Run mode stores:

- stdout JSON: `<as-of-date>-<utc-run-stamp>-portfolio-remediation-daily.json`
- stderr log: `<as-of-date>-<utc-run-stamp>-portfolio-remediation-daily.stderr.log`

The wrapper validates:

- required env exists
- `python3` exists
- artifact root is writable
- ticket limit is a positive integer
- run date and skip dates use ISO date format
- skip date hit writes skip artifact and does not run DB runner
- `portfolio-remediation-daily-run` exits successfully
- output JSON has `report_name = portfolio_remediation_daily_automation`
- output JSON has top-level `run_id`

## Verification

```bash
bash scripts/verify_portfolio_remediation_scheduler_activation.sh
```

The verification script checks:

- wrapper syntax
- verify script syntax
- missing required env fails
- preflight-only succeeds with required env
- preflight output is valid JSON
- preflight output includes skip metadata
- no cron/launchd/GitHub Actions scheduler activation artifact exists

## Boundaries

- This wrapper is not a scheduler.
- It does not install cron, launchd, GitHub Actions, or hosted automation.
- It does not send alerts.
- It only supports explicit skip dates and does not fetch an external holiday calendar.
- It does not auto-resolve or ignore tickets.
- It does not execute trades.

## Next Steps

1. intended runtime env file을 만들고 실제 의도한 runtime DB에서 wrapper run mode를 1회 실행한다.
2. Choose alert destination.
3. Decide how to maintain `PORTFOLIO_REMEDIATION_SKIP_DATES`.
4. After explicit approval, run install mode and manually bootstrap launchd.
