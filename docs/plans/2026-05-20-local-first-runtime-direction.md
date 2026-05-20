# Local First Runtime Direction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 외부 서버 배포를 즉시 목표에서 내리고, 현재 프로젝트의 실행 기준을 local-first 투자 운영 시스템으로 고정한다.

**Architecture:** Next.js와 FastAPI는 로컬 화면/읽기 API 프로세스로 유지한다. 데이터 수집과 AI 분석은 웹 요청 서버 내부가 아니라 `stockanalysis-operations` worker/CLI가 실행하며, 외부 server scheduler는 미래 운영 옵션으로만 남긴다.

**Tech Stack:** Markdown decision docs, Next.js route copy, existing `stockanalysis-operations` backend boundary, AWH task harness.

---

### Task 1: Task Boundary

**Files:**
- Create: `docs/tasks/local-first-runtime-direction/contract.md`
- Create: `docs/tasks/local-first-runtime-direction/handoff.md`
- Create: `docs/tasks/local-first-runtime-direction/review.md`

**Step 1: Write the task contract**

Define the task as a direction correction from external server scheduler selection to local-first runtime.

**Step 2: Capture out-of-scope**

Exclude external deployment, `launchctl` execution, LaunchAgents writes, schema changes, auth changes, and broker/order execution.

**Step 3: Add handoff and review placeholders**

Record expected verification commands and remaining risks.

### Task 2: Architecture Decision Document

**Files:**
- Create: `docs/local-first-runtime-direction.md`
- Modify: `docs/server-side-scheduler-architecture.md`

**Step 1: Write the local-first decision**

Explain the difference between the local web UI/API processes and external production server deployment.

**Step 2: Reframe server-side scheduler**

Keep server-side scheduler as future optional operating mode, not the immediate next implementation.

**Step 3: Document execution modes**

Document three modes: manual local run, local scheduled run, and future external scheduler.

### Task 3: Roadmap And Agent Rules

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`

**Step 1: Update immediate next task**

Set immediate next task to `local-first-runtime-direction`.

**Step 2: Preserve safety boundaries**

Keep `launchctl` and LaunchAgents mutation forbidden without explicit approval.

**Step 3: Clarify next implementation sequence**

Next implementation should improve local run orchestration and data-health visibility before external deployment.

### Task 4: Data Health Wording

**Files:**
- Modify: `apps/web/src/app/data-health/page.tsx`

**Step 1: Replace external-server-first wording**

Change copy from "server scheduler deployment" to "local runner / operations worker".

**Step 2: Keep technical boundary**

Do not imply FastAPI/Next runs long data jobs. The worker still owns data operations.

**Step 3: Verify browser wording**

Open `/data-health` and verify it no longer presents external server scheduler as the immediate target.

### Task 5: Verification

**Files:**
- Update: `docs/tasks/local-first-runtime-direction/handoff.md`
- Update: `docs/tasks/local-first-runtime-direction/review.md`

**Step 1: Run frontend checks**

Run `cd apps/web && npm run typecheck` and `cd apps/web && npm run build`.

**Step 2: Run browser smoke**

Verify `/data-health` renders local-first wording and no console errors.

**Step 3: Run task harness**

Run `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-first-runtime-direction`.

**Step 4: Run whitespace check**

Run `git diff --check`.
