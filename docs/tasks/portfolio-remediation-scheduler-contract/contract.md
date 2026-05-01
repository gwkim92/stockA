# Task Contract

## Task

- 이름: portfolio-remediation-scheduler-contract
- 요청: 실제 scheduler 활성화 전 `portfolio-remediation-daily-run` 운영 계약을 확정한다.
- 담당: Codex
- 날짜: 2026-04-30

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: scheduler activation 전 필요한 실행 주기, 실패 알림, artifact 저장, retry/rollback 정책이 문서화되고, repo-local verify script가 해당 문서와 no-activation boundary를 검증한다.

## Why

- `portfolio-remediation-daily-run`은 이미 deterministic runner로 구현되어 있다. 그러나 실제 반복 실행을 켜기 전에는 언제 실행할지, 실패 시 어떻게 알릴지, 실행 결과를 어디에 남길지, 재시도와 롤백 기준을 먼저 고정해야 한다.

## Scope

- 포함:
  - scheduler activation 전 contract
  - automation loop contract
  - command template
  - artifact/log retention policy
  - alert/retry/rollback policy
  - no-activation verification script
  - docs/task handoff 갱신
- 제외:
  - 실제 OS cron install
  - hosted automation 생성
  - app automation 활성화
  - secrets 또는 deployment config 변경
  - live broker/trading integration
  - remediation 자동 실행
  - DB schema 변경
  - recommendation/thesis/review/performance 산식 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-30-portfolio-remediation-scheduler-contract.md`
  - `docs/portfolio-remediation-scheduler-contract.md`
  - `docs/portfolio-remediation-daily-automation.md`
  - `docs/tasks/portfolio-remediation-scheduler-contract/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_remediation_scheduler_contract.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment config
  - secrets
  - actual host scheduler files
- 검증에 사용할 명령:
  - `bash -n scripts/verify_portfolio_remediation_scheduler_contract.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_contract.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-contract`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - scheduler contract docs
  - loop contract
  - verification script
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] 실행 주기가 문서화된다.
- [x] 실패 알림 정책이 문서화된다.
- [x] artifact/log 저장 정책이 문서화된다.
- [x] retry/rollback 정책이 문서화된다.
- [x] 실제 scheduler activation이 범위 밖임이 명시된다.
- [x] verify script가 no-activation boundary를 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- contract는 scheduler를 실제로 켜지 않는다.
- scheduler activation은 host 정책, secrets, runtime environment 확인 후 별도 승인으로 진행해야 한다.
- 반복 실행은 open ticket을 늘릴 수 있으므로 ticket report와 alert threshold가 먼저 필요하다.
