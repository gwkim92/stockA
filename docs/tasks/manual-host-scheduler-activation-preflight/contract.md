# Task Contract

## Task

- 이름: manual-host-scheduler-activation-preflight
- 요청: exact-command approval 이후 실제 host mutation 직전 runtime env와 approval packet을 함께 검증한다.
- 담당: Codex
- 날짜: 2026-05-15

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: approved exact-command packet과 repo-outside runtime env readiness가 모두 통과해야만 external manual execution 가능 상태가 되며, Codex task 안에서는 `launchctl`이나 LaunchAgents write를 직접 실행하지 않는다.

## Why

- 사용자가 진행 승인을 해도 env/evidence가 없으면 실제 host mutation을 하면 안 된다.
- 실행 직전에는 승인 packet과 runtime env를 함께 재검증해야 한다.
- 실제 실행 여부와 별개로 operator가 무엇을 실행하고 무엇을 증거로 남겨야 하는지 고정해야 한다.

## Scope

- 포함:
  - manual host scheduler activation preflight report builder
  - `stockanalysis-operations manual-host-scheduler-activation-preflight`
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
  - `src/stockanalysis/operations/manual_host_scheduler_activation_preflight.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_manual_host_scheduler_activation_preflight.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/preflight_manual_host_scheduler_activation.sh`
  - `scripts/verify_manual_host_scheduler_activation_preflight.sh`
  - `docs/manual-host-scheduler-activation-preflight.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/plans/2026-05-15-manual-host-scheduler-activation-preflight.md`
  - `docs/tasks/manual-host-scheduler-activation-preflight/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_manual_host_scheduler_activation_preflight tests.test_data_operations_cli -v`
  - `bash scripts/verify_manual_host_scheduler_activation_preflight.sh`
  - `bash scripts/verify_manual_host_scheduler_activation_explicit_approval.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task manual-host-scheduler-activation-preflight`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Manual host scheduler activation preflight report builder
- Thin wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] approved exact-command packet plus passed runtime env returns external manual execution readiness.
- [x] unapproved packet blocks external manual execution.
- [x] failed runtime env blocks external manual execution.
- [x] repo-inside approval/env/output paths are rejected by Python policy.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap records that actual host mutation still requires external manual execution with evidence.
- [x] targeted, roadmap, AWH, compileall, and diff checks pass.
- [ ] full regression verification is blocked in the current system Python by missing FastAPI dependency and sandboxed socket bind; targeted, roadmap, AWH, compileall, and diff checks pass.

## Risks

- This does not activate recurring jobs.
- The next physical host mutation remains outside Codex execution until the user supplies repo-outside env/evidence and approves exact host commands.
- Manual execution outside this task can still affect host scheduler state.
