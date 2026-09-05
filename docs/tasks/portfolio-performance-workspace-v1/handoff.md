# Portfolio and performance workspace v1 — handoff

## Integration record

This task is tracked by PR #31 on `codex/portfolio-performance-workspace-v1`, based on `develop@9b1717d13989a2c584aa8aafbb1b3bb01887880b`. The PR records the final feature SHA, final-head workflow result, merge SHA and post-merge verification. Integrate only a green, mergeable final head. The earlier temporary tool rejection no longer prevents the authorized connector operations: PR creation and the refinements succeeded in this continuation without an alternate write path.

## Delivered

- Holdings review at `/portfolio/coverage`: symbol/coverage filters, requested date, explicit absent/unknown evidence, measured base-currency position subtotals and recorded review reasons.
- Outcomes at `/performance`: absolute/benchmark returns, alpha in percentage points, contribution in basis points, horizon/search filters, whole-report summary and measurement exclusions.
- Exact portfolio/row identity, body-inclusive deadlines, GET-only authenticated reads and sanitized error states.
- Original return helpers unchanged; native amounts never substituted into same-base-currency subtotals; incomplete/mixed-currency rows excluded with visible counts. No account-total, strategy-return or cash-flow-return claim.
- Whole-report summaries unchanged by local filters; no-sample or missing summary values remain unmeasured.
- Exact history reference before displaying feedback. Latest stored review is not a fabricated before/after comparison.
- Original policy detail page preserved with its source blob intact at `/portfolio/coverage/details`, labeled as latest policy data rather than historical selected-date data.
- Both legacy-detail links disable automatic prefetch. Deliberate navigation still renders the original page. Report dates persist across holdings/performance tabs.
- Valid summary dt/dd structure and keyboard-operable date/filter/disclosure controls.
- Mobile content moved ahead of repeated explanations. Counts, exclusions and source/date boundaries remain visible; compact outcome numbers have a one-row mobile layout while currency amounts retain a wider two-column layout.

## Verified implementation checkpoints

Run `33959995147`, job `101290132021`, head `87e2c075d7b992fd38bec85b0b362cee16f2a7c4` passed full frontend checks plus the original 64 and initial 24 review browser cases. Downloaded captures revealed excessive vertical introduction on mobile.

Expanded integration run `33960125294` caught a fixture typo: the old adapter calls `/api/trading/readiness`, not `/api/trading-readiness`. The fixture and both positive/negative request assertions were corrected; the production API was not changed and the legacy render assertion was retained.

Run `33960380119` then passed those legacy/date/prefetch cases but failed both new mobile first-record position checks (holdings y=790.140625, performance y=862.828125 against <780). The layout and redundant copy were revised without relaxing the checks.

Run `33960672457`, job `101291902742`, head `ef623e96de7f473a9ae6669daccab1c56f990b4c` completed successfully:

- 30 frontend test files / 234 unit tests, including 40 new review tests.
- Next production build and generated-route TypeScript check.
- 64 existing desktop/mobile browser cases plus 32 review/integration cases (96 total).
- Both browser reports have zero unexpected, flaky or skipped cases.
- Whole-page axe, page-width overflow and first-record position checks in the tested primary views.
- Full and production dependency audits each report zero findings at inspection time.

Artifact `9967855227`, SHA-256 `0cdca3a9e97eb1d7eb7620b2813436f10f7726090b730a314a2578906416013e`, was downloaded, hash-verified and inspected. Actual desktop holdings and mobile holdings/performance captures were reviewed. A last compact-outcome summary refinement follows that checkpoint; its final-head browser artifact and inspection are recorded in PR #31. No screenshot-only hiding or styling is used.

## Verification boundaries

The complete application tests ran on clean GitHub runners. The sandbox has no complete locked dependency installation and cannot resolve GitHub/npm; local checks are not represented as a complete repository build. Browser API data is deliberately synthetic, not current recommendations or account balances. The new browser suite checks selected-date requests, native-currency exclusion, missing data, zero versus unknown outcomes, exact feedback ownership, invalid/future/duplicate dates, link prefetch and deliberate legacy navigation.

No live EC2 record comparison, current host-health validation, production deployment, whole-backend regression or investment profitability test occurred. No main, backend/schema, recommendation weights, benchmark/evaluation split, portfolio/order/broker, dependency/lockfile, AWS account, infrastructure or production-secret change occurred. CI retains read-only repository permissions and blocking high/critical audit gates.

## Continuation

Validate representative real company/ETF/source-limited records through the existing intended runtime before production rollout. Remaining deeper research/evidence pages can use the same design conventions. A genuine judgment-change view must compare stored historical snapshots rather than label the latest record a new change.
