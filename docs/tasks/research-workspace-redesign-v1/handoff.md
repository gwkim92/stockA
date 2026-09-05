# Research workspace redesign v1 — handoff

## Scope and integration

PR #29, feature branch `codex/research-workspace-redesign-v1`, based on develop@9aa401882cd9b8b1a5b4a50d0673966c1f2b2e20. Final integration is tracked by the PR state; the final documentation head must pass the same checks before merge.

The shared app shell/navigation and design system are rebuilt. Home, candidate exploration and investment-memo reading receive specific layouts/interactions. Other research/operations pages inherit the shared shell/tokens/components but are not represented as individually redesigned and live-validated pages.

## Delivered

- Research/review navigation grouping, compact desktop rail and mobile bottom dock.
- Native modal page search and safe-format direct ticker navigation; keyboard shortcut, Escape/focus return and route-aware active navigation.
- Light reading surfaces, consistent typography/spacing/status controls, table/card hierarchy and reduced-motion handling.
- Research home workbench with cycle observations, candidates, news and holding review; existing source-date/unknown/error behavior preserved.
- Candidate search and filters, immutable incoming order/scores, explicit source limitations and no-results reset.
- Investment-memo chapter links to real sections; existing thesis ownership, ETF/company distinction and data guards unchanged.
- Loading/error/missing-route recovery without fabricated metrics or raw UI error disclosure.

## Verified implementation evidence

Run 33953275578 / job 101271883219 at head aaa9df7c76767887bba70702bb2d16c4d4957c79 completed successfully:

- 28 frontend unit-test files; 159 tests passed (31 more than the 128-test baseline).
- Next production build and generated-route typecheck passed.
- 44 Chromium cases passed: previous 30 home/memo cases plus 14 workspace cases across desktop/mobile.
- Full healthy-home shell and dialog axe checks passed; scope-specific memo checks remain.
- Tested 1440/390px viewports and 1024/360px reduced-motion layouts without horizontal overflow.
- Full and production npm audit inventories each report zero findings at the time of the run.

The first run caught removed company-evidence explanatory copy; the distinction was restored rather than deleting the regression assertion. Browser captures then exposed unused cycle-grid space, undersized home metadata and a legacy oversized H1 rule. The layout and typography were refined and the memo screenshot now captures the initial reading state before anchor navigation, without hiding/restyling UI elements.

Refined code head 5015e50a732ad6a64479baee8c861b4c2ff8209d passed run 33953740820 / job 101273155254, including the same tests/audits/build/browser steps and an explicit compact-title-size assertion. Artifact 9965690234 has SHA-256 92dbd6b6b93d55481653bf588bc4659e56d9c2a58d6842117281af1b70af499b. Its desktop/mobile home, candidate and memo captures were downloaded for visual review; final home and memo viewport images were inspected. Both final audit JSON inventories contain zero findings.

## Source and execution boundaries

The sandbox cannot resolve GitHub/npm for a complete local checkout/install. Exact tracked source was obtained through an authenticated read-only artifact; local syntax, fixture-server and whitespace checks ran, while complete frontend execution ran on clean GitHub runners. Per-file before/after hashes protected the application-source transfer. The temporary transfer/export helpers and payloads are absent from the final tree. A runner attempt to modify a workflow was denied; the application-only transfer was separated from the workflow filter update performed via the already-authorized GitHub connector. Persistent CI retains contents:read and does not persist checkout credentials.

No package/lockfile, backend, live DB/schema, score/weight/benchmark/evaluation split, portfolio/allocation/order/broker, account/production secret, AWS, scheduler, production deployment or main-branch changes. The existing intended runtime documentation was read, not treated as current host-health evidence. The previous live-data comparison/deployment task remains unexecuted, not silently replaced with fixture evidence.

## Continuation

Use the existing intended runtime for real company/ETF/source-limited records before production rollout. Carry the design system into any deeper page-specific revisions with their own browser evidence. A genuine prior/current judgment-change view must compare stored snapshots; do not invent a change from a current snapshot or introduce more nested approval wrappers in place of the research experience.
