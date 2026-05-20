# Task Contract

## Task

- 이름: local-runtime-status-orchestrator
- 요청: local-first runtime을 위해 로컬 상태를 한 번에 확인하는 read-only operations CLI를 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `stockanalysis-operations local-runtime-status`가 로컬 runtime 상태 JSON을 출력한다.
  - env 파일 값과 API key, DB password, token은 절대 출력하지 않는다.
  - FastAPI/Next local endpoints는 선택적으로 probe한다.
  - report는 `launchctl`/LaunchAgents 실제 설치가 왜 계속 막혀 있는지 설명한다.
  - 실제 `launchctl`, LaunchAgents write/delete, 외부 scheduler 배포는 수행하지 않는다.

## Scope

- 포함:
  - `src/stockanalysis/operations/local_runtime_status.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_local_runtime_status_orchestrator.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_local_runtime_status_orchestrator.sh`
  - `docs/local-runtime-status-orchestrator.md`
  - `docs/plans/2026-05-20-local-runtime-status-orchestrator.md`
  - `docs/tasks/local-runtime-status-orchestrator/*`
  - `docs/local-first-runtime-direction.md`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 제외:
  - 서비스 시작/중지 automation
  - `launchctl` 실행
  - `~/Library/LaunchAgents` 쓰기/삭제
  - DB schema 변경
  - API/DTO 변경
  - broker/order behavior 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/local_runtime_status.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_local_runtime_status_orchestrator.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_local_runtime_status_orchestrator.sh`
  - `docs/local-runtime-status-orchestrator.md`
  - `docs/plans/2026-05-20-local-runtime-status-orchestrator.md`
  - `docs/tasks/local-runtime-status-orchestrator/contract.md`
  - `docs/tasks/local-runtime-status-orchestrator/handoff.md`
  - `docs/tasks/local-runtime-status-orchestrator/review.md`
  - `docs/local-first-runtime-direction.md`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_local_runtime_status_orchestrator.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-runtime-status-orchestrator`
  - `git diff --check`

## Done Criteria

- [x] Local runtime status CLI exists.
- [x] Tests prove secrets are not emitted.
- [x] Report explains why LaunchAgents remain blocked.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
