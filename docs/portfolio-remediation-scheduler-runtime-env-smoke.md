# Portfolio Remediation Scheduler Runtime Env Smoke

이 문서는 trusted env file을 사용해 scheduler wrapper run mode를 1회 실행하고, 실제 runtime DB와 artifact 상태를 검증하는 manual gate를 정의한다.

## Current Status

- `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`를 추가했다.
- runner는 `--env-file`을 받아 shell source한 뒤 `scripts/run_portfolio_remediation_daily_scheduler.sh`를 실행한다.
- wrapper가 생성한 JSON artifact, stderr artifact, BABA open remediation ticket, latest DB pipeline run status를 검증한다.
- runner 자체는 `scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`에서 Docker Postgres fixture로 검증한다.
- actual smoke 전에 `scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`로 readiness를 먼저 확인한다.
- production credentials와 host launchd install은 아직 실행하지 않는다.

## Command

```bash
bash scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh \
  --env-file /absolute/path/to/portfolio-remediation-scheduler.env
```

성공 시 runner는 아래 형태의 JSON summary를 stdout으로 출력한다.

```json
{
  "runtime_env_smoke": "passed",
  "json_path": "/absolute/path/to/artifacts/2024-11-01-20260501T000000Z-portfolio-remediation-daily.json",
  "stderr_path": "/absolute/path/to/artifacts/2024-11-01-20260501T000000Z-portfolio-remediation-daily.stderr.log",
  "run_id": "00000000-0000-0000-0000-000000000000",
  "ticket_count": 1,
  "latest_daily_automation_status": "succeeded"
}
```

## Env File

env file은 trusted shell sourceable file이어야 한다. 이 파일은 repo에 저장하지 않는 것을 기본으로 한다.

```bash
STOCKANALYSIS_PSQL_COMMAND="psql postgresql://user:password@host:5432/stockanalysis"
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01"
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1"
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02"
PORTFOLIO_REMEDIATION_TICKET_LIMIT="50"
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="/absolute/path/to/artifacts/portfolio-remediation-scheduler"
```

## Verification

```bash
bash scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh
```

검증은 아래를 확인한다.

- runner syntax
- scheduler wrapper syntax
- Docker Postgres migration/seed
- prerequisite pipeline execution
- temp env file sourcing
- wrapper JSON/stderr artifact creation
- BABA open `thesis_remediation` ticket
- latest `portfolio_remediation_daily_automation` status `succeeded`

## Boundaries

- production credentials를 repo에 저장하지 않는다.
- host `~/Library/LaunchAgents`에 쓰지 않는다.
- `launchctl bootstrap`을 실행하지 않는다.
- external alert destination은 아직 없다.
- market holiday skip은 아직 weekday schedule contract 수준이다.
- ticket auto-resolve, remediation auto-run, trade automation은 없다.

## Next Steps

1. `scripts/render_portfolio_remediation_scheduler_env_template.sh --output <env>`로 repo 밖 env template을 만든다.
2. env file placeholder를 실제 runtime 값으로 바꾼다.
3. `scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`를 실행한다.
4. 실제 의도한 runtime DB에서 `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`를 1회 실행한다.
5. 통과 결과의 `json_path`, `stderr_path`, `run_id`를 운영 기록으로 남긴다.
6. 명시 승인 후 `scripts/install_portfolio_remediation_scheduler.sh --install --env-file <env>`와 `launchctl bootstrap`을 실행한다.
