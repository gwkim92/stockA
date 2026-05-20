# Task Contract

## Task

- 이름: data-operations-artifact-runner
- 요청: data operations cadence registry 이후 실제 scheduler 활성화 전에 stdout/stderr/metadata artifact capture wrapper를 구현한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: known cadence `job_id`에 대해 command를 실행하고, `STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT` 아래에 stdout/stderr/metadata artifact를 남기는 generic runner와 CLI가 존재한다.

## Why

- 반복 운영 루프는 실패 시 stdout/stderr/metadata를 남겨야 원인 분석과 rerun이 가능하다.
- cadence registry만으로는 실제 실행 증거가 남지 않는다.
- scheduler를 켜기 전에 repo-local wrapper가 deterministic smoke로 검증되어야 한다.

## Scope

- 포함:
  - known `job_id` validation
  - stdout/stderr/metadata artifact capture
  - JSON stdout normalization when possible
  - command argv redaction
  - CLI `data-operations-run`
  - verification script
  - docs/task handoff/roadmap 갱신
- 제외:
  - actual scheduler activation
  - cron/launchd/hosted automation 생성
  - production env file or real credentials
  - DB schema changes
  - write APIs, RBAC, audit write model
  - broker/order flow
  - benchmark/scoring/evaluation split 변경
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/artifact_runner.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_data_operations_artifact_runner.py`
  - `tests/test_ingest_cli.py`
  - `docs/data-operations-artifact-runner.md`
  - `docs/data-operations-cadence-foundation.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_data_operations_artifact_runner.sh`
  - `scripts/verify_data_operations_cadence_foundation.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-data-operations-artifact-runner.md`
  - `docs/tasks/data-operations-artifact-runner/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_artifact_runner.sh`
  - `bash scripts/verify_data_operations_cadence_foundation.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-artifact-runner`
  - `git diff --check`

## Deliverables

- Artifact runner module
- CLI run wrapper
- Unit tests and CLI smoke
- Verification script
- Task docs and roadmap updates

## Completion Criteria

- [x] runner validates known cadence job ids.
- [x] runner writes stdout, stderr, metadata, and JSON stdout when possible.
- [x] runner captures failed exit codes without losing artifacts.
- [x] runner redacts sensitive argv values in metadata.
- [x] CLI returns child exit code and prints metadata JSON.
- [x] roadmap moves fixed next task to runtime env readiness.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not activate production scheduling.
- Command argv redaction is a guardrail, not a substitute for keeping secrets out of argv.
- Runtime env readiness for real providers is the next task.
