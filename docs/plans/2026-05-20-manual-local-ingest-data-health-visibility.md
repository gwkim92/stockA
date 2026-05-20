# Manual Local Ingest Data Health Visibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show the latest manual market/news/AI local ingest smoke summary in `/api/data-health` and the Next.js `/data-health` cockpit without exposing secrets.

**Architecture:** The operations CLI writes a secret-free summary JSON only when an explicit repo-outside `--output` path is provided. The read-only frontend adapter loads that summary from `STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT`, sanitizes it, and adds an additive `manual_local_ingest_smoke` field to the data-health DTO. The UI renders this as operator evidence, not as proof that automatic scheduling is enabled.

**Tech Stack:** Python stdlib JSON/path helpers, existing `stockanalysis-operations` CLI, FastAPI live adapter DTO, Next.js Server Components, TypeScript DTO types.

---

### Task 1: Contract and Roadmap Guardrail

**Files:**
- Create: `docs/tasks/manual-local-ingest-data-health-visibility/contract.md`
- Modify: `AGENTS.md`
- Modify: `docs/project-execution-roadmap.md`

**Steps:**
- Record the new task scope and keep actual `launchctl`/LaunchAgents mutation forbidden.
- Update the immediate next task from `manual-local-ingest-smoke` to this visibility slice.
- Keep the decision explicit: this is local-first operator visibility, not external server scheduler deployment.

### Task 2: Summary Report Output and Sanitized Loader

**Files:**
- Modify: `src/stockanalysis/operations/manual_local_ingest_smoke.py`
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_manual_local_ingest_smoke.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
- Add `STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT` as the repo-outside summary path env name.
- Add a sanitized visibility builder that returns `not_configured`, `missing_report`, `invalid_report`, or a safe summary from a valid `manual_local_ingest_smoke` report.
- Add `--output` to `manual-local-ingest-smoke`; require repo-outside output paths and write the report there.
- Verify no DB URL, API key, bearer token, or raw secret-like marker can appear in the summary.

### Task 3: Data Health API and Frontend

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/korean-labels.ts`
- Modify: `apps/web/src/app/data-health/page.tsx`
- Modify: `docs/api/frontend/examples/data-health.json`
- Modify: `docs/frontend-api-contract.md`

**Steps:**
- Add `data.manual_local_ingest_smoke` to `/api/data-health`.
- Display smoke status, execution mode, generated time, planned jobs, artifact run summaries, and next action in Korean.
- Keep all paths secret-free except artifact/report paths that are explicitly repo-outside operator evidence and contain no credentials.

### Task 4: Verification and Handoff

**Files:**
- Create: `scripts/verify_manual_local_ingest_data_health_visibility.sh`
- Create: `docs/tasks/manual-local-ingest-data-health-visibility/handoff.md`
- Create: `docs/tasks/manual-local-ingest-data-health-visibility/review.md`

**Steps:**
- Run focused Python unit tests and the new verify script.
- Run frontend typecheck/build if UI types changed.
- Run project roadmap verification and AWH for the new task.
- Record remaining risk: full `--execute` live provider/DB smoke still consumes quota and must be run deliberately.
