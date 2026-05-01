# Task Contract

## Task

- 이름: frontend-api-adapter-foundation
- 요청: frontend API contract examples를 반환하는 read-only Python adapter를 만든다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: API path를 입력하면 `docs/api/frontend/contract-index.json`에 연결된 example JSON을 반환하는 adapter와 CLI가 존재하고 검증된다.

## Why

- frontend scaffold 전에 UI가 사용할 API-shaped payload를 안정적으로 제공해야 한다.
- 아직 live DB adapter를 만들기 전이라도 fixture adapter가 있으면 `apps/web` 개발과 browser smoke를 시작할 수 있다.

## Scope

- 포함:
  - frontend API contract loader
  - read-only fixture adapter
  - CLI list/get command
  - tests
  - verification script
  - docs/task handoff 갱신
- 제외:
  - actual HTTP API server
  - live DB query adapter
  - frontend scaffold
  - auth/RBAC
  - deployment config
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `pyproject.toml`
  - `docs/plans/2026-05-01-frontend-api-adapter-foundation.md`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/tasks/frontend-api-adapter-foundation/`
  - `docs/verification-plan.md`
  - `src/stockanalysis/frontend/`
  - `tests/test_frontend_api_adapter.py`
  - `scripts/verify_frontend_api_adapter.sh`
- 수정 금지 파일:
  - DB migrations
  - deployment secrets
  - frontend scaffold directories
- 검증에 사용할 명령:
  - `bash -n scripts/verify_frontend_api_adapter.sh`
  - `bash scripts/verify_frontend_api_adapter.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-adapter-foundation`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - frontend API adapter module
  - adapter CLI
  - adapter tests
  - adapter verification script
  - adapter docs
  - README/verification plan update
  - task contract/plan/handoff/review

## Completion Criteria

- [x] known API path가 linked example JSON을 반환한다.
- [x] unknown API path가 stable error JSON과 non-zero exit code를 반환한다.
- [x] CLI list command가 contract endpoints를 출력한다.
- [x] CLI get command가 response payload를 출력한다.
- [x] actual HTTP server는 생성하지 않는다.
- [x] actual frontend scaffold는 생성하지 않는다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Risks

- fixture adapter는 live DB freshness를 보장하지 않는다.
- exact path matching만 지원하므로 query normalization은 다음 단계에서 필요할 수 있다.
- HTTP server가 없으므로 browser fetch는 아직 직접 연결되지 않는다.
