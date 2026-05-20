# Task Contract

## Task

- 이름: data-operations-backend-orchestration-boundary
- 요청: data operations host activation 흐름에서 shell wrapper가 backend orchestration 역할을 과도하게 담당하는 문제를 줄인다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: data operations 운영 로직은 Python backend package의 CLI/service boundary로 들어가고, shell은 검증 또는 thin wrapper 역할만 한다.

## Why

- 현재 FastAPI 서버는 read-only frontend DTO API이며 write/activation flow를 담당하지 않는다.
- data operations backend 모듈은 존재하지만 전용 `stockanalysis-operations` entrypoint가 없어 일부 shell wrapper가 path guard, JSON IO, decision dispatch를 직접 담당하고 있다.
- host scheduler activation final preflight를 계속 shell 중심으로 확장하면 제품 backend와 하네스 검증 경계가 더 흐려진다.

## Scope

- 포함:
  - `stockanalysis-operations` console entrypoint
  - operations CLI first slice
  - repo-outside path policy helper
  - JSON report IO helper
  - host activation execution decision wrapper의 thin-wrapper 전환
  - unit tests and verification updates
  - roadmap/handoff/docs updates
- 제외:
  - FastAPI write/operator API
  - RBAC, actor identity, audit write
  - DB schema changes for operations state
  - actual `launchctl` execution
  - host LaunchAgents write
  - child data operation command execution outside existing artifact runner behavior
  - broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `pyproject.toml`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/path_policy.py`
  - `src/stockanalysis/operations/report_io.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/decide_data_operations_live_scheduler_host_activation_execution.sh`
  - `scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/data-operations-backend-orchestration-boundary.md`
  - `docs/plans/2026-05-11-data-operations-backend-orchestration-boundary.md`
  - `docs/tasks/data-operations-backend-orchestration-boundary/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli -v`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- `stockanalysis-operations` backend CLI entrypoint
- shared path/report IO helpers
- thin execution decision shell wrapper
- CLI tests and verification updates
- docs/task handoff

## Completion Criteria

- [x] operations CLI can print cadence reports.
- [x] operations CLI can validate host activation execution decisions.
- [x] repo-inside execution request paths are rejected by Python policy, not shell-only logic.
- [x] thin wrapper delegates to `stockanalysis.operations.cli`.
- [x] no code path executes `launchctl` or writes host LaunchAgents.
- [x] roadmap records the boundary refactor as a deliberate interposed task before execution final preflight.
- [x] verification commands pass and evidence is recorded.

## Risks

- This is a first slice, not a full migration of every data operations wrapper.
- Existing legacy `stockanalysis-ingest data-operations-*` commands remain for compatibility.
- A future task should migrate the remaining non-verify wrappers to the same CLI boundary.
