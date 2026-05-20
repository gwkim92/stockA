# Task Contract

## Task

- 이름: data-operations-live-scheduler-host-activation-execution-decision
- 요청: host activation execution request 이후 approve/deny decision record를 검증하되 실행하지 않는다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: execution request가 있어도 scheduler activation은 실행되지 않고, approve/deny decision gate JSON만 생성된다.

## Why

- execution request는 실행 승인 요청이지 실행 승인 기록이 아니다.
- 실제 host mutation 전에 별도 decision record가 요청 상태와 mutation boundary를 명확히 acknowledge해야 한다.

## Scope

- 포함:
  - host activation execution decision report builder
  - repo-outside decision wrapper script
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
  - `src/stockanalysis/operations/scheduler_activation_execution_decision.py`
  - `tests/test_data_operations_scheduler_activation_execution_decision.py`
  - `scripts/decide_data_operations_live_scheduler_host_activation_execution.sh`
  - `scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`
  - `docs/data-operations-live-scheduler-host-activation-execution-decision.md`
  - `docs/data-operations-live-scheduler-host-activation-execution-request.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-live-scheduler-host-activation-execution-decision.md`
  - `docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Host activation execution decision report builder
- Host activation execution decision wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] missing decision is blocked.
- [x] approve decision moves only to execution final preflight.
- [x] deny decision blocks execution.
- [x] mismatched request paths and missing acknowledgements are rejected.
- [x] decision reports do not contain secret env values.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task to execution final preflight.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- A future final preflight task still must revalidate fresh evidence before any host mutation.
- Command previews may remain in evidence, but scripts must not execute them.
