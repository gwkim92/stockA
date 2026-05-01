# Portfolio Remediation Scheduler Install

이 문서는 macOS `launchd`용 scheduler install artifact를 정의한다.

## Current Status

- `scripts/install_portfolio_remediation_scheduler.sh`를 추가했다.
- 기본 모드는 `--dry-run`이다.
- 검증은 launchd plist를 temp artifact root에 렌더링할 뿐 host scheduler를 설치하지 않는다.
- 실제 install은 `--install`을 명시해야 하며, 이번 검증에서는 실행하지 않는다.
- Docker runtime smoke는 `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`로 별도 검증한다.
- env file 기반 runtime smoke gate는 `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`로 실행한다.
- env readiness gate는 `scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`로 실행한다.

## Dry Run

```bash
bash scripts/install_portfolio_remediation_scheduler.sh \
  --dry-run \
  --env-file /absolute/path/to/portfolio-remediation-scheduler.env
```

dry-run은 아래를 수행한다.

- env file 존재 확인
- scheduler wrapper 실행 가능 여부 확인
- schedule hour/minute 검증
- launchd plist 렌더링
- rendered plist path 출력

## Install Mode

```bash
bash scripts/install_portfolio_remediation_scheduler.sh \
  --install \
  --env-file /absolute/path/to/portfolio-remediation-scheduler.env
```

install mode는 rendered plist를 `~/Library/LaunchAgents/com.stockanalysis.portfolio-remediation-daily.plist`에 복사한다. `launchctl bootstrap`은 자동 실행하지 않고, 수동 activation command를 출력한다.

## Env File

env file은 shell source 가능한 형식이어야 한다.

```bash
STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PORTFOLIO_REMEDIATION_AS_OF_DATE="2024-11-01"
PORTFOLIO_REMEDIATION_UNIVERSE_VERSION="fixture-v1"
PORTFOLIO_REMEDIATION_COVERAGE_MEASUREMENT_END_DATE="2024-12-02"
PORTFOLIO_REMEDIATION_ARTIFACT_ROOT="/absolute/path/to/artifacts/portfolio-remediation-scheduler"
```

## Schedule

Default launchd schedule:

- label: `com.stockanalysis.portfolio-remediation-daily`
- weekdays: Monday through Friday
- hour: `18`
- minute: `30`

Override with:

- `PORTFOLIO_REMEDIATION_LAUNCHD_LABEL`
- `PORTFOLIO_REMEDIATION_SCHEDULE_HOUR`
- `PORTFOLIO_REMEDIATION_SCHEDULE_MINUTE`
- `PORTFOLIO_REMEDIATION_INSTALL_ARTIFACT_ROOT`

## Verification

```bash
bash scripts/verify_portfolio_remediation_scheduler_install.sh
```

검증은 아래를 확인한다.

- install script syntax
- scheduler wrapper syntax
- temp env file 기반 dry-run success
- rendered plist에 label, env file, wrapper path, working directory, weekday schedule 포함
- dry-run output이 host LaunchAgents 경로가 아님

## Boundaries

- verification은 actual host install을 실행하지 않는다.
- `launchctl bootstrap`을 자동 실행하지 않는다.
- external alert destination은 아직 없다.
- market holiday skip은 explicit `PORTFOLIO_REMEDIATION_SKIP_DATES` 수준이다.
- ticket auto-resolve, remediation auto-run, trade automation은 없다.

## Next Steps

1. repo 밖에 intended runtime env file을 만들고 `scripts/check_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`를 실행한다.
2. 실제 의도한 runtime DB에 대해 `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`를 실행한다.
3. alert destination을 정한다.
4. `PORTFOLIO_REMEDIATION_SKIP_DATES` 유지 방식을 결정한다.
5. 이후 `--install`과 `launchctl bootstrap`을 명시 승인 후 실행한다.
