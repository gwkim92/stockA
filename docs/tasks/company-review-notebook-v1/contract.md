# Company review notebook v1

User asks to continue stockA after PR #41 and prioritize the actual research workflow over more internal diagnostics. Base develop@d9a154d6cb70c5e2ef817c755baa7e514bfe7df3.

## Product outcome

Add an investor-facing company review route under the existing workspace. Read stored claims, catalysts, risks and invalidation conditions alongside an explicitly linked source document, and write a personal review note/next-check date without changing recommendations or orders. Connect the entry from existing company research. Do not invent source-to-claim entailment, translations, financial facts or approvals.

## Scope

Reuse authenticated bounded server readers and exact identity checks. Only fetch a source when its ID is explicitly present in the returned company source inventory; arbitrary source query parameters cannot fetch unrelated documents. Keep source failure separate from company data and notes. Distinguish raw excerpts/summaries from model interpretations and original source from URLs. Keep funds distinct from company research. Preserve return navigation and selected source in the URL without heavy prefetch.

Notes are explicit-save, browser-local drafts, not server records, accounts, durable audit history or calendar reminders. Show that boundary before saving. Unknown storage, corrupt drafts, blocked storage and a changed company/research snapshot must not silently overwrite or reattach prior notes to new claims. No current-source match means no verified-citation claim. Export a plain-text/Markdown review with original identifiers, snapshot/date, human notes and limitations; no automatic model generation. Avoid injecting user/source markup.

## Acceptance

Test actual saved API shapes, source allowlisting, wrong/missing records, empty versus unknown, snapshot change, storage refusal/corruption, edit/save/reload/delete/export, mobile keyboard/touch, navigation, accessibility and overflow. Run production desktop/mobile browser interactions and inspect final screenshots, not an image mock. Preserve existing regression suites and audit gates. Record exact feature head, CI and integration status. Live EC2/model-quality testing is not implied by synthetic fixtures.

## Boundaries

No main, financial rules/weights/thresholds, production DB/EC2, schema/migration, benchmark/evaluation/golden data, portfolio/order/broker, paid model calls, dependencies/lockfile, accounts/secrets/AWS, scheduler or deployment changes. New frontend/local-draft behavior only. Browser storage is not confidential server storage. A temporary read-only tracked-source export may be used for the DNS-restricted workspace and must be removed from final tree. Repository writes use the GitHub connector. No independent-review or full application validation claim.