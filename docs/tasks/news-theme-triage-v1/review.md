# News and theme review — implementation decisions

## The product flow

`/events` is now a news-first selection list, not a processing-gate dashboard. The article leads to its explicit source, interpretation, company and dated theme review. `/themes/[themeKey]` prioritizes connected company review and keeps the actual stored cycle observations, normalized model inputs, associated news and source use notes distinct.

This is read-only triage/navigation. It does not persist triage decisions, create a watchlist, synthesize investment recommendations or execute playbooks. Existing classification and analysis routes remain reachable.

## Queries and pagination

A native GET form sends a real cutoff date, optional symbol and theme to the existing API. Changing these server criteria deliberately omits the previous cursor. The page uses only an actual returned next cursor; it does not manufacture offsets or claim to search the whole collection. Literal body search and missing-source/evidence/restricted filters operate on the current received page, and that limitation is displayed next to the counts. Search and filter state survive refresh/back navigation. Date and local filters are carried into next/first-page links.

API pagination metadata may be absent or malformed, so such a response is marked as having unknown page information rather than a confirmed last page. Duplicate event IDs can describe different instrument/source relationships; they are retained, with distinct render keys and counts labeled as received records rather than unique articles.

## Meaning of the date and status

The selected date is a cutoff request, not a claim that all news arrived today. Original event dates and the API returned date remain visible. The existing API convention of a UTC default date is unchanged and documented in the UI. Each downstream company/thesis/recommendation page has its own response date. The live adapter's latest active-thesis associations are not an exact point-in-time historical reconstruction, and its per-section record limits are not removed by this UI task.

Theme state, previous-state field, model score, features and actual history are independent source fields. No transition is inferred across an unknown, missing, duplicate or undated record. Duplicate history dates and post-cutoff observations are labeled. Measured zero is not missing; normalized features are not returns. A rejected/suppressed record stays restricted even when another quality field reports pass. The mere presence of source/evidence links never establishes quality approval.

Only stored titles and summaries are displayed. No keyword translation or inferred market narrative is added. Internal storage addresses and arbitrary backend extra fields are absent from the client projection. Primary identities are checked, authenticated GET requests refuse redirects and use a response-body-inclusive deadline, and error bodies/tokens are not rendered.

## Visual refinement

The first successful production-browser capture showed that redundant header navigation, a repeated introductory sentence and the long UTC explanation delayed the first news-source action on mobile. Those repeated elements were removed or moved after the records; requested/returned dates and current-page search scope remain at the top. An explicit layout test checks that the first source action finishes above the actual mobile navigation dock. No source metadata, warnings or UI are hidden just for screenshots.

## Boundaries

No main, dependency/lockfile, backend/schema, scores/weights, benchmark/evaluation split, portfolio/order/broker, account/secrets/AWS, scheduler or deployment writes. No substitute database or live EC2 query. The synthetic fixture is only evidence of UI and request behavior, not current market/account accuracy, full backend correctness or investment performance. Existing adapter defaults and historical precision limitations remain separately scoped.
