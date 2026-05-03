# Frontend API Pagination Conventions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Read-only frontend list endpoints에 `limit`, `cursor`, `next_cursor` pagination contract를 고정하고 fixture/live/FastAPI runtime에서 같은 validation/error behavior를 제공한다.

**Architecture:** 기존 DTO `data` shape는 유지하고, collection responses에 optional top-level `pagination` metadata를 추가한다. DB schema, SQL benchmark, scoring, auth/RBAC, write APIs는 바꾸지 않고 response-boundary pagination부터 적용한다.

**Tech Stack:** Python stdlib URL parsing/base64 JSON cursors, FastAPI error boundary, unittest, shell verification.

---

### Task 1: Lock Task Contract

**Files:**
- Create: `docs/tasks/frontend-api-pagination-conventions/contract.md`
- Create: `docs/tasks/frontend-api-pagination-conventions/plan.md`
- Create: `docs/tasks/frontend-api-pagination-conventions/handoff.md`
- Create: `docs/tasks/frontend-api-pagination-conventions/review.md`

**Steps:**
1. Define list endpoints and collection keys.
2. Exclude DB schema, SQL-level cursor scans, write APIs, auth/RBAC, frontend UI changes.
3. List verification commands.

### Task 2: Add Pagination Helper

**Files:**
- Create: `src/stockanalysis/frontend/pagination.py`
- Test: `tests/test_frontend_pagination.py`

**Steps:**
1. Add `FrontendPaginationError`.
2. Add `FrontendPaginationParams` and opaque cursor encode/decode.
3. Add list endpoint specs for `tickets`, `cycle_states`, `events`, `positions`, and `outcomes`.
4. Add `apply_frontend_pagination(api_path, payload)`.
5. Validate `limit` as `1..100`, cursor as opaque v1 offset cursor, and reject pagination params on non-list paths.

### Task 3: Wire Fixture And Live Adapter

**Files:**
- Modify: `src/stockanalysis/frontend/api_adapter.py`
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `src/stockanalysis/frontend/api_server.py`
- Modify: `src/stockanalysis/frontend/fixture_server.py`
- Test: `tests/test_frontend_api_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`
- Test: `tests/test_frontend_api_server.py`

**Steps:**
1. Apply pagination after fixture payload load, including canonical matching when only `limit/cursor` differs.
2. Apply pagination after live payload construction.
3. Map `FrontendPaginationInvalid` to HTTP 400 in FastAPI and fixture server.
4. Verify invalid pagination uses stable error envelope.

### Task 4: Update DTO Examples And Types

**Files:**
- Modify: `docs/api/frontend/examples/remediation-tickets.json`
- Modify: `docs/api/frontend/examples/cycle-state-list.json`
- Modify: `docs/api/frontend/examples/event-list.json`
- Modify: `docs/api/frontend/examples/portfolio-coverage.json`
- Modify: `docs/api/frontend/examples/performance-outcomes.json`
- Modify: `apps/web/src/lib/types.ts`

**Steps:**
1. Add top-level `pagination` metadata to list response examples.
2. Add optional `pagination` to `ApiResponse<TData>` TypeScript type.
3. Preserve all existing `data` fields.

### Task 5: Update Docs And Verification

**Files:**
- Create: `docs/frontend-api-pagination-conventions.md`
- Create: `scripts/verify_frontend_api_pagination_conventions.sh`
- Modify: `docs/frontend-api-contract.md`
- Modify: `docs/frontend-api-server.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/frontend-api-pagination-conventions/handoff.md`
- Modify: `docs/tasks/frontend-api-pagination-conventions/review.md`

**Steps:**
1. Document collection endpoints, defaults, max limit, cursor opacity, no page-number rule.
2. Add pagination verification command.
3. Move immediate next task to API runtime metrics/log sink decision.
4. Record verification evidence.

### Task 6: Verify And Publish

**Commands:**
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_pagination tests.test_frontend_api_adapter tests.test_frontend_live_adapter tests.test_frontend_api_server -v`
- `bash scripts/verify_frontend_api_pagination_conventions.sh`
- `bash scripts/verify_frontend_api_contract.sh`
- `bash scripts/verify_frontend_api_server.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-pagination-conventions`
- `git diff --check`

**Steps:**
1. Run targeted unit tests.
2. Run contract and FastAPI smoke verification.
3. Run roadmap and AWH verification.
4. Commit, push, and open PR.
