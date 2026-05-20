# Task Contract

## Task

- 이름: data-operations-live-scheduler-host-activation-execution-final-preflight
- 요청: approved host activation execution decision 이후 실제 host mutation 전에 fresh runtime readiness와 evidence chain을 다시 검증한다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 승인된 execution decision이 있어도 이 task는 scheduler를 설치하지 않고, host activation execution task로 넘길 수 있는지 여부만 JSON으로 판정한다.

## Why

- execution decision은 실행 승인 기록이지만, 실제 host mutation 직전에는 runtime env와 reviewed plan이 여전히 유효한지 다시 확인해야 한다.
- 이전 backend boundary correction에 따라 새 구현은 shell heredoc orchestration이 아니라 `stockanalysis-operations` backend CLI/service boundary를 사용해야 한다.

## Scope

- 포함:
  - host activation execution final preflight report builder
  - Python env file loader for operations CLI
  - `stockanalysis-operations host-activation-execution-final-preflight`
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
  - `src/stockanalysis/operations/env_file.py`
  - `src/stockanalysis/operations/scheduler_activation_execution_final_preflight.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_scheduler_activation_execution_final_preflight.py`
  - `scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh`
  - `scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh`
  - `docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-live-scheduler-host-activation-execution-final-preflight.md`
  - `docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution_final_preflight tests.test_data_operations_cli -v`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh`
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-operations-live-scheduler-host-activation-execution-final-preflight`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Host activation execution final preflight report builder
- Operations CLI subcommand
- Thin wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] approved execution decision plus fresh runtime readiness passes to a future execution task.
- [x] denied/missing execution decision blocks execution.
- [x] failed runtime readiness blocks execution.
- [x] reviewed host plan command previews must match execution request command previews.
- [x] repo-inside input/output paths are rejected by Python policy.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task to a separate host activation execution task that still requires explicit user confirmation.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- The next execution task is high-risk host mutation and must not run without explicit user confirmation.
- Remaining non-verify wrappers still need incremental migration to the operations CLI boundary.
