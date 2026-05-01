# Task Contract

## Task

- 이름: portfolio-remediation-scheduler-holiday-skip
- 요청: scheduler wrapper에 market holiday skip gate를 추가한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `PORTFOLIO_REMEDIATION_RUN_DATE`가 `PORTFOLIO_REMEDIATION_SKIP_DATES`에 포함되면 scheduler wrapper가 daily DB runner를 실행하지 않고 skip artifact를 남긴다.

## Why

- scheduler contract의 미해결 항목이었던 holiday skip rule을 최소 안전 형태로 구현해야 unattended 운영 위험을 줄일 수 있다.
- 외부 calendar 자동 동기화 없이도 운영자가 repo 밖 env file에 명시적 skip dates를 넣어 휴장일 실행을 막을 수 있어야 한다.

## Scope

- 포함:
  - wrapper explicit skip date gate
  - skip JSON/stderr artifact
  - preflight payload 확장
  - skip behavior verification
  - docs/task handoff 갱신
- 제외:
  - NYSE/Nasdaq holiday calendar 자동 수집
  - external alert destination
  - actual host launchd install
  - actual runtime DB smoke
  - remediation 자동 실행
  - ticket lifecycle 자동 변경
  - live broker/trading integration
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-05-01-portfolio-remediation-scheduler-holiday-skip.md`
  - `docs/portfolio-remediation-scheduler-holiday-skip.md`
  - `docs/portfolio-remediation-scheduler-contract.md`
  - `docs/portfolio-remediation-scheduler-activation.md`
  - `docs/portfolio-remediation-scheduler-env-readiness.md`
  - `docs/tasks/portfolio-remediation-scheduler-holiday-skip/`
  - `docs/verification-plan.md`
  - `scripts/run_portfolio_remediation_daily_scheduler.sh`
  - `scripts/verify_portfolio_remediation_scheduler_activation.sh`
  - `scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment secrets
  - host scheduler locations outside repo
- 검증에 사용할 명령:
  - `bash -n scripts/run_portfolio_remediation_daily_scheduler.sh`
  - `bash -n scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_activation.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-holiday-skip`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - wrapper holiday skip gate
  - holiday skip verification script
  - scheduler holiday skip docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] wrapper가 `PORTFOLIO_REMEDIATION_SKIP_DATES`를 해석한다.
- [x] skip date hit에서 daily DB runner를 호출하지 않는다.
- [x] skip date hit에서 JSON artifact를 생성한다.
- [x] skip date hit에서 stderr log artifact를 생성한다.
- [x] preflight output에 skip metadata가 포함된다.
- [x] production credentials는 repo에 저장하지 않는다.
- [x] actual DB smoke는 실행하지 않는다.
- [x] actual host scheduler install은 실행하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- 이 작업은 explicit skip dates만 지원하므로 holiday calendar 최신성은 운영자가 관리해야 한다.
- external holiday calendar 자동 수집은 아직 없다.
- skip artifact는 DB provenance를 만들지 않는다.
