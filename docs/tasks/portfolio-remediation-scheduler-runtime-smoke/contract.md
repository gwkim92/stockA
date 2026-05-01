# Task Contract

## Task

- 이름: portfolio-remediation-scheduler-runtime-smoke
- 요청: scheduler wrapper run mode를 실제 DB runtime에서 smoke test한다.
- 담당: Codex
- 날짜: 2026-04-30

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: Docker Postgres에서 prerequisite data를 만든 뒤 `scripts/run_portfolio_remediation_daily_scheduler.sh` run mode가 `portfolio-remediation-daily-run`을 실행하고 JSON/stderr artifact와 succeeded DB pipeline run을 남긴다.

## Why

- install dry-run은 launchd plist 렌더링만 증명한다. 실제 scheduler 등록 전에는 wrapper run mode가 DB runtime에서 artifact capture와 JSON validation까지 통과하는지 확인해야 한다.

## Scope

- 포함:
  - Docker runtime smoke script
  - wrapper run mode artifact validation
  - daily remediation JSON payload validation
  - DB latest `portfolio_remediation_daily_automation` status validation
  - docs/task handoff 갱신
- 제외:
  - actual host launchd install
  - production DB smoke
  - external alert destination
  - market holiday calendar integration
  - remediation 자동 실행
  - ticket lifecycle 자동 변경
  - live broker/trading integration
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-30-portfolio-remediation-scheduler-runtime-smoke.md`
  - `docs/portfolio-remediation-scheduler-runtime-smoke.md`
  - `docs/portfolio-remediation-scheduler-install.md`
  - `docs/portfolio-remediation-scheduler-activation.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment secrets
  - host scheduler locations outside repo
- 검증에 사용할 명령:
  - `bash -n scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-runtime-smoke`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - scheduler runtime smoke verification script
  - scheduler runtime smoke docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] Docker Postgres prerequisite pipeline이 준비된다.
- [x] scheduler wrapper run mode가 실행된다.
- [x] wrapper stdout JSON artifact가 생성된다.
- [x] wrapper stderr log artifact가 생성된다.
- [x] JSON payload가 BABA open remediation ticket을 포함한다.
- [x] latest `portfolio_remediation_daily_automation` run status가 `succeeded`다.
- [x] actual host scheduler install은 실행하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- Docker socket 권한은 sandbox 밖 실행이 필요할 수 있다.
- production runtime DB smoke는 아직 아니다.
- external alert destination과 market holiday skip rule은 아직 없다.
