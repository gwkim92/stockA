# Frontend API Runtime Boundary Implementation Plan

**Goal:** local read-only frontend HTTP runtime에 production-facing boundary policy를 추가해 source mode, host exposure, CORS, auth seam, error metadata를 명확히 분리한다.

**Architecture:** 기존 `fixture_server.py`는 계속 stdlib HTTP server로 유지하되, runtime policy를 별도 module로 분리한다. policy는 local/prod profile, source mode, allowed origin, read-token auth seam, startup guard를 담당하고 server는 이를 적용만 한다.

**Tech Stack:** Python stdlib `http.server`, dataclass policy object, environment variables, `unittest`, agent-work-harness.

---

### Task 1: Task Harness

**Files:**
- Create: `docs/tasks/frontend-api-runtime-boundary/contract.md`
- Create: `docs/tasks/frontend-api-runtime-boundary/plan.md`
- Create: `docs/tasks/frontend-api-runtime-boundary/handoff.md`
- Create: `docs/tasks/frontend-api-runtime-boundary/review.md`

**Steps:**
- Record scope: runtime boundary only.
- Exclude write APIs, broker/order flow, full auth/RBAC implementation, DB schema changes.
- Record validation commands.

### Task 2: Runtime Policy

**Files:**
- Create: `src/stockanalysis/frontend/runtime_policy.py`
- Test: `tests/test_frontend_fixture_server.py`

**Steps:**
- Add `FrontendRuntimePolicy`.
- Add profile validation for local and production.
- Reject unauthenticated non-loopback local exposure.
- Require read-token auth, explicit allowed origin, and DB command for production live/auto source.

### Task 3: Server Integration

**Files:**
- Modify: `src/stockanalysis/frontend/fixture_server.py`
- Test: `tests/test_frontend_fixture_server.py`
- Modify: `pyproject.toml`

**Steps:**
- Accept runtime policy CLI options.
- Add auth guard for read endpoints.
- Add CORS/header policy.
- Add startup/health metadata.
- Add `stockanalysis-frontend-runtime-server` alias while keeping existing fixture server entrypoint.

### Task 4: Verification And Docs

**Files:**
- Create: `scripts/verify_frontend_api_runtime_boundary.sh`
- Create: `docs/frontend-api-runtime-boundary.md`
- Modify: `docs/frontend-fixture-server.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/frontend-api-adapter.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `README.md`

**Steps:**
- Document env vars and boundary decisions.
- Run fixture server verification.
- Run runtime boundary verification.
- Run AWH, placeholder scan, and diff check.
