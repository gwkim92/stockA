# Session Handoff

## Active Task

- 이름: portfolio-remediation-scheduler-runtime-env-smoke
- 담당: Codex
- 날짜: 2026-05-01

## Current Status

- 완료:
  - env file 기반 runtime smoke runner를 추가했다.
  - Docker Postgres fixture로 runner가 wrapper, artifact, BABA ticket, latest DB run status를 검증하는지 확인했다.
  - README, verification plan, scheduler runtime/install docs를 갱신했다.
- 막힌 점:
  - production DB smoke와 actual launchd install은 이번 범위 밖이다.

## Files Touched

- 생성:
  - `docs/plans/2026-05-01-portfolio-remediation-scheduler-runtime-env-smoke.md`
  - `docs/portfolio-remediation-scheduler-runtime-env-smoke.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/contract.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/plan.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/handoff.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/review.md`
  - `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`
  - `scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`
- 수정:
  - `README.md`
  - `docs/portfolio-remediation-scheduler-runtime-smoke.md`
  - `docs/portfolio-remediation-scheduler-install.md`
  - `docs/verification-plan.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/contract.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/handoff.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/review.md`

## Decisions

- env file은 trusted shell sourceable file로 취급한다.
- production credentials는 repo에 저장하지 않는다.
- actual host launchd install과 `launchctl bootstrap`은 범위 밖이다.
- Docker fixture로 runner 자체를 검증한다.
- runner는 wrapper stdout JSON path를 읽고 sibling stderr log path를 검증한다.
- runner는 `STOCKANALYSIS_PSQL_COMMAND`를 `shlex.split`으로 해석해 latest DB run status를 조회한다.

## Verification Already Run

- `bash -n scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`: 통과
- `bash -n scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-runtime-env-smoke`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- production DB runtime smoke
- repo 밖 intended runtime env file
- actual host launchd install
- `launchctl bootstrap`
- external alert destination
- market holiday calendar integration

## Exact Next Step

- 다음 세션은 이것부터 시작: repo 밖에 intended runtime env file을 만들고 실제 의도한 runtime DB에서 `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh --env-file <env>`를 1회 실행한다. 통과하면 별도 승인으로 `scripts/install_portfolio_remediation_scheduler.sh --install --env-file <env>`와 `launchctl bootstrap`을 진행한다.

## Risks

- env file source 방식은 untrusted file에 쓰면 안 된다.
- Docker smoke는 production DB runtime quality를 보장하지 않는다.
- alert destination과 market holiday skip rule이 아직 없으므로 unattended 운영 준비는 미완성이다.
