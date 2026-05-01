# Task Contract

## Task

- 이름: portfolio-remediation-scheduler-runtime-env-smoke
- 요청: intended runtime env file로 scheduler wrapper run mode를 1회 smoke 실행할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: trusted env file을 입력으로 받아 scheduler wrapper를 실행하고 JSON/stderr artifact, BABA open remediation ticket, latest DB pipeline run status를 검증하는 repo-local smoke runner가 존재한다.

## Why

- Docker runtime smoke는 wrapper 동작을 증명했지만, 실제 운영 전에는 launchd가 사용할 env file과 같은 형태로 runtime DB smoke를 실행할 수 있어야 한다.
- production credentials를 repo에 저장하지 않으면서도 운영 전 manual gate를 표준화해야 한다.

## Scope

- 포함:
  - env file 기반 smoke runner
  - Docker fixture 기반 runner verification
  - artifact path validation
  - JSON payload validation
  - latest `portfolio_remediation_daily_automation` status validation
  - docs/task handoff 갱신
- 제외:
  - 실제 production DB credentials 생성 또는 저장
  - actual host launchd install
  - `launchctl bootstrap`
  - external alert destination
  - market holiday calendar integration
  - remediation 자동 실행
  - ticket lifecycle 자동 변경
  - live broker/trading integration
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-05-01-portfolio-remediation-scheduler-runtime-env-smoke.md`
  - `docs/portfolio-remediation-scheduler-runtime-env-smoke.md`
  - `docs/portfolio-remediation-scheduler-runtime-smoke.md`
  - `docs/portfolio-remediation-scheduler-install.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/`
  - `docs/verification-plan.md`
  - `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`
  - `scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment secrets
  - host scheduler locations outside repo
- 검증에 사용할 명령:
  - `bash -n scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`
  - `bash -n scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-runtime-env-smoke`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - env file 기반 runtime smoke runner
  - Docker verification script
  - runtime env smoke docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] env file 기반 smoke runner가 추가된다.
- [x] runner가 wrapper JSON artifact를 검증한다.
- [x] runner가 wrapper stderr artifact를 검증한다.
- [x] runner가 BABA open remediation ticket을 검증한다.
- [x] runner가 latest `portfolio_remediation_daily_automation` status `succeeded`를 검증한다.
- [x] production credentials는 repo에 저장하지 않는다.
- [x] actual host scheduler install은 실행하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- env file은 shell source 방식이라 trusted file로만 사용해야 한다.
- Docker smoke는 production DB 품질을 보장하지 않는다.
- production runtime smoke는 실제 credentials 없이는 수행할 수 없다.
