# Portfolio Review Managed Gates V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Distinguish unmanaged portfolio concentration problems from portfolio review decisions that are already captured, blocked from automatic orders, and waiting for outcome feedback.

**Architecture:** Keep benchmark drift and portfolio review decision data visible. Add deterministic `attention_required` and `managed_review_status` fields to the data-health payload. Open gates only for missing/unmanaged evidence, not for already recorded review decisions with a wait/action-router state.

**Tech Stack:** Python live adapter, Next.js TypeScript UI, unittest, AWH verification, EC2 smoke.

---

### Task 1: Contract

**Files:**
- Create: `docs/tasks/portfolio-review-managed-gates-v1/contract.md`
- Create: `docs/tasks/portfolio-review-managed-gates-v1/handoff.md`
- Create: `docs/tasks/portfolio-review-managed-gates-v1/review.md`

**Steps:**
- Record scope and invariants.
- Explicitly state no recommendation weight, portfolio position, benchmark, or order changes.

### Task 2: Backend Gate Policy

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add helpers that classify benchmark drift and portfolio review history as managed when review decisions exist and the action router is waiting for the outcome window.
- Continue opening gates for missing benchmark composition, stale/partial benchmark source, missing history, missing router, contradictions, or unsafe action router states.
- Add tests proving the current fixture state no longer opens those two gates, while unmanaged cases still do.

### Task 3: Frontend Copy

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/app/data-health/page.tsx`

**Steps:**
- Add the new payload fields to TypeScript types.
- Render managed review copy such as "검토 이력 관리 중" rather than "확인 필요".

### Task 4: Verification And EC2

**Commands:**
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-review-managed-gates-v1`

**EC2 smoke:**
- Pull branch, run focused verification, rebuild Next.js, restart services.
- Confirm `/api/data-health` no longer opens benchmark/review-history gates when current decisions are managed and read-only.
