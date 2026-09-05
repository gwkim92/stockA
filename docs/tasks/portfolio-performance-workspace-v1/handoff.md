# Portfolio and performance workspace v1 — handoff

## Current status

Implementation and repository tests are uploaded to `codex/portfolio-performance-workspace-v1` based on `develop@9b1717d13989a2c584aa8aafbb1b3bb01887880b`.

- implementation commit: `2098d25b25bd78e37a9bca7327353dbabdbcb824`;
- test/CI commit: `c893fa4d3b8de328a3fdee17cf90896ce4c0af06`;
- no PR was created for this branch and it has not been merged into develop;
- no production deployment or actual EC2 data validation occurred.

The connected tool blocked an additional two-file refinement and the PR creation request because it could not determine their security status. Those blocked modifications were not applied through another route. The test tree successfully created before the blocked refinement was committed separately and uploaded. A read confirmed there is no PR for this branch. Do not merge the branch or claim its full product workflow passed.

## Uploaded functionality

- `/portfolio/coverage`: holdings, thesis/outcome/valuation filters, requested date, explicit missing evidence, stored review reasons, exact-history-linked feedback.
- `/performance`: per-recommendation absolute and benchmark returns, alpha in percentage points, contribution in basis points, horizon filters, whole-report summaries, exclusions and attribution explanations.
- Authenticated GET-only requests with a response-body deadline and no raw error/credential serialization into page results.
- Position subtotal eligibility requires explicit matching base currency, finite market value and positive cost; native currency fields are never substituted. Existing return calculation helpers are reused unchanged. Subtotals are not presented as full account balances or strategy returns.
- Local filters retain incoming order and do not recalculate the report summary.
- Original portfolio policy/feedback screen is preserved unchanged as `LegacyPortfolioPage.tsx`, reachable at `/portfolio/coverage/details`; its latest-data behavior is labeled separately from the new historical-date selection.
- Latest stored review records are not described as a newly computed prior/current change history.

## Verification actually executed

The sandbox has no complete locked npm dependency installation and cannot resolve GitHub/npm. The full Next/Vitest/Playwright workflow was not executed for this branch.

Local results against the uploaded implementation:

- strict TypeScript 5.8.3 compilation of the pure report model and transport plus their existing helper dependencies: passed;
- syntax transpilation of 14 changed TS/TSX/config/test files: zero syntax errors;
- fixture server Node syntax check: passed;
- Node native test runner, compiled model/transport focused checks: 20 passed;
- Node native test runner, real localhost HTTP calls to the isolated synthetic report server: 8 passed.

Focused coverage includes saved API contracts, exact portfolio identity, absent/duplicate rows, invalid/future dates, mixed currencies, zero versus missing values, thesis linkage, immutable filtering, alpha units, zero-sample summaries, exact feedback history reference, error redaction and body timeout/abort. HTTP tests additionally exercised selected-date query propagation, the two-of-four eligible position subtotal, missing base currencies, mismatched feedback, wrong-portfolio responses, empty outcomes and missing summaries. The first custom local test harness incorrectly let a default argument replace undefined input; that harness was corrected to call the parser directly, with the product parser and repository test unchanged.

These are 28 focused local checks, not a claim that the repository Vitest tests or the browser cases passed. Test market/portfolio values are synthetic.

## Remaining verification and review

Run the branch's full locked install, all frontend unit tests, production Next build, repository TypeScript 6 typecheck, full/production audit gates, existing home/discovery/memo browser suite and the new review browser suite. Capture and inspect desktop/mobile layouts. Test the preserved legacy details route, including its use of latest rather than selected historical data.

The blocked optional refinement concerned valid definition-list grouping in the summary and suppressing prefetch of the legacy policy route. Both need review before integration; the primary loader itself has only one coverage request, but link prefetch behavior has not been browser-verified. No screenshot of the new pages is available from a production browser run. Do not reuse earlier discovery screenshots as evidence for this work.

## Boundaries

No main, backend/schema, scoring/weights, benchmark/evaluation split, portfolio/order/broker, dependency/lockfile, AWS/account/production-secret or deployment changes. Actual EC2 records and investment performance remain unverified. PR #30's existing 194 unit / 64 browser results apply to that earlier discovery implementation, not to these new review pages.
