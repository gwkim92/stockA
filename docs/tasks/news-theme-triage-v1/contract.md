# News triage and theme review v1

Continue the user's stockA development and overall UX/UI redesign after PR #33. Base develop@861f7f09402b342dd94a190b4767a010be906892.

## Product outcome

Make the entry to the investment operating loop useful: read actual incoming events, narrow the review list, open its exact interpretation/source, inspect the associated theme, and continue to the connected company/thesis/recommendation. Prioritize the news and next review destination over another dashboard of processing gates. This iteration is read-only triage/navigation, not persisted triage decisions or an order/playbook engine.

## Scope

Rewrite `/events` and `/themes/[themeKey]`. Use the existing event-list and theme-detail API contracts, exact identifiers, bounded authenticated GETs, a real requested cutoff date, server symbol/theme filtering and cursor pagination. Local text/review filters must be labeled as applying only to the received page; changing server criteria resets the cursor. Preserve search state in the URL, and carry the explicit requested date between news and theme views. Do not silently make a historical request today or describe all returned historical events as today's news.

Theme review must keep recorded cycle state, actual history observations and normalized features separate. Do not invent transitions across missing/duplicate/undated history, or turn model scores into returns. Preserve duplicate event relationships if one event has different source/instrument links; avoid React key collisions without deleting source records. Linked companies need genuine company-analysis links, and only explicitly returned thesis/recommendation/source/evidence IDs may become deep links.

Unknown/empty/failure are distinct. Rejected/suppressed evidence stays restricted; evidence-link existence is not approval. Stored original titles, Korean titles and summaries remain separate. No frontend keyword translation, arbitrary top-stock ranking, inferred freshness thresholds or source-policy changes.

## Verification

Test saved contracts and adversarial identities, missing fields, literal search, rejected/unknown gates, bounded cursors, date validation, paging/reset, partial failures, source dates, duplicate/history behavior and error redaction. Add real production desktop/mobile browser interactions, source/theme/company navigation, accessibility/overflow checks and screenshot review. Run existing 328 unit tests and 174 browser cases plus the new tests, build/typecheck and dependency audit gates before develop integration. Keep the task handoff current and record exact results.

## Exclusions

No main, dependencies/lockfile, backend/schema, financial scoring/weights/benchmark/evaluation splits, portfolio/order/broker, account/secret/AWS, scheduler or production deployment changes. Do not use another database. Existing live-adapter defaults, collection limits and latest-thesis associations may constrain historical precision; show this limitation instead of claiming point-in-time reconstruction. Actual EC2 records and deployment remain unverified unless the existing authorized runtime is actually used.
