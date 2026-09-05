# Research discovery workspace v1 — handoff

## Integration tracking

PR #30 continues the workspace redesign with page-specific changes to `/stocks`, `/cycles` and `/market-map`. Base: develop@5aee8063db146c6eb03ad33492f7da3440d9d443. The final PR-head product check, screenshot artifacts and PR merge state are the integration record. No production deployment is included.

## Delivered

- Shared discovery framing, compact responsive summaries and expandable count/date definitions.
- Company/symbol/market search; recommendation/holding/price-attention filters; recorded prices, currencies and dates; explicit absent-versus-null connections. No arbitrary best-stock ordering.
- Theme-state cards with known-history transitions, normalized feature bars, zero distinct from missing features, related company links and overlap-inclusive membership counts.
- Market group and return-window controls with source dates, provider quality and explicit XAG proxy context. Detailed 120-day returns, 252-day position/drawdown, shock/confidence and source policies remain available.
- Separate regime/conflict, correlation, news-source and provider-quality sections. Missing records do not become healthy zeros.
- URL-persisted search/filter/window choices with reload/back-navigation support, preserving incoming scores and row order.
- GET-only authenticated reads with body-inclusive deadlines, abort/timer cleanup, safe error presentation and no fixture fallback on HTTP failure.

## Verification and visual review

Initial implementation head 6e01ea2d52121d36e103c84de7d53dcad144b6ed passed Web Product Quality run 33956226761 / job 101279958135:

- 29 frontend test files, 194 unit tests (35 new discovery cases).
- Next.js production build and generated-route typecheck.
- 64 Chromium desktop/mobile cases (20 new discovery cases).
- Three redesigned routes passed full-page axe and page-width overflow checks in the tested viewports.
- Full and production dependency audit inventories contained zero findings at inspection time.

Initial browser artifact 9966477325, SHA-256 fac4759593667810415bfc1777abbaf539194a9ef33331f947d43ed20b46e0da, was downloaded and inspected. The mobile first record was too far below explanations, so count definitions moved into an accessible disclosure and summaries were compacted. Detailed market provenance was retained, not removed for a smaller screen.

The follow-up introduced an explicit first-record visibility assertion: y < 780px on mobile, y < 850px on desktop. Refinement runs 33956697303 and 33957027697 each passed unit/build/type/audit and 63 of 64 browser cases, but the mobile market record remained at y=786.09375. Shorter result text alone did not change that position. The assertion was not relaxed. Code head 28ef115dc35acb6cccc6a565d53992d7643bf8c4 further makes mobile counts a single scan row and moves a repeated candidate-navigation link after the results. The final PR-head run must validate this layout before merge; the resulting screenshots and exact final run ID are recorded on PR #30.

Local checks cover syntax transpilation of 13 TS/TSX files with zero syntax errors, fixture-server syntax, pure model assertions using the repository API examples and diff whitespace. Complete npm/build/browser execution runs on the clean GitHub runner, not a claimed full local clone/install. Unit cases use unmodified saved examples plus adversarial test inputs; browser fixtures are synthetic rather than real investment recommendations.

## Actual-data access and exclusions

The intended EC2/SSH-tunnel documentation was inspected. This session has no configured stockA frontend API base/read token or PostgreSQL command, and no listener on the documented local API/web tunnel ports. AWS integration discovery returned an available but unconnected provider. These findings do not prove the deployed service/database is absent or unhealthy.

No actual EC2 company/ETF/source-limited records were queried. No replacement DB, credential, account, AWS rule, production deployment, schema/backend financial computation, benchmark/evaluation split, score/weight, portfolio/order/broker, scheduler, dependency/lockfile or main change occurred. The temporary read-only source export helper is absent from the final tree. Persistent CI retains contents:read; repository changes were pushed only through the connected GitHub tools.

## Continuation

Live-data comparison and deployment remain unexecuted. Validate representative actual records through the existing intended runtime before rollout. Remaining page-specific UX work includes portfolio review, performance and deeper evidence navigation. Genuine prior/current judgment views must compare stored records, not infer a change from a single current snapshot.
