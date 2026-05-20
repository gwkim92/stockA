# Task Contract

## Task

- 이름: manual-host-scheduler-activation-explicit-approval
- 요청: host activation execution confirmation 이후 실제 host mutation 명령을 정확히 승인할 수 있는 approval packet을 만든다.
- 담당: Codex
- 날짜: 2026-05-15

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: exact execution commands와 rollback commands가 기계 검증 가능한 approval packet에 고정되고, approval record가 있어도 Codex task 안에서는 `launchctl`이나 LaunchAgents write를 직접 실행하지 않는다.

## Why

- `계속 진행`은 구현 진행 승인으로 보되, 실제 host mutation 실행 승인이 아니다.
- 이전 gate는 manual operator 실행 가능 상태만 만들었다.
- 이번 task는 사용자가 승인해야 할 정확한 명령과 책임 경계를 JSON으로 고정한다.

## Scope

- 포함:
  - manual host scheduler activation explicit approval report builder
  - exact command/rollback command drift validation
  - `stockanalysis-operations manual-host-scheduler-activation-explicit-approval`
  - thin wrapper script
  - verification script
  - docs/task handoff/roadmap updates
- 제외:
  - 실제 `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기
  - child data operation command 실행
  - production env file 생성
  - provider network calls
  - DB schema changes
  - FastAPI write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/manual_host_scheduler_activation_approval.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_manual_host_scheduler_activation_approval.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh`
  - `scripts/verify_manual_host_scheduler_activation_explicit_approval.sh`
  - `docs/manual-host-scheduler-activation-explicit-approval.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/plans/2026-05-15-manual-host-scheduler-activation-explicit-approval.md`
  - `docs/tasks/manual-host-scheduler-activation-explicit-approval/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_manual_host_scheduler_activation_approval tests.test_data_operations_cli -v`
  - `bash scripts/verify_manual_host_scheduler_activation_explicit_approval.sh`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task manual-host-scheduler-activation-explicit-approval`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Manual host scheduler activation explicit approval report builder
- Exact command approval record validation
- Thin wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] missing approval blocks host mutation and emits approval record template.
- [x] approval record allows only manual operator execution outside Codex.
- [x] abort record blocks host mutation.
- [x] exact execution/rollback command drift is rejected.
- [x] malformed/mismatched/secret-like approval records are rejected.
- [x] repo-inside input/output paths are rejected by Python policy.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap records that actual host mutation still requires separate exact user approval.
- [x] targeted, roadmap, AWH, compileall, and diff checks pass.
- [ ] full regression verification is blocked in the current system Python by missing FastAPI dependency and sandboxed socket bind; targeted, roadmap, AWH, compileall, and diff checks pass.

## Risks

- This does not activate recurring jobs.
- The next physical host mutation remains outside Codex execution until the user explicitly approves exact host commands.
- Manual execution outside this task can still affect host scheduler state.
