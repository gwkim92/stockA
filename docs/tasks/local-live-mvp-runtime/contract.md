# Task Contract

## Task

- 이름: local-live-mvp-runtime
- 요청: local live MVP 구동을 위한 Python runtime, repo-outside env, FastAPI/Next/data-operations smoke 준비와 scheduler exact-command blocker 수정.
- 담당: Codex
- 날짜: 2026-05-16

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: Python 3.13 runtime boundary와 repo-outside local env가 준비되고, 실제 host scheduler activation 전 차단 버그인 quoted `~` command preview가 제거되며, 가능한 로컬 smoke 결과와 남은 차단점이 기록된다.

## Why

- 현재 프로젝트는 코드와 검증 기반은 있으나 실제 프로세스가 도는 상태가 아니다.
- FastAPI deps, Postgres runtime, repo-outside env, launchd command preview가 local live MVP의 직접 차단점이다.
- scheduler는 안전 게이트가 유지되어야 하므로 실제 `launchctl` 실행보다 단발 DB/API/UI smoke를 먼저 증명한다.

## Scope

- 포함:
  - Python 3.13 venv/runtime readiness 확인
  - repo-outside local runtime env 준비
  - scheduler activation request command preview를 shell-safe `$HOME` path로 수정
  - 관련 unit/verification script 갱신
  - FastAPI/Next/data-operations smoke 시도와 차단점 기록
  - handoff/roadmap/verification 기록
- 제외:
  - 실제 `launchctl bootstrap`, `kickstart`, `print` 실행
  - `~/Library/LaunchAgents` 쓰기
  - production secret 생성 또는 commit
  - DB schema 변경
  - AI/RAG/eval 구현
  - 페이퍼 거래 또는 실거래 구현
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/scheduler_activation_request.py`
  - scheduler activation request 관련 tests/verification scripts
  - local live MVP task docs
  - roadmap/verification/handoff 문서
- 수정 금지 파일:
  - `db/migrations/`
  - repo-inside env/secrets
  - host LaunchAgents path
  - benchmark/scoring/evaluation split
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -c "import fastapi, uvicorn, psycopg, httpx"`
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_scheduler_activation_request -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_live_scheduler_activation_request.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `cd apps/web && npm run typecheck && npm run build`
  - `git diff --check`

## Completion Criteria

- [ ] venv dependency import succeeds.
- [ ] generated scheduler activation commands use `$HOME/Library/LaunchAgents`, not quoted `~/Library/LaunchAgents`.
- [ ] verification scripts prove no `launchctl` is executed by repo scripts.
- [ ] frontend typecheck/build passes.
- [ ] FastAPI/data-operations smoke either passes or records concrete environment blocker.
- [ ] handoff records exact runtime kit paths, commands run, and remaining blockers.

## Risks

- Docker/Postgres may be unavailable on the host.
- Network may block dependency installation without approval.
- Local fixture env can prove runtime wiring but not real provider reachability.
- Actual recurring jobs remain inactive until explicit manual host activation.
