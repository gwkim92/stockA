# Thesis Lifecycle Professional Gates V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Thesis 상세가 전문 투자 검토 gate를 통해 buy case, catalyst, risk, invalidation, valuation, review cadence, evidence freshness를 강제 점검하게 만든다.

**Architecture:** 새 schema를 만들지 않고 기존 thesis detail live state의 `lifecycle`, `evidence`, `evidence_review`, `latest_review`를 조합해 `professional_lifecycle_gates` DTO를 만든다. Next.js thesis 상세 화면은 이 DTO를 상단 gate section으로 렌더링하고 기존 lifecycle/evidence 섹션은 drill-down으로 유지한다.

**Tech Stack:** Python live adapter, unittest fixture executor, TypeScript DTO, Next.js App Router Server Component.

---

### Task 1: Contract And Current Shape

**Files:**
- Create: `docs/tasks/thesis-lifecycle-professional-gates-v1/contract.md`
- Create: `docs/tasks/thesis-lifecycle-professional-gates-v1/handoff.md`
- Create: `docs/plans/2026-05-26-thesis-lifecycle-professional-gates-v1.md`
- Inspect: `src/stockanalysis/frontend/live_adapter.py`
- Inspect: `apps/web/src/app/theses/[thesisId]/page.tsx`

**Step 1:** Confirm existing thesis detail already returns lifecycle and evidence.

**Step 2:** Keep the new slice read-only and explicitly exclude recommendation weight changes, thesis edit APIs, orders, and schema changes.

### Task 2: Backend DTO

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Step 1:** Add `observed_at` to thesis evidence rows and payloads.

**Step 2:** Add `professional_lifecycle_gates` with gates:
- `buy_case`
- `catalysts`
- `risks`
- `invalidation`
- `valuation`
- `review_cadence`
- `evidence_freshness`
- `order_boundary`

**Step 3:** Ensure every gate remains read-only:
- `automatic_order_allowed=false`
- `broker_submit_allowed=false`
- `order_boundary=read_only_no_order`

**Step 4:** Add unit assertions for gate order, stale evidence warning, review cadence warning, and order boundary.

### Task 3: Frontend Contract And Rendering

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/korean-labels.ts`
- Modify: `apps/web/src/app/theses/[thesisId]/page.tsx`

**Step 1:** Add `ProfessionalLifecycleGates` and `ProfessionalLifecycleGate` types.

**Step 2:** Render the gate summary near the top of the thesis detail page.

**Step 3:** Keep the existing lifecycle section as detail drill-down rather than competing summary.

### Task 4: Roadmap And Verification

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/thesis-lifecycle-professional-gates-v1/handoff.md`

**Step 1:** Update immediate next task after completion.

**Step 2:** Run focused backend test, adapter suite, full unittest, compileall, Next typecheck/build, roadmap verifier, AWH verify, and diff check.

**Step 3:** Deploy to EC2, restart FastAPI/Next.js, and smoke `/api/theses/{id}` plus `/theses/{id}` through `http://127.0.0.1:13000`.
