# Task Contract

## Task

- 이름: data-operations-live-scheduler-host-activation-execution
- 요청: host activation execution final preflight 이후 실제 host mutation 직전 confirmation gate를 만든다.
- 담당: Codex
- 날짜: 2026-05-15

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: final preflight가 통과해도 confirmation record 없이는 실행이 blocked로 남고, confirmation record가 있어도 이 task는 `launchctl`이나 LaunchAgents write를 직접 실행하지 않는다.

## Why

- 실제 host scheduler activation은 고위험 host mutation이다.
- `계속 진행`은 구현 진행 승인으로 보되, 실제 `launchctl bootstrap` 실행 승인은 별도로 더 명확히 받아야 한다.
- 이전 boundary 결정에 따라 shell이 아니라 `stockanalysis-operations` backend CLI/service boundary에서 실행 gate를 관리한다.

## Scope

- 포함:
  - host activation execution report builder
  - confirmation record validation
  - `stockanalysis-operations host-activation-execution`
  - thin wrapper script
  - verification script
  - docs/task handoff/roadmap updates
- 제외:
  - 실제 `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기
  - child data operation command 실행
  - production env file 생성
  - provider network calls
  - Alertmanager receiver routing
  - DB schema changes
  - FastAPI write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_activation_execution.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_data_operations_scheduler_activation_execution.py`
  - `scripts/run_data_operations_live_scheduler_host_activation_execution.sh`
  - `scripts/verify_data_operations_live_scheduler_host_activation_execution.sh`
  - `docs/data-operations-live-scheduler-host-activation-execution.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/plans/2026-05-15-data-operations-live-scheduler-host-activation-execution.md`
  - `docs/tasks/data-operations-live-scheduler-host-activation-execution/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution -v`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution.sh`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-operations-live-scheduler-host-activation-execution`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Host activation execution gate report builder
- Confirmation record validation
- Thin wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] missing confirmation blocks host mutation.
- [x] confirm record allows only manual operator execution outside this task.
- [x] abort record blocks host mutation.
- [x] malformed/mismatched/secret-like confirmation records are rejected.
- [x] repo-inside input/output paths are rejected by Python policy.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap records that actual host mutation still requires separate manual action.
- [ ] full regression verification is blocked in the current system Python by missing FastAPI dependency and sandboxed socket bind; targeted, roadmap, AWH, compileall, and diff checks pass.

## Risks

- This does not activate recurring jobs.
- The next physical host mutation remains outside Codex execution until the user explicitly approves exact host commands.
- Manual execution outside this task can still affect host scheduler state.
