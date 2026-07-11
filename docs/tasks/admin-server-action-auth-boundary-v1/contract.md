# admin-server-action-auth-boundary-v1 Contract

## Task Request

- request: Close the unauthenticated Next.js admin Server Action boundary before deployment while preserving read-only AI operations visibility.
- context: `/admin/ai-agents` currently exposes four callable Server Actions that forward a server-side admin token to Codex OAuth relogin and smoke POST routes. The page has no application user/session authorization layer.

## Goal

- goal: Make the web application status-only and fail-closed: no browser-reachable Server Action, POST helper, admin action token, device-auth secret, or mutation control remains in `apps/web`, while operators retain a sanitized Codex OAuth status view and use the existing server CLI/SSH boundary for mutations.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/admin/ai-agents/`
  - `apps/web/src/app/data-health/_components/DataHealthLiveAiInvocationSection.tsx`
  - `apps/web/src/app/data-health/_components/dataHealthAiProviderModel.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/package.json`
  - focused frontend tests and `apps/web/tests/e2e/investment-workspace.spec.ts`
  - `docs/frontend-architecture.md`
  - `docs/frontend-api-contract.md`
  - `scripts/verify_admin_server_action_auth_boundary_v1.sh`
  - this task's plan, contract, handoff, and review

## Invariants

- Keep the backend `GET /__admin/codex-oauth/status` endpoint unchanged and token-protected, but do not call it from Next.js; the web page reads `/api/admin/ai-agents` and immediately projects its nested operator status into a safe DTO.
- Do not add a partial home-grown login/session system in this task.
- Do not change FastAPI admin endpoints, runtime environment secrets, scheduler configuration, or EC2 deployment state.
- Never pass or render `auth_url`, `user_code`, `device_auth_pid`, `status_path`, raw login-probe messages, raw error summaries, read tokens, or admin action tokens.
- Recommendation scoring, weights, benchmark definitions, portfolio positions, broker submit, and order boundaries remain unchanged.
- Mutating relogin and smoke actions must be described as server CLI/SSH-only operations.

## Acceptance Criteria

- `apps/web/src` contains no `"use server"` directive and no exported Server Action.
- `apps/web/src` contains no admin POST helper, admin action token env reference, or Codex OAuth relogin/smoke POST wrapper.
- `/admin/ai-agents` renders a server-side sanitized status view with no mutation button, form, device code, auth URL, PID, filesystem path, or raw error detail.
- Unknown statuses and execution-boundary mismatches render fail-closed operator-review language.
- `/data-health` directs operators to the read-only status page and states that relogin/smoke actions run through server CLI/SSH.
- `npm start` binds Next.js to `127.0.0.1` by default.
- Focused security tests, full Vitest, typecheck, build, full Playwright E2E, visual QA, frontend API contract, roadmap, AWH, verification script, and diff checks pass.

## Verification Commands

- verification command: `bash scripts/verify_admin_server_action_auth_boundary_v1.sh`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task admin-server-action-auth-boundary-v1`
- verification command: `git diff --check`
