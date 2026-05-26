# Recommendation Professional Decision Waterfall V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 추천 상세를 거시·뉴스·기업·재무·밸류에이션·포지션·thesis·페이퍼 검증이 이어지는 전문 투자 검토서로 만든다.

**Architecture:** 새 schema를 만들지 않고 기존 recommendation detail live state를 조합해 `professional_decision_waterfall` DTO를 만든다. Next.js 추천 상세 화면은 backend DTO를 우선 렌더링하고 기존 세부 섹션은 증거 drill-down으로 유지한다.

**Tech Stack:** Python live adapter, unittest fixture executor, TypeScript DTO, Next.js App Router Server Component.

---

### Task 1: Contract And Current Shape

**Files:**
- Create: `docs/tasks/recommendation-professional-decision-waterfall-v1/contract.md`
- Create: `docs/tasks/recommendation-professional-decision-waterfall-v1/handoff.md`
- Create: `docs/plans/2026-05-26-recommendation-professional-decision-waterfall-v1.md`
- Inspect: `src/stockanalysis/frontend/live_adapter.py`
- Inspect: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`

**Step 1:** Confirm the existing recommendation detail fields already include score components, equity research, industry position, evidence trace, evidence review, and outcome.

**Step 2:** Keep scope read-only and explicitly exclude recommendation weight changes, order quantities, broker submit, and schema changes.

### Task 2: Backend DTO

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Step 1:** Add `professional_decision_waterfall` to `build_live_recommendation_detail_response`.

**Step 2:** Build helper functions that derive eight steps:
- `macro_cycle`
- `news_ai`
- `business_competition`
- `financial_quality`
- `valuation`
- `thesis`
- `position_sizing`
- `paper_validation`

**Step 3:** Ensure the top-level waterfall and every step remain read-only:
- `automatic_order_allowed=false`
- `broker_submit_allowed=false`
- `order_boundary=read_only_no_order`

**Step 4:** Add unit assertions for status, step order, position sizing facts, and order boundary.

### Task 3: Frontend Contract And Rendering

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/korean-labels.ts`
- Modify: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`

**Step 1:** Add `ProfessionalDecisionWaterfall` and `ProfessionalDecisionStep` types.

**Step 2:** Map `data.professional_decision_waterfall.steps` into `ProfessionalResearchFlow` steps.

**Step 3:** Use backend summary/footer so the page follows one authoritative decision order.

**Step 4:** Keep existing detailed sections as drill-down, not as competing navigation.

### Task 4: Roadmap And Verification

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/recommendation-professional-decision-waterfall-v1/handoff.md`

**Step 1:** Update immediate next task after completion.

**Step 2:** Run focused backend test, adapter suite, full unittest, compileall, Next typecheck/build, roadmap verifier, AWH verify, and diff check.

**Step 3:** Deploy to EC2, restart FastAPI/Next.js, and smoke `/api/recommendations/{id}` plus `/recommendations/{id}` through `http://127.0.0.1:13000`.
