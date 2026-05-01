# Apps Web Scaffold Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create the first `apps/web` Next.js App Router frontend shell for the investment cockpit, backed only by the local frontend fixture server contract.

**Architecture:** The app uses React Server Components for read views and fetches contract-shaped DTOs from `STOCKANALYSIS_FRONTEND_API_BASE_URL`. It keeps all reads server-side, avoids browser secrets, and remains fixture-only until live DB read adapters and auth are implemented.

**Tech Stack:** Next.js 16.2.4, React 19.2.5, TypeScript 6.0.3, CSS modules/global CSS, Node 24.6.0, npm 11.5.2.

---

### Task 1: Task Boundary

**Files:**
- Create: `docs/tasks/apps-web-scaffold/contract.md`
- Create: `docs/tasks/apps-web-scaffold/plan.md`
- Create: `docs/tasks/apps-web-scaffold/handoff.md`
- Create: `docs/tasks/apps-web-scaffold/review.md`

**Step 1: Define scope**

Document fixture-only Next.js scaffold, initial routes, data client, docs, and verification.

**Step 2: Define exclusions**

Exclude live DB reads, write APIs, auth/RBAC, broker integration, and production deployment.

### Task 2: Next App Skeleton

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.mjs`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/next-env.d.ts`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/remediation/page.tsx`
- Create: `apps/web/src/app/data-health/page.tsx`
- Create: `apps/web/src/app/cycles/page.tsx`
- Create: `apps/web/src/app/loading.tsx`
- Create: `apps/web/src/app/error.tsx`
- Create: `apps/web/src/app/not-found.tsx`
- Create: `apps/web/src/app/globals.css`
- Create: `apps/web/src/lib/frontend-api.ts`
- Create: `apps/web/src/lib/types.ts`

**Step 1: Add dependencies**

Use current npm registry versions checked during implementation.

**Step 2: Add RSC data client**

Fetch exact fixture API paths from `STOCKANALYSIS_FRONTEND_API_BASE_URL`, defaulting to `http://127.0.0.1:8765`.

**Step 3: Add route shell**

Implement `/`, `/remediation`, `/data-health`, and `/cycles` as read-only Server Component pages.

### Task 3: Design System

**Files:**
- Create: `apps/web/src/app/globals.css`

**Step 1: Define visual direction**

Use editorial operating-room visual language: paper background, ink text, amber risk, blue evidence, green validated, red broken thesis.

**Step 2: Add responsive layout**

Support desktop cockpit density and mobile single-column reading.

### Task 4: Verification Updates

**Files:**
- Modify: `scripts/verify_frontend_architecture.sh`
- Modify: `scripts/verify_frontend_api_contract.sh`
- Modify: `scripts/verify_frontend_api_adapter.sh`
- Modify: `scripts/verify_frontend_fixture_server.sh`
- Create: `scripts/verify_apps_web_scaffold.sh`

**Step 1: Remove obsolete absence checks**

Earlier frontend foundation tasks should no longer fail because `apps/web` exists.

**Step 2: Add web scaffold verification**

Run npm install check, TypeScript check, Next build with fixture server running, and route smoke where feasible.

### Task 5: Docs

**Files:**
- Create: `docs/apps-web-scaffold.md`
- Modify: `README.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/frontend-fixture-server.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/apps-web-scaffold/handoff.md`
- Modify: `docs/tasks/apps-web-scaffold/review.md`

**Step 1: Document local development**

Document starting fixture server and web dev server.

**Step 2: Document boundaries**

Document read-only fixture mode and deferred live API/auth/write boundaries.

### Task 6: Final Verification

Run:

```bash
bash -n scripts/verify_apps_web_scaffold.sh
bash scripts/verify_apps_web_scaffold.sh
bash scripts/verify_frontend_fixture_server.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task apps-web-scaffold
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```

Record evidence in handoff and review.
