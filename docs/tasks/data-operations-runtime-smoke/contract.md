# Task Contract

## Task

- 이름: data-operations-runtime-smoke
- 요청: env readiness 이후 실제 scheduler 활성화 전에 대표 cadence job을 disposable/local runtime에서 artifact runner로 실행하는 smoke를 구현한다.
- 담당: Codex
- 날짜: 2026-05-04

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: trusted repo-outside env file이 readiness를 통과한 뒤, known cadence `job_id`가 `data-operations-run`으로 실행되고 stdout/stderr/metadata artifact와 secret-free smoke summary가 남는다.

## Why

- env readiness는 설정 형식만 확인한다. 실제 반복 운영 전에는 최소 1개 representative job이 runner, env inheritance, DB boundary, artifact capture를 함께 통과하는지 확인해야 한다.
- scheduler 활성화 전에 실패가 발생해도 stdout/stderr/metadata가 남는지 검증해야 한다.

## Scope

- 포함:
  - runtime smoke report builder
  - `scripts/smoke_data_operations_runtime.sh`
  - Docker Postgres + fixture macro batch representative verification
  - env readiness gate integration
  - stdout/stderr/metadata artifact assertions
  - docs/task handoff/roadmap 갱신
- 제외:
  - actual scheduler activation
  - cron/launchd/GitHub Actions 생성
  - production env file or real credentials
  - provider network credential validation
  - DB schema changes
  - write APIs, RBAC, audit write model
  - broker/order flow
  - benchmark/scoring/evaluation split 변경
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/runtime_smoke.py`
  - `tests/test_data_operations_runtime_smoke.py`
  - `scripts/smoke_data_operations_runtime.sh`
  - `scripts/verify_data_operations_runtime_smoke.sh`
  - `docs/data-operations-runtime-smoke.md`
  - `docs/data-operations-runtime-env-readiness.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_data_operations_runtime_env_readiness.sh`
  - `scripts/verify_data_operations_artifact_runner.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-04-data-operations-runtime-smoke.md`
  - `docs/tasks/data-operations-runtime-smoke/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_runtime_smoke.sh`
  - `bash scripts/verify_data_operations_runtime_env_readiness.sh`
  - `bash scripts/verify_data_operations_artifact_runner.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-runtime-smoke`
  - `git diff --check`

## Deliverables

- Runtime smoke report builder
- Runtime smoke shell wrapper
- Docker/local verification script
- Unit tests
- Docs and handoff updates

## Completion Criteria

- [x] smoke wrapper refuses missing command/env misuse.
- [x] smoke wrapper runs env readiness before the artifact runner.
- [x] representative `macro-weekly` job runs through `data-operations-run` against disposable Postgres using fixtures.
- [x] stdout/stderr/metadata artifacts exist and metadata has redacted argv only.
- [x] smoke report does not expose DB URL/API keys/user-agent values.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate production scheduling.
- This does not validate provider credentials against remote APIs because fixture mode is intentional.
- Docker must be available for the full runtime smoke verification.
