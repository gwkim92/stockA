# Professional Workspace CJK Copy Finalization V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the interrupted Korean/CJK wrapping cleanup while preserving investment semantics, responsive layout, and long-token resilience.

**Architecture:** Keep the fix presentation-only. Use component-scoped typography classes for Korean prose, preserve an explicit emergency break path for dynamic external tokens, and lock the news/cycle and professional-decision boundaries with focused tests before browser verification.

**Tech Stack:** Next.js 16.2.9, React 19, TypeScript, CSS modules/global CSS, Vitest, Testing Library, Playwright.

---

### Task 1: Freeze the Task Boundary

**Files:**
- Create: `docs/tasks/professional-workspace-cjk-copy-finalization-v1/contract.md`
- Create: `docs/tasks/professional-workspace-cjk-copy-finalization-v1/handoff.md`
- Create: `docs/plans/2026-07-11-professional-workspace-cjk-copy-finalization-v1.md`

**Step 1:** Record the branch, base commit, dirty-file scope, failed visual evidence, and no-order invariants.

**Step 2:** Run `git status --short --branch` and confirm the 31 existing frontend changes remain intact.

### Task 2: Lock the Semantic Boundaries with Failing Tests

**Files:**
- Modify: `apps/web/src/components/recommendation-professional-audit-panel.test.tsx`
- Modify: `apps/web/src/lib/presentation/research-view-models.test.ts`
- Modify or create a focused recommendation detail component test under `apps/web/src/`

**Step 1:** Add assertions that investor-facing output retains separate `뉴스` and `사이클` evidence wording and uses `전문 판단 입력` for the professional-decision gate.

**Step 2:** Add an assertion that the professional market-correlation paragraph receives a Korean-prose class rather than relying on inline styling alone.

**Step 3:** Run the focused Vitest files and confirm the new assertions fail against the current interrupted patch.

### Task 3: Apply the Minimal Copy and Wrapping Fix

**Files:**
- Modify: `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationMarketCorrelationsPanel.tsx`
- Modify: `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationQualityBoundaryPanel.module.css`
- Modify: `apps/web/src/app/recommendations/[recommendationId]/_components/RecommendationDetailDisclosure.module.css`
- Modify: affected recommendation presentation/model files in the current diff
- Modify: `apps/web/src/app/globals.css`

**Step 1:** Restore precise news/cycle and professional-decision wording.

**Step 2:** Replace fragmentary copy with concise full Korean sentences using a consistent register.

**Step 3:** Add component-scoped `text-wrap: pretty` and `word-break: keep-all` to prose containers that produced the screenshot defects.

**Step 4:** Keep or restore emergency wrapping for dynamic long-token containers; do not apply `overflow-wrap: normal` indiscriminately to shared external-data selectors.

**Step 5:** Run the focused tests and confirm they pass.

### Task 4: Verify Automated Frontend Behavior

**Files:**
- Modify if required: `apps/web/tests/e2e/investment-workspace.spec.ts`

**Step 1:** Run `npm test` and expect 19 or more test files to pass.

**Step 2:** Run `npm run typecheck` and expect exit 0.

**Step 3:** Run `npm run build` and expect all application routes to compile.

**Step 4:** Start the fixture-backed production server on `127.0.0.1:13003` and run all Playwright projects with one worker.

**Step 5:** Confirm the required routes have no console error, clipping, or horizontal overflow.

### Task 5: Run Fresh Visual QA

**Files:**
- Update: `docs/tasks/professional-workspace-cjk-copy-finalization-v1/handoff.md`

**Step 1:** Capture `/cycle-map`, summary recommendation, professional recommendation, `/stocks/AAPL`, and `/stocks/SPY` at 375px, 768px, and 1280px after the final source edit.

**Step 2:** Dispatch independent design-system/functional and CJK-precision reviewers over all 15 captures.

**Step 3:** If either reviewer returns `REVISE` or `FAIL`, fix only the located root cause and repeat the full capture set.

**Step 4:** Record the final PASS evidence and any explicitly unverified state in the handoff.

### Task 6: Final Verification and Commit

**Files:**
- Update: `docs/tasks/professional-workspace-cjk-copy-finalization-v1/handoff.md`

**Step 1:** Run the frontend API contract, roadmap, AWH task, and `git diff --check` verification commands.

**Step 2:** Inspect `git diff --stat` and ensure no backend/scoring/order file changed.

**Step 3:** Stage only the intended tracked source, tests, and task documents; explicitly exclude QA output directories.

**Step 4:** Commit with a small task-specific message and leave deployment for the subsequent security/runtime gate.
