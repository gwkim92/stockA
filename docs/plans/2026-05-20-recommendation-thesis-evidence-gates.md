# Recommendation Thesis Evidence Gates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show whether each recommendation and thesis has enough traceable evidence before a human treats it as investable.

**Architecture:** Do not change scoring, schema, broker flow, or LLM behavior. Add deterministic read-only evidence gate payloads at the frontend live adapter boundary from existing recommendation/thesis detail DTO state. Render those gates on the existing recommendation and thesis pages in Korean.

**Tech Stack:** Python stdlib, frontend live adapter DTOs, Next.js server components, TypeScript contract types, unittest, existing AWH harness.

---

### Task 1: Harness Contract

**Files:**
- Create: `docs/tasks/recommendation-thesis-evidence-gates/contract.md`
- Create: `docs/tasks/recommendation-thesis-evidence-gates/handoff.md`
- Create: `docs/tasks/recommendation-thesis-evidence-gates/review.md`

**Steps:**
- Define this as a read-only quality gate task.
- Exclude recommendation generation, benchmark changes, schema changes, LLM calls, broker/order writes, and scheduler activation.
- Record verification commands.

### Task 2: API Evidence Gates

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add recommendation `evidence_review` with summary and gates:
  - linked thesis exists.
  - score components exist.
  - AI/source evidence is linked to score components.
  - outcome measurement exists.
  - automatic order boundary remains blocked.
- Add thesis `evidence_review` with summary and gates:
  - source events exist.
  - performance outcome exists.
  - invalidation conditions exist.
  - latest human review exists.
  - broker/order boundary remains blocked.
- Keep all payloads secret-free and read-only.

### Task 3: TypeScript Contract

**Files:**
- Modify: `apps/web/src/lib/types.ts`

**Steps:**
- Add a shared evidence-review shape inline to recommendation and thesis detail data.
- Keep labels generic enough for future API reuse.

### Task 4: Recommendation/Thesis UI

**Files:**
- Modify: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- Modify: `apps/web/src/app/theses/[thesisId]/page.tsx`

**Steps:**
- Render a “근거 품질 점검” panel.
- Show pass/warning/blocked counts and human-readable next steps.
- Make clear that these gates are not order approval.

### Task 5: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-thesis-evidence-gates`
- Browser check: `/recommendations/AAPL-2024-11-01` and `/theses/AAPL-bootstrap-v1`
- `git diff --check`

### Done Criteria

- Recommendation detail API and UI show evidence gates.
- Thesis detail API and UI show evidence gates.
- The feature stays read-only and does not change scoring/trading/scheduler behavior.
- Handoff/review contain fresh verification evidence.
