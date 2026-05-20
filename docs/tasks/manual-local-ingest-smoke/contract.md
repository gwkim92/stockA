# Task Contract

## Task

- 이름: manual-local-ingest-smoke
- 요청: local-first runtime에서 market/news/AI 수동 수집 smoke를 preview-first 방식으로 실행하고 artifact를 남기는 CLI를 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `stockanalysis-operations manual-local-ingest-smoke`가 market/news/AI smoke 계획을 출력한다.
  - 기본 모드는 preview이며, `--execute` 없이는 provider/API/DB write command를 실행하지 않는다.
  - `--execute` 시 기존 artifact runner로 stdout/stderr/metadata를 남긴다.
  - env 파일 값과 API key, DB password, token은 절대 출력하지 않는다.
  - 실제 `launchctl`, LaunchAgents write/delete, 외부 scheduler 배포는 수행하지 않는다.

## Scope

- 포함:
  - `src/stockanalysis/operations/manual_local_ingest_smoke.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_manual_local_ingest_smoke.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_manual_local_ingest_smoke.sh`
  - `docs/manual-local-ingest-smoke.md`
  - `docs/plans/2026-05-20-manual-local-ingest-smoke.md`
  - `docs/tasks/manual-local-ingest-smoke/*`
  - `docs/local-runtime-status-orchestrator.md`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 제외:
  - 자동 반복 실행 설치
  - `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기/삭제
  - DB schema 변경
  - API/DTO 변경
  - broker/order behavior 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/manual_local_ingest_smoke.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_manual_local_ingest_smoke.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_manual_local_ingest_smoke.sh`
  - `docs/manual-local-ingest-smoke.md`
  - `docs/plans/2026-05-20-manual-local-ingest-smoke.md`
  - `docs/tasks/manual-local-ingest-smoke/contract.md`
  - `docs/tasks/manual-local-ingest-smoke/handoff.md`
  - `docs/tasks/manual-local-ingest-smoke/review.md`
  - `docs/local-runtime-status-orchestrator.md`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_manual_local_ingest_smoke.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task manual-local-ingest-smoke`
  - `git diff --check`

## Done Criteria

- [x] Manual local ingest smoke CLI exists.
- [x] Preview mode does not execute jobs.
- [x] Execute mode uses artifact runner.
- [x] Tests prove secrets are not emitted.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
