# Company and evidence workspace v1 — handoff

## Integration record

PR #33, branch `codex/company-evidence-workspace-v1`, based on develop@4b8d05aca22a0bedf2dd999f22e2b6ad59480802. The PR records the final checked head, integration SHA and post-merge run. Do not equate the checkpoint below with a check on a later unverified revision.

## Delivered

- `/stocks/[symbol]`: compact research-first entry, actual recorded close/date, explicitly reported daily return, source status, holdings/recommendation unknown-state distinctions, investment case and direct source links.
- Price observations: 30/90/all received-record controls, chronological recorded closes only, null breaks, invalid/future/duplicate-date handling and an accessible selected-observation table. No inferred daily returns, synthetic calendar observations or corporate-action adjustment.
- Company and fund primary sections are distinct. Full existing financial, valuation, industry, fund and price components remain at `/stocks/[symbol]/details`; these links disable prefetch. Existing low-level adapters still have legacy defaults and are not claimed fully remediated by this task.
- Optional market context streams separately with an authenticated bounded read and exact symbol/instrument validation. It cannot erase primary research or supply an unrelated first thesis.
- `/ai-evidence/[evidenceId]`: stored interpretation, uncertainty/rejection reasons, exact extracted-field-to-chunk navigation, readable original excerpt/summary text and explicit source-link conflict handling. No keyword-generated Korean source narrative.
- Successful model execution is not approval. Explicit rejection takes precedence. Existing backend alias shapes are labeled rather than treated as independent exact attestation.
- Main company/evidence requests have a five-second response-body deadline, no-store and no-redirect behavior, server-side credentials and sanitized failure states. The optional context deadline is three seconds.

## Verification checkpoint and visual refinements

Initial tested head `d04634fff7bb25352bdf485cd3c2f5f169365c7b` passed Web Product Quality run `33969941025`, job `101316540228`: locked install, full frontend unit regression, production build, generated-route typecheck, full/production audits and all four browser suites.

Artifact `9970666573`, SHA-256 `5346b5d49c93da17ddd99f1b27f946839b58b6ec53e1a1e87c33c016dcf0a1df`, was downloaded and verified. HTML reports contain 64 home/discovery, 32 holdings, 34 readers and 34 company/evidence cases: 164 expected, zero unexpected/flaky/skipped. Both audit JSON inventories contain zero findings at the inspection time.

Initial desktop/mobile company and evidence viewport captures were inspected. The company mobile header and notes delayed the first investment case, and the evidence source action was too far down the mobile page. The next code revision collapses general source notes (explicit blockers remain open), compacts mobile company metrics and places the source action next to interpretation. New stricter first-reading/source-action position checks require y < 700px, without removing existing checks. Additional browser cases open the full saved fund contract and compare a synthetic financial ratio between summary and the retained detailed model. These refinements are in `197b614dbe44b724db721783710893ffe903b256`; final-head CI and final screenshots must be reviewed before integration. The final PR body records that evidence.

Local strict TypeScript compilation of the pure model/transport and its existing dependencies passed. Changed TS/TSX/config/test syntax, fixture-server syntax, focused compiled model/transport assertions and whitespace checks also passed. A full local locked installation/Next build was not performed because GitHub/npm DNS is unavailable in this sandbox; clean GitHub runners execute the full frontend validation.

## Explicit limits

Synthetic prices, company/fund fields, document excerpts and test-server responses are test inputs, not actual market/account evidence or recommendations. This task did not validate current EC2 records or host health, run full backend regression or backtests, or deploy the app. The existing intended environment remains the target; no substitute database was created.

No main, dependencies/lockfile, backend/schema, scoring/weights, benchmark/evaluation split, portfolio/order/broker, account/production secrets, AWS or scheduler changes. The temporary source export was read-only, did not persist credentials and is absent from the final diff. Persistent CI is read-only and keeps high/critical dependency findings blocking. No independent reviewer approval is claimed.

## Continuation

Validate actual representative records through the existing authorized runtime before rollout. Remaining event/theme entry pages and genuine historical judgment comparisons require separately bounded work. Do not label a latest snapshot as a change history or repeat more readiness wrappers instead of the research workflow.
