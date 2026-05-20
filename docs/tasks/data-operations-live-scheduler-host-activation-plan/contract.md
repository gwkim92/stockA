# Task Contract

## Task

- 이름: data-operations-live-scheduler-host-activation-plan
- 요청: final preflight 통과 후 host scheduler activation 실행 계획을 만들되 실행하지 않는다.
- 담당: Codex
- 날짜: 2026-05-11

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: final preflight 통과 증거가 있어도 host activation은 실행되지 않고, operator review용 JSON/Markdown plan과 다음 execution request 단계만 생성된다.

## Why

- final preflight 통과는 실행 허가가 아니라 실행 계획을 준비할 수 있다는 뜻이다.
- 실제 host mutation 전에 명령, rollback, observability, 책임자를 사람이 다시 검토할 수 있는 plan이 필요하다.

## Scope

- 포함:
  - host activation plan report builder
  - Markdown plan renderer
  - repo-outside plan wrapper script
  - verification script
  - docs/task handoff/roadmap updates
- 제외:
  - 실제 `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기
  - production env file 생성
  - provider network calls
  - Alertmanager receiver routing
  - DB schema changes
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_activation_host_plan.py`
  - `tests/test_data_operations_scheduler_activation_host_plan.py`
  - `scripts/plan_data_operations_live_scheduler_host_activation.sh`
  - `scripts/verify_data_operations_live_scheduler_host_activation_plan.sh`
  - `docs/data-operations-live-scheduler-host-activation-plan.md`
  - `docs/data-operations-live-scheduler-activation-final-preflight.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - prior data-operations verification scripts that assert immediate next task
  - `docs/plans/2026-05-11-data-operations-live-scheduler-host-activation-plan.md`
  - `docs/tasks/data-operations-live-scheduler-host-activation-plan/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - host scheduler paths
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_live_scheduler_host_activation_plan.sh`
  - `bash scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`

## Deliverables

- Host activation plan report builder
- Host activation plan wrapper script
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] passing final preflight creates JSON and Markdown plans.
- [x] denied/blocked final preflight is rejected.
- [x] plan includes command and rollback previews.
- [x] final reports do not contain secret env values.
- [x] no script executes `launchctl` or writes host LaunchAgents.
- [x] roadmap moves fixed next task to execution request.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate recurring jobs.
- A future execution request task still must require explicit approval before host mutation.
- Command previews mention `launchctl`, but scripts must not execute it.
