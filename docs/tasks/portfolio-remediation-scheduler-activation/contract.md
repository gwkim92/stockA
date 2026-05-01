# Task Contract

## Task

- 이름: portfolio-remediation-scheduler-activation
- 요청: 실제 scheduler가 호출할 runtime wrapper와 preflight 검증을 추가한다.
- 담당: Codex
- 날짜: 2026-04-30

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `scripts/run_portfolio_remediation_daily_scheduler.sh`가 `portfolio-remediation-daily-run` 실행 전 required env와 artifact root를 검증하고, run mode에서는 stdout JSON/stderr log artifact를 저장한다. 실제 scheduler install은 여전히 수행하지 않는다.

## Why

- scheduler contract만으로는 host scheduler가 무엇을 호출해야 하는지 불명확하다. 실제 cron/launchd/hosted automation을 켜기 전에 repo-local wrapper를 만들어 실행 경계, artifact 저장, JSON validation을 고정해야 한다.

## Scope

- 포함:
  - scheduler runtime wrapper
  - preflight-only mode
  - required env validation
  - artifact root writable check
  - stdout JSON/stderr log capture
  - JSON report name validation
  - no-scheduler-install verification
  - docs/task handoff 갱신
- 제외:
  - 실제 OS cron install
  - launchd plist install
  - hosted automation 생성
  - app automation 활성화
  - secrets 또는 deployment config 변경
  - alert destination 연동
  - market holiday calendar integration
  - live broker/trading integration
  - remediation 자동 실행
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-30-portfolio-remediation-scheduler-activation.md`
  - `docs/portfolio-remediation-scheduler-activation.md`
  - `docs/portfolio-remediation-scheduler-contract.md`
  - `docs/tasks/portfolio-remediation-scheduler-activation/`
  - `docs/verification-plan.md`
  - `scripts/run_portfolio_remediation_daily_scheduler.sh`
  - `scripts/verify_portfolio_remediation_scheduler_activation.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment config
  - secrets
  - actual host scheduler files
- 검증에 사용할 명령:
  - `bash -n scripts/run_portfolio_remediation_daily_scheduler.sh`
  - `bash -n scripts/verify_portfolio_remediation_scheduler_activation.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_activation.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-activation`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - scheduler runtime wrapper
  - scheduler activation verification script
  - scheduler activation docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] wrapper가 required env를 검증한다.
- [x] wrapper가 artifact root writable check를 수행한다.
- [x] wrapper가 `--preflight-only` mode를 지원한다.
- [x] wrapper가 run mode에서 stdout JSON과 stderr log를 저장한다.
- [x] wrapper가 JSON report name을 검증한다.
- [x] verify script가 missing env failure와 successful preflight를 확인한다.
- [x] verify script가 no-scheduler-install boundary를 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- 이 작업은 실제 scheduler를 켜지 않는다.
- alert destination과 holiday skip rule은 아직 없다.
- run mode는 실제 DB runtime과 `STOCKANALYSIS_PSQL_COMMAND`가 있어야 한다.
