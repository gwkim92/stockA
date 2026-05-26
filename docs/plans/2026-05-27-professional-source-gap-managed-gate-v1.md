# Professional Source Gap Managed Gate V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Treat already-guarded professional source blockers as managed source limitations instead of unresolved operating gates.

**Architecture:** Keep the full `professional_source_gap_prioritization` payload visible, but add a deterministic `attention_required` policy that only opens `professional_source_gap_attention` when a gap is still actionable or unsafe. Durable source exclusions that already block professional decision use and paper validation remain visible as source limitations, not as an open gate.

**Tech Stack:** Python live adapter, Next.js TypeScript types/UI, unittest, AWH task verification.

---

### Task 1: Task Contract

**Files:**
- Create: `docs/tasks/professional-source-gap-managed-gate-v1/contract.md`
- Create: `docs/tasks/professional-source-gap-managed-gate-v1/handoff.md`
- Create: `docs/tasks/professional-source-gap-managed-gate-v1/review.md`

**Steps:**
- Record mutable surface, invariants, and verification commands.
- State explicitly that the task is visibility/gate policy only: no score, benchmark, position, or order changes.

### Task 2: Gate Policy

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add a helper that inspects built professional source gap rows.
- Return `attention_required=false` when all gaps are either durable source blockers already blocked from professional/paper use or fund-company-model-not-applicable rows with fund analysis path.
- Keep `attention_required=true` for unguarded source blockers, coverage gaps, fund source gaps, or gaps that still feed professional decisions.
- Update frontend contract tests for both managed and unguarded cases.

### Task 3: UI Copy

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/app/data-health/page.tsx`

**Steps:**
- Add `attention_required` to the TypeScript type.
- Render managed source blockers with a lower-severity explanation, not as "broken" data.

### Task 4: Verification And Deploy

**Commands:**
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task professional-source-gap-managed-gate-v1`

**EC2 smoke:**
- Pull the branch.
- Run compile/typecheck/focused tests.
- Restart FastAPI/Next.js.
- Confirm `/api/data-health` no longer includes `professional_source_gap_attention` when all current source blockers are safely guarded, while `professional_source_gap_prioritization` still exposes EROK.
