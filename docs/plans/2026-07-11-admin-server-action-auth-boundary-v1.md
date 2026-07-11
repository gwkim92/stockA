# Admin Server Action Auth Boundary V1 Implementation Plan

**Goal:** Remove the unauthenticated browser-to-privileged-server mutation path while retaining useful read-only AI operations status.

**Architecture:** Treat the absence of application authentication as a hard boundary. Delete the Next Server Actions and POST/token helper instead of inventing partial auth. Read the existing `/api/admin/ai-agents` registry only from the server page, immediately project its nested operator status into an explicit safe DTO, and render a static status panel. Keep the token-protected backend `GET /__admin/codex-oauth/status` endpoint unchanged but outside the Next.js call graph, and keep mutations in the established operations CLI/SSH channel.

**Tech Stack:** Next.js 16, React 19 server components, TypeScript, Vitest, Testing Library, Playwright, shell verification.

## Task 1: Lock the Security Boundary with Tests

**Files:**
- Create: `apps/web/src/app/admin/ai-agents/codex-oauth-status-view.test.ts`
- Create or modify: `apps/web/src/app/admin/ai-agents/CodexOauthOperatorPanel.test.tsx`
- Create: `scripts/verify_admin_server_action_auth_boundary_v1.sh`

1. Add a projector test proving sensitive raw fields cannot appear in the safe view.
2. Add a fail-closed execution-boundary mismatch case.
3. Add component and page-level tests proving the status panel and rendered admin page have no button, form, device code, external auth URL, PID, path, or raw error detail.
4. Add static checks for Server Actions, admin POST helpers/tokens, and loopback start binding.
5. Run the focused tests before implementation and record the expected failures.

## Task 2: Remove the Browser Mutation Surface

**Files:**
- Delete: `apps/web/src/app/admin/ai-agents/actions.ts`
- Modify: `apps/web/src/lib/frontend-api.ts`

1. Remove the generic admin POST helper and admin action token header/env handling from `apps/web`.
2. Remove Codex OAuth relogin and smoke POST wrappers.
3. Retain only the read-only `/api/admin/ai-agents` GET adapter in Next.js; leave the backend-only `GET /__admin/codex-oauth/status` route unchanged and unused by the web application.

## Task 3: Introduce a Safe Status View

**Files:**
- Create: `apps/web/src/app/admin/ai-agents/codex-oauth-status-view.ts`
- Modify: `apps/web/src/app/admin/ai-agents/CodexOauthOperatorPanel.tsx`
- Modify: `apps/web/src/app/admin/ai-agents/page.tsx`

1. Map known raw statuses into fixed Korean labels, tone, summary, and CLI-only next action.
2. Map smoke status through a strict allowlist and format only a safe last-check timestamp.
3. Detect any order-boundary inconsistency and render it as blocked/operator-review required.
4. Convert the client operator panel into a server-rendered static status panel.
5. Pass only the projected DTO to the component; do not expose the raw payload beyond the server page.

## Task 4: Align Adjacent Copy and Runtime Binding

**Files:**
- Modify: `apps/web/src/app/data-health/_components/DataHealthLiveAiInvocationSection.tsx`
- Modify: `apps/web/package.json`
- Modify: `apps/web/tests/e2e/investment-workspace.spec.ts`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/frontend-api-contract.md`

1. State that the web console is status-only and mutations require server CLI/SSH.
2. Bind `next start` to `127.0.0.1` by default.
3. Add an E2E assertion that the admin route contains the status-only boundary and no mutation controls.
4. Record the no-Server-Action and server CLI/SSH-only mutation rules in the frontend architecture and API contract.

## Task 5: Verify and Review

1. Run focused red/green tests and the static security verifier.
2. Run full unit, type, build, E2E, API contract, roadmap, AWH, and diff checks.
3. Capture `/admin/ai-agents` at 375/768/1280px and obtain independent design/functional and Korean/CJK PASS verdicts.
4. Update handoff/review, stage only intended files, and commit.
