# Task Contract

## Task

- 이름: frontend-api-pagination-conventions
- 요청: frontend read-only list endpoint의 pagination/cursor/limit/error contract를 고정한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: list endpoint는 `limit`, `cursor`, top-level `pagination.next_cursor` 규칙을 갖고, fixture/live/FastAPI runtime이 같은 validation/error boundary를 적용한다.

## Why

- live read completeness와 API server boundary는 갖췄지만 list endpoint가 커질 때 사용할 pagination 규칙이 아직 "later" 상태다.
- UI 확장 전에 API contract가 먼저 정해져야 프론트 테이블, fetch adapter, live SQL 최적화가 흔들리지 않는다.

## Scope

- 포함:
  - pagination convention 문서
  - list endpoint spec
  - opaque cursor encode/decode helper
  - `limit` validation
  - `cursor` validation
  - top-level `pagination` response metadata
  - fixture/live/FastAPI/stdlib fixture server error mapping
  - DTO examples/type update
  - verification script
  - docs/task handoff 갱신
- 제외:
  - DB schema 변경
  - SQL-level cursor seek pagination
  - benchmark/evaluation split 변경
  - scoring formula 변경
  - write endpoint
  - full auth/RBAC/session/actor identity
  - frontend UI table implementation
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/pagination.py`
  - `src/stockanalysis/frontend/api_adapter.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/api_server.py`
  - `src/stockanalysis/frontend/fixture_server.py`
  - `tests/test_frontend_pagination.py`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_frontend_api_server.py`
  - `docs/api/frontend/examples/*.json`
  - `apps/web/src/lib/types.ts`
  - `docs/frontend-api-pagination-conventions.md`
  - `scripts/verify_frontend_api_pagination_conventions.sh`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-api-server.md`
  - `docs/frontend-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-pagination-conventions.md`
  - `docs/tasks/frontend-api-pagination-conventions/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - production env/secrets
  - deployment configs
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `python3 -m py_compile src/stockanalysis/frontend/pagination.py`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_pagination tests.test_frontend_api_adapter tests.test_frontend_live_adapter tests.test_frontend_api_server -v`
  - `bash scripts/verify_frontend_api_pagination_conventions.sh`
  - `bash scripts/verify_frontend_api_contract.sh`
  - `bash scripts/verify_frontend_api_server.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-pagination-conventions`
  - `git diff --check`

## Deliverables

- Pagination helper
- Fixture/live/API server pagination validation
- DTO examples with pagination metadata
- Pagination convention docs
- Verification script
- Updated roadmap/handoff/review

## Completion Criteria

- [x] `limit` accepts integers `1..100`.
- [x] invalid `limit` returns stable `FrontendPaginationInvalid` error.
- [x] valid `cursor` resumes from an opaque offset cursor.
- [x] invalid `cursor` returns stable `FrontendPaginationInvalid` error.
- [x] non-list endpoint rejects pagination params.
- [x] list response examples include top-level `pagination`.
- [x] existing `data` fields remain backward compatible.
- [x] Verification commands pass and evidence is recorded.

## Risks

- This slice applies response-boundary pagination, not SQL-level cursor seek scans.
- Cursor format is intentionally opaque but may need versioned migration if SQL-level cursors replace offset payloads.
