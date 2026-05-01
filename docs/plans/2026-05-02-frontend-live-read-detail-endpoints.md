# Frontend Live Read Detail Endpoints Implementation Plan

**Goal:** recommendation, thesis, AI evidence, source document detail endpoints를 canonical Postgres live read DTO로 확장한다.

**Architecture:** 기존 `src/stockanalysis/frontend/live_adapter.py`의 read-only adapter 패턴을 유지한다. 각 endpoint는 path identifier를 보수적으로 해석하고, SQL renderer가 contract-shaped JSON object를 반환하며, Python builder가 opaque ID/timestamp/number normalization을 담당한다.

**Tech Stack:** Python stdlib, Postgres JSON builders, existing `PsqlCommandExecutor`, `unittest`, agent-work-harness.

---

### Task 1: Task Harness

**Files:**
- Create: `docs/tasks/frontend-live-read-detail-endpoints/contract.md`
- Create: `docs/tasks/frontend-live-read-detail-endpoints/plan.md`
- Create: `docs/tasks/frontend-live-read-detail-endpoints/handoff.md`
- Create: `docs/tasks/frontend-live-read-detail-endpoints/review.md`

**Steps:**
- Record scope: recommendation detail, thesis detail, AI evidence detail, source document detail.
- Exclude DB schema, scoring, benchmark, auth/RBAC, and write APIs.
- Record validation commands.

### Task 2: Live Adapter Routes

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Route `/api/recommendations/:id`.
- Route `/api/theses/:id`.
- Route `/api/ai-evidence/:id`.
- Route `/api/source-documents/:id`.
- Keep unsupported live paths rejected.

### Task 3: SQL Renderers And DTO Builders

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add recommendation detail SQL from `signal.recommendation`, `signal.recommendation_batch`, `signal.recommendation_score_component`, `performance.recommendation_outcome`, and thesis link.
- Add thesis detail SQL from `signal.investment_thesis`, latest `signal.thesis_review`, related recommendation/outcome/event evidence.
- Add AI evidence SQL from `ai.extraction_artifact`, `ai.model_invocation`, source document, event, classification/instrument impact, and chunks.
- Add source document SQL from `ingest.source_document`, `ai.document_chunk`, linked extraction artifacts/events, and retrieval run.
- Normalize DTO fields with helper builders.

### Task 4: Verification And Docs

**Files:**
- Modify: `docs/frontend-api-adapter.md`
- Modify: `docs/frontend-api-contract.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/tasks/frontend-live-read-detail-endpoints/handoff.md`
- Modify: `docs/tasks/frontend-live-read-detail-endpoints/review.md`

**Steps:**
- Update supported live endpoint list.
- Run `bash scripts/verify_frontend_live_read_adapter.sh`.
- Run `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`.
- Run `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-detail-endpoints`.
- Run placeholder scan and `git diff --check`.
