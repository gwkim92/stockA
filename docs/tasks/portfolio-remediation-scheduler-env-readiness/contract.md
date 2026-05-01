# Task Contract

## Task

- 이름: portfolio-remediation-scheduler-env-readiness
- 요청: actual runtime DB smoke 전에 repo 밖 scheduler env file을 만들고 검증하는 readiness gate를 구축한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: repo 밖 env template renderer와 readiness checker가 존재하고, unedited template은 실패하며 valid temp env는 wrapper preflight까지 통과한다.

## Why

- production credentials는 Codex가 임의로 만들 수 없고 repo에 저장하면 안 된다.
- 실제 runtime DB smoke 전에 env file 형식, 필수 값, artifact root, wrapper preflight를 표준화해야 한다.

## Scope

- 포함:
  - repo-outside env template renderer
  - env readiness checker
  - wrapper `--preflight-only` integration
  - placeholder detection
  - Docker/DB connection 없는 verification
  - docs/task handoff 갱신
- 제외:
  - 실제 production DB credentials 생성 또는 저장
  - actual DB smoke execution
  - actual host launchd install
  - `launchctl bootstrap`
  - external alert destination
  - market holiday calendar integration
  - live broker/trading integration
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-05-01-portfolio-remediation-scheduler-env-readiness.md`
  - `docs/portfolio-remediation-scheduler-env-readiness.md`
  - `docs/portfolio-remediation-scheduler-runtime-env-smoke.md`
  - `docs/portfolio-remediation-scheduler-install.md`
  - `docs/tasks/portfolio-remediation-scheduler-env-readiness/`
  - `docs/verification-plan.md`
  - `scripts/render_portfolio_remediation_scheduler_env_template.sh`
  - `scripts/check_portfolio_remediation_scheduler_runtime_env.sh`
  - `scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment secrets
  - host scheduler locations outside repo
- 검증에 사용할 명령:
  - `bash -n scripts/render_portfolio_remediation_scheduler_env_template.sh`
  - `bash -n scripts/check_portfolio_remediation_scheduler_runtime_env.sh`
  - `bash -n scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-env-readiness`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - scheduler env template renderer
  - scheduler env readiness checker
  - readiness verification script
  - readiness docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] renderer가 repo 밖 env template을 생성한다.
- [x] renderer가 repo 내부 output을 거부한다.
- [x] readiness checker가 repo 내부 env file을 거부한다.
- [x] readiness checker가 unedited template placeholder를 거부한다.
- [x] readiness checker가 valid env file에서 wrapper preflight까지 통과한다.
- [x] production credentials는 repo에 저장하지 않는다.
- [x] actual DB smoke는 실행하지 않는다.
- [x] actual host scheduler install은 실행하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- env file은 shell source 방식이라 trusted file로만 사용해야 한다.
- readiness는 DB connectivity를 증명하지 않는다.
- actual runtime DB smoke와 launchd activation은 별도 승인/실행이 필요하다.
