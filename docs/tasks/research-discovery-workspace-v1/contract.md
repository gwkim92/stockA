# Research discovery workspace v1

## Request and base
Continue after the shared workspace redesign, including remaining page-specific UX/UI and verification of actual-data access. Base: develop@5aee8063db146c6eb03ad33492f7da3440d9d443. Work branch: codex/research-discovery-workspace-v1.

## Product objective
Make company discovery, market context and theme-cycle exploration usable under the shared design system. Preserve existing analysis/detail routes and separate observed market facts, model output and research navigation from investment advice. Do not describe a recommendation/holding association as today's best stock. Do not claim a transition when its previous state is unknown, or unique security coverage by summing overlapping theme memberships.

## Scope
- Inspect existing stocks, cycles and market pages and their actual backend DTOs.
- Add functional read-only discovery filters, date context, comparable observed values, mobile layouts and links to existing analysis.
- Preserve null/unknown/empty/source-limited semantics, existing rank/score values and API contract compatibility. Do not normalize missing evidence into a healthy zero.
- Read intended runtime documentation and check only documented authorized access paths. A failed/missing connection is not proof the remote service or database is absent. No new DB/account/secret/infrastructure configuration.
- Extend frontend unit and production-browser tests using clearly synthetic fixtures. Record actual-data validation separately from fixture QA.

## Boundaries
No schema/backend scoring/weight/benchmark/evaluation changes, live financial writes, portfolio mutation, orders, broker actions, AWS writes, production deployment or main changes. Follow AGENTS.md account and branch restrictions. This task changes presentation/navigation, not policy or approved freshness thresholds.

## Acceptance
Functional search/filter/reset, URL-safe links, unknown-date and unknown-state handling, keyboard accessibility, no page-width overflow, and existing detailed analyses remain reachable. Full frontend tests, Next production build/typecheck, full/production audit and desktop/mobile Playwright must pass before integration. Capture and inspect the redesigned views. A short-lived read-only branch source export may be used because local GitHub DNS is unavailable; remove it from the final tree. All repository changes are pushed through the connected GitHub actions, not a write-capable runner.
