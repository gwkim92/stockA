# Task Contract

## Task

- 이름: data-operations-scheduler-activation-boundary
- 요청: runtime smoke 이후 실제 scheduler 설치 전에 generic data operations scheduler wrapper/env/artifact/skip boundary를 구현한다.
- 담당: Codex
- 날짜: 2026-05-04

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: actual scheduler가 나중에 호출할 repo-local wrapper가 존재하고, trusted repo-outside env readiness, known cadence job validation, command redaction preflight, skip-date boundary, artifact runner invocation을 검증할 수 있다.

## Why

- scheduler 설치 전에 호출 계약이 고정되어야 host scheduler artifacts와 secrets가 섞이지 않는다.
- runtime smoke는 수동 실행 증거다. actual scheduler가 호출할 wrapper contract는 별도 boundary로 고정해야 한다.

## Scope

- 포함:
  - generic scheduler boundary Python report helper
  - `scripts/run_data_operations_scheduler_job.sh`
  - preflight-only JSON
  - configured skip-date JSON artifact
  - artifact runner invocation
  - no scheduler install artifact guard
  - docs/task handoff/roadmap 갱신
- 제외:
  - actual scheduler install/activation
  - cron/launchd/GitHub Actions 파일 생성
  - production env file or real credentials
  - provider network credential validation
  - DB schema changes
  - write APIs, RBAC, audit write model
  - broker/order flow
  - benchmark/scoring/evaluation split 변경
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_boundary.py`
  - `tests/test_data_operations_scheduler_boundary.py`
  - `scripts/run_data_operations_scheduler_job.sh`
  - `scripts/verify_data_operations_scheduler_activation_boundary.sh`
  - `docs/data-operations-scheduler-activation-boundary.md`
  - `docs/data-operations-runtime-smoke.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_data_operations_runtime_smoke.sh`
  - `scripts/verify_data_operations_runtime_env_readiness.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-04-data-operations-scheduler-activation-boundary.md`
  - `docs/tasks/data-operations-scheduler-activation-boundary/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_scheduler_activation_boundary.sh`
  - `bash scripts/verify_data_operations_runtime_smoke.sh`
  - `bash scripts/verify_data_operations_runtime_env_readiness.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-scheduler-activation-boundary`
  - `git diff --check`

## Deliverables

- Generic scheduler boundary helper
- Scheduler job wrapper
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] wrapper refuses missing env file, repo-inside env file, and missing command.
- [x] preflight runs env readiness and emits secret-free JSON.
- [x] preflight validates known cadence job and redacts sensitive command argv.
- [x] configured skip date emits skip JSON artifact without running child command.
- [x] non-skip mode invokes `data-operations-run` and produces artifact metadata.
- [x] no cron/launchd/GitHub Actions scheduler activation artifacts are created.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not install or enable a scheduler.
- This does not validate provider credentials against remote APIs.
- Actual host scheduler rendering remains a separate dry-run task.
