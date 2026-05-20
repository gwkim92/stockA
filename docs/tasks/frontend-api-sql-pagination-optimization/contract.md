# Task Contract

## Task

- 이름: frontend-api-sql-pagination-optimization
- 요청: frontend live list endpoint의 response-boundary pagination을 SQL-level bounded window로 최적화한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: live read list endpoint는 기존 `limit`/opaque `cursor` contract를 유지하면서 SQL/report boundary에서 `limit + 1`과 cursor offset을 적용해 한 페이지와 `has_more` 판정용 초과 row만 읽는다.

## Why

- `frontend-api-pagination-conventions`는 contract를 고정했지만 첫 slice는 response-boundary slicing이었다.
- list payload가 커질수록 DB에서 전체 JSON 배열을 만든 뒤 Python에서 자르는 방식은 API latency와 memory risk를 키운다.
- 프론트 productization 전에 live read의 데이터 로딩 경계를 먼저 줄여야 한다.

## Scope

- 포함:
  - SQL pagination task docs
  - live adapter list endpoint SQL/report window 적용
  - `limit + 1` read와 top-level `pagination` metadata 유지
  - cycles/events/performance outcomes/remediation tickets/portfolio coverage list response 검증
  - verification script와 project roadmap/verification doc 업데이트
- 제외:
  - DB schema/index migration
  - true keyset/seek cursor v2
  - cursor wire format 변경
  - benchmark/evaluation split 변경
  - scoring formula 변경
  - auth/RBAC/write endpoint
  - frontend UI table 구현
  - broker/order flow
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/pagination.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/signal/portfolio_remediation_ticket.py`
  - `src/stockanalysis/performance/coverage.py`
  - `tests/test_frontend_pagination.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_portfolio_remediation_ticket.py`
  - `tests/test_portfolio_outcome_coverage_report.py`
  - `docs/frontend-api-sql-pagination-optimization.md`
  - `scripts/verify_frontend_api_sql_pagination_optimization.sh`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-sql-pagination-optimization.md`
  - `docs/tasks/frontend-api-sql-pagination-optimization/`
- 수정 금지 파일:
  - `db/migrations/`
  - `apps/web/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `python3 -m py_compile src/stockanalysis/frontend/pagination.py src/stockanalysis/frontend/live_adapter.py src/stockanalysis/signal/portfolio_remediation_ticket.py src/stockanalysis/performance/coverage.py`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_pagination tests.test_frontend_live_adapter tests.test_portfolio_remediation_ticket tests.test_portfolio_outcome_coverage_report -v`
  - `bash scripts/verify_frontend_api_sql_pagination_optimization.sh`
  - `bash scripts/verify_frontend_api_pagination_conventions.sh`
  - `bash scripts/verify_frontend_api_server.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-sql-pagination-optimization`
  - `git diff --check`

## Deliverables

- SQL/report window helper and live adapter integration
- Coverage/remediation report pagination support
- Targeted unit tests
- Verification script
- Updated docs/task handoff/review

## Completion Criteria

- [x] list endpoint live reads request `limit + 1` at SQL/report boundary.
- [x] opaque cursor offset is pushed into SQL/report boundary.
- [x] response shape and existing pagination metadata remain backward compatible.
- [x] non-list endpoint pagination rejection remains unchanged.
- [x] coverage/performance summaries remain computed from the full filtered set, not only the displayed page.
- [x] Verification commands pass and evidence is recorded.

## Risks

- This slice keeps the existing v1 offset cursor wire format; deep page performance can still degrade compared with keyset pagination.
- SQL query plans may still need future composite indexes, but schema/index changes are deliberately excluded from this task.
