# Task Contract

## Task

- 이름: portfolio-remediation-scheduler-install
- 요청: `portfolio-remediation-daily-run` scheduler를 위한 launchd install artifact를 추가한다.
- 담당: Codex
- 날짜: 2026-04-30

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `scripts/install_portfolio_remediation_scheduler.sh --dry-run`이 launchd plist를 artifact로 렌더링하고, 실제 host scheduler install 없이 label/schedule/env/wrapper path를 검증한다.

## Why

- wrapper만 있으면 어떤 scheduler가 어떤 설정으로 호출해야 하는지 여전히 host마다 달라진다. macOS 개발 환경에서는 launchd install artifact가 필요하지만, 실제 host 등록은 env file과 runtime DB smoke test 후 명시적으로만 수행해야 한다.

## Scope

- 포함:
  - launchd plist rendering
  - dry-run default install script
  - explicit `--install` mode guard
  - env file path validation
  - weekday schedule rendering
  - local artifact failure marker policy
  - no-host-install verification
  - docs/task handoff 갱신
- 제외:
  - 실제 `launchctl bootstrap` 실행
  - 실제 `~/Library/LaunchAgents` 쓰기 검증
  - secrets 생성 또는 수정
  - external alert destination 연동
  - market holiday calendar integration
  - live broker/trading integration
  - remediation 자동 실행
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-30-portfolio-remediation-scheduler-install.md`
  - `docs/portfolio-remediation-scheduler-install.md`
  - `docs/portfolio-remediation-scheduler-activation.md`
  - `docs/portfolio-remediation-scheduler-contract.md`
  - `docs/tasks/portfolio-remediation-scheduler-install/`
  - `docs/verification-plan.md`
  - `scripts/install_portfolio_remediation_scheduler.sh`
  - `scripts/verify_portfolio_remediation_scheduler_install.sh`
  - `scripts/verify_portfolio_remediation_scheduler_contract.sh`
  - `scripts/verify_portfolio_remediation_scheduler_activation.sh`
- 수정 금지 파일:
  - `src/`
  - `tests/`
  - DB migrations
  - deployment secrets
  - host scheduler locations outside repo
- 검증에 사용할 명령:
  - `bash -n scripts/install_portfolio_remediation_scheduler.sh`
  - `bash -n scripts/verify_portfolio_remediation_scheduler_install.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_install.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_contract.sh`
  - `bash scripts/verify_portfolio_remediation_scheduler_activation.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-install`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - launchd install script
  - install dry-run verification script
  - scheduler install docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] install script defaults to dry-run.
- [x] install script renders a valid launchd plist artifact.
- [x] install mode requires explicit `--install`.
- [x] rendered plist contains wrapper path, env file path, label, weekday schedule.
- [x] verification script proves dry-run without writing host scheduler paths.
- [x] previous contract/activation verifies still pass.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- actual host install is still not executed in verification.
- holiday skip is weekday-only, not market-holiday aware.
- alert destination is still local artifact marker, not external notification.
