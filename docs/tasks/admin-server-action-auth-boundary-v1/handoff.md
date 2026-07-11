# admin-server-action-auth-boundary-v1 Handoff

## Status

- completed: local implementation and verification are complete; not pushed or deployed to EC2.
- current branch: `codex/admin-server-action-auth-boundary-v1`.
- base commit: `a7ca511d`.

## Delivered

- Deleted the four browser-callable Next Server Actions and removed the web admin POST/token helper surface.
- Replaced the raw client operator console with a static server component that receives only a fixed allowlist DTO.
- Added fail-closed projection for unknown, malformed, missing, or order-boundary-inconsistent operator state.
- Added component and full-page sentinel tests proving OAuth URL/code, PID, path, raw error, token, and raw labels are not rendered.
- Made the admin and data-health copy explicit: status is web read-only; relogin and live smoke operations are server CLI/SSH-only.
- Bound `npm start` to `127.0.0.1` by default.
- Preserved backend token-protected OAuth endpoints unchanged.

## Starting Evidence

- `apps/web/src/app/admin/ai-agents/actions.ts` exports four browser-callable Server Actions without application user/session authorization.
- Three mutating actions call internal Codex OAuth relogin/direct-smoke/news-smoke POST wrappers; the refresh action also broadens the callable Server Action surface unnecessarily.
- `apps/web/src/lib/frontend-api.ts` reads `STOCKANALYSIS_FRONTEND_API_ADMIN_ACTION_TOKEN` and forwards it through `X-Stockanalysis-Admin-Action-Token`.
- The client panel receives raw status fields including device auth URL/code, PID, status path, login probe, and error details.
- The FastAPI routes still require read auth plus a separate admin token, but that server-side token is not a substitute for authenticating the browser caller of a Next Server Action.

## Threat Model

- A network client that can reach Next.js can discover and invoke a deployed Server Action even when the UI button is hidden.
- Next.js then acts as a confused deputy, attaching privileged server-side headers to an unauthenticated caller's mutation.
- Device code, auth URL, PID, path, and raw diagnostics create unnecessary sensitive-data exposure on a page with no session authorization.

## Exact Next Step

- exact next step: fast-forward this verified commit into local `develop`, then open `recommendation-weight-review-readiness-semantics-v2` as a separate shadow/read-only task. That task must separate evidence sufficiency from user authorization and must not change recommendation weights, scoring, portfolio positions, or order/broker boundaries.

## Guardrails

- Do not implement weight changes, automatic orders, or broker submit.
- Do not mutate backend admin routes or EC2 runtime configuration in this task.
- Keep all existing QA artifact directories untracked and unstaged.

## Verification Evidence

- TDD red: focused tests initially failed because the safe projector did not exist and the old client panel still exposed mutation/raw-state behavior; the static verifier failed on `actions.ts`.
- Focused green: 3 files, 9 tests passed.
- Full Vitest: 25 files, 59 tests passed.
- TypeScript and production build: passed.
- Playwright: 78 total, 74 passed, 4 viewport-specific intentional skips, 0 failed; includes status-only admin assertions and serious-accessibility checks across desktop/mobile/tablet.
- Backend security regression: 31 FastAPI/Codex OAuth tests passed, including read-token and separate admin-action-token enforcement.
- Static boundary verifier, frontend API contract, project roadmap, AWH readiness, shell syntax, and `git diff --check`: passed.
- Production runtime: `127.0.0.1:13003` only; removed/stale `Next-Action` POST returned 404; page Server Action manifest contains empty node/edge maps.
- Browser HTML and three-viewport capture scan: console errors 0, horizontal overflow 0, buttons/forms/external auth links 0, forbidden OAuth/admin-token fields 0.
- Final visual set: `output/playwright/admin-server-action-auth-boundary-v1/final3`, 9 images; two fresh independent reviewers returned PASS for design/functional/security and Korean/CJK/responsive quality.

## Residual Risks / Unverified

- FastAPI `/__admin/codex-oauth/status` and `/api/admin/ai-agents` still contain the raw operator DTO for authenticated internal clients. The raw nested object enters Next server memory, then is projected before any browser rendering; backend DTO minimization is a separate future hardening task.
- The repository has no browser user/session authorization by design, so the web application remains status-only.
- EC2 systemd command, reverse-proxy reachability, and live runtime were not inspected or changed in this task. The local package-script loopback binding does not prove deployment binding until a later deployment smoke.
- Recommendation weights, benchmark definitions, portfolio positions, broker submit, and order boundaries were not changed.
