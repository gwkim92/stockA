# Portfolio Remediation Scheduler Env Readiness

이 문서는 actual runtime DB smoke 전에 scheduler env file을 repo 밖에서 만들고, DB 접속 없이 형식과 wrapper preflight를 검증하는 readiness gate를 정의한다.

## Current Status

- `scripts/render_portfolio_remediation_scheduler_env_template.sh`를 추가했다.
- `scripts/check_portfolio_remediation_scheduler_runtime_env.sh`를 추가했다.
- template renderer는 repo 내부 output path를 거부한다.
- readiness checker는 repo 내부 env file을 거부한다.
- readiness checker는 unedited placeholder template을 거부한다.
- readiness checker는 wrapper `--preflight-only`까지 실행한다.
- actual DB smoke, host launchd install, `launchctl bootstrap`은 아직 실행하지 않는다.

## Render Template

```bash
bash scripts/render_portfolio_remediation_scheduler_env_template.sh \
  --output /absolute/outside/repo/portfolio-remediation-scheduler.env
```

기존 파일을 덮어쓰려면 명시적으로 `--force`를 사용한다.

```bash
bash scripts/render_portfolio_remediation_scheduler_env_template.sh \
  --output /absolute/outside/repo/portfolio-remediation-scheduler.env \
  --force
```

## Readiness Check

```bash
bash scripts/check_portfolio_remediation_scheduler_runtime_env.sh \
  --env-file /absolute/outside/repo/portfolio-remediation-scheduler.env
```

통과 시 아래 형태의 JSON summary를 출력한다.

```json
{
  "runtime_env_readiness": "passed",
  "env_file": "/absolute/outside/repo/portfolio-remediation-scheduler.env",
  "artifact_root": "/absolute/path/to/portfolio-remediation-scheduler-artifacts",
  "psql_command_argv0": "psql",
  "wrapper_preflight": "passed"
}
```

## What It Checks

- env file이 repo 밖에 있음
- required env variables 존재
- placeholder 값이 남아 있지 않음
- `PORTFOLIO_REMEDIATION_AS_OF_DATE`와 `PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE`가 ISO date 형식임
- `PORTFOLIO_REMEDIATION_TICKET_LIMIT`가 positive integer임
- `PORTFOLIO_REMEDIATION_ARTIFACT_ROOT`가 absolute path이고 writable임
- `STOCKANALYSIS_PSQL_COMMAND`가 shell split 가능하고 첫 command가 local PATH에 존재함
- scheduler wrapper `--preflight-only`가 valid JSON을 반환함
- optional `PORTFOLIO_REMEDIATION_RUN_DATE`와 `PORTFOLIO_REMEDIATION_SKIP_DATES`가 설정된 경우 ISO date 형식인지 wrapper preflight에서 확인함

## Verification

```bash
bash scripts/verify_portfolio_remediation_scheduler_env_readiness.sh
```

검증은 아래를 확인한다.

- renderer/checker/wrapper/install script syntax
- repo 내부 template output 거부
- unedited template readiness failure
- valid temp env readiness success
- install dry-run compatibility

## Boundaries

- DB에 접속하지 않는다.
- production credentials를 repo에 저장하지 않는다.
- host `~/Library/LaunchAgents`에 쓰지 않는다.
- `launchctl bootstrap`을 실행하지 않는다.
- external alert destination은 아직 없다.
- market holiday skip은 아직 weekday schedule contract 수준이다.

## Next Steps

1. repo 밖 env file을 렌더링한다.
2. env file의 placeholder를 실제 runtime 값으로 바꾼다.
3. readiness check를 실행한다.
4. readiness가 통과하면 actual runtime DB smoke를 실행한다.
5. actual smoke가 통과하면 별도 승인 후 install과 `launchctl bootstrap`을 진행한다.
