# Server Side Scheduler Architecture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reframe scheduler activation from Mac LaunchAgents toward a server-managed scheduler/worker architecture.

**Architecture:** Keep `stockanalysis-operations` as the canonical job runner. Production scheduling should happen in a server/runtime scheduler that invokes operations jobs and writes run artifacts to Postgres/artifact storage; FastAPI remains read-only request serving, not a background job runner.

**Tech Stack:** Python `stockanalysis-operations`, Postgres `ops.pipeline_run`, FastAPI read-only API, Next.js cockpit, deployment scheduler/worker runtime.

---

### Task 1: Write Architecture Decision

**Files:**
- Create: `docs/server-side-scheduler-architecture.md`

**Step 1:** Explain why Mac LaunchAgents are local MVP only.

**Step 2:** Define target server-side architecture: scheduler, worker, Postgres, artifact store, FastAPI, Next.js.

**Step 3:** Define job ownership and failure handling.

**Step 4:** Define what remains out of scope: broker orders, write APIs, secrets in repo, web-server-in-process scheduler.

### Task 2: Update Operator UI Wording

**Files:**
- Modify: `apps/web/src/app/data-health/page.tsx`

**Step 1:** Remove wording that implies Mac host scheduler is the final operating model.

**Step 2:** Add a short server scheduler target model card.

**Step 3:** Keep current status clear: recent runs succeeded, recurring server scheduler is not deployed yet.

### Task 3: Update Project Direction

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`

**Step 1:** Add server-managed scheduler architecture as the fixed next direction before physical LaunchAgents activation.

**Step 2:** Preserve the guardrail that `launchctl` and LaunchAgents writes remain forbidden without explicit approval.

### Task 4: Record Harness State

**Files:**
- Create: `docs/tasks/server-side-scheduler-architecture/contract.md`
- Create: `docs/tasks/server-side-scheduler-architecture/handoff.md`
- Create: `docs/tasks/server-side-scheduler-architecture/review.md`

**Step 1:** Document mutable surface.

**Step 2:** Record verification commands.

### Task 5: Verify

**Commands:**
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/data-health`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-side-scheduler-architecture`
- `git diff --check`

**Expected:** All pass. No `launchctl` command is executed.
