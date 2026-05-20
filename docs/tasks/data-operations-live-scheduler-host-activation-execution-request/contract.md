# Task Contract

## Task

- 이름: data-operations-live-scheduler-host-activation-execution-request
- 요청: reviewed host activation plan 이후 실제 실행 전 명시적 execution approval 요청 패킷을 만들되 실행하지 않는다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: host activation plan이 준비되어도 scheduler activation은 실행되지 않고, operator/user가 검토할 execution approval request JSON만 생성된다.

## Why

- host activation plan은 실행 계획이지 실행 승인 기록이 아니다.
- 실제 host mutation 전에 명령 preview, rollback preview, 책임자, 위험 acknowledgement를 다시 명시적으로 승인해야 한다.

## Scope

- 포함:
  - host activation execution request report builder
  - repo-outside request wrapper script
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
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_activation_execution_request.py`
  - `tests/test_data_operations_scheduler_activation_execution_request.py`
  - `scripts/request_data_operations_live_scheduler_host_activation_execution.sh`
  - `scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh`
  - `docs/data-operations-live-scheduler-host-activation-execution-request.md`
  - `docs/data-operations-live-scheduler-host-activation-plan.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-live-scheduler-host-activation-execution-request.md`
  - `docs/tasks/data-operations-live-scheduler-host-activation-execution-request/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_plan.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Host activation execution request report builder
- Host activation execution request wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] ready host activation plan creates a pending execution approval request.
- [x] non-ready or mutated host activation plan is rejected.
- [x] request includes command and rollback previews.
- [x] request reports do not contain secret env values.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task to execution decision.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- A future execution decision task still must validate explicit approval before any host mutation.
- Command previews mention `launchctl`, but scripts must not execute it.
