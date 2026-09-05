# Investor home reliability — handoff

## Status

Implementation and code-head verification are complete in PR #25 on `codex/investor-home-reliability-v1`, based on `develop@7907caa3dbcd2d571bb066f173e7ec9225409284`. Integration is tracked by the PR merge state and requires the final head's product check. Product reassessment and subsequent priorities are in `docs/product-review-2026-09-05.md`.

## Implemented

- Four independent GET feeds in place of seven coupled home requests.
- Five-second budget including response JSON body, abort, and timer cleanup.
- Per-section unavailable/invalid/timeout state; no exception or credential serialization into UI.
- Unknown counts/coverage remain unknown; genuinely empty successful feeds remain distinguishable.
- Analysis date separated from response-generation timestamp; historical, future, and missing dates explicit.
- Required row identities checked before rendering.
- Backend candidate order preserved; source restriction overrides paper-input permission.
- Investor-first cycle/candidate/news/holding-review flow and performance navigation.
- Compact home summary/metrics and collapsed detailed operating status; shared components and deeper routes unchanged.
- Full frontend test/build/type CI plus desktop/mobile production-browser tests and screenshots.

## Verification

Initial run `33944296217` at head `2052f2db7c8368cb396c0c1e74a627721bf0a873` passed 91 tests and 14 browser cases. Downloaded desktop/mobile screenshots revealed an oversized status panel preceding research content; it was collapsed and moved after the research sections, and the summary/mobile metrics were compacted.

Refined implementation run `33944683498` at head `f68dbff79ed4edd282c9b527a67d4c5e35079060` completed successfully:

- 26 frontend test files, 95 tests passed, including 36 new home/model/transport cases.
- Next.js production build and generated-route typecheck passed.
- 14 Chromium browser cases passed (seven scenarios across desktop/mobile).
- Healthy-page scoped axe check passed; tested viewports had no horizontal overflow or page errors.
- Final screenshots downloaded and visually inspected at 1440px desktop and 390px mobile widths.
- Browser artifact `9962965590`; SHA-256 `c204cdb4db3c42d01332824dcbec4469a3e9cd2b77677d824144cbeb1c94a0d8`.

Local strict TypeScript compilation and actual compiled model/transport assertions also passed. A complete local repository build was not performed because the execution sandbox cannot resolve GitHub/npm; the clean GitHub runner supplies repository-level evidence. Final documentation changes rerun the same check before integration.

## Limits and risks

The browser HTTP fixtures are deliberate test inputs, not live market/portfolio evidence. Do not describe screenshot sample values as real recommendations. No EC2 deployment/current-host validation, live PostgreSQL observation, backend regression discovery, strategy backtest, or scoring change took place. No dependency/lockfile, migration, benchmark, portfolio, order, broker, scheduler, or secret changes are included.

The existing lockfile audit reports eight high-severity package entries, including direct dependency `next`; these are not eight distinct CVEs or a confirmed exploit assessment. Diagnostic inventory is preserved in `dependency-audit.json`. The audit step is explicitly non-gating and exited 1; the product workflow's success is not security clearance. Remediation is tracked in issue #26 and is required before a production rollout. No force-update was performed.

## Continuation

Preserve all existing production account/secret/branch/trading boundaries. Resolve dependency advisories before deploying to the documented existing environment. Next investor-facing work should consolidate existing company thesis/evidence and true historical change views, not add more nested approval wrappers. Fixed-horizon scoring research belongs in an isolated benchmarked comparison before any live weight change.
