# Thesis/source reading workspace — implementation review

## Investor workflow

This is a page-specific continuation of the shared research design, not an additional approval system. The two rewritten routes are the destinations of existing company, holding and recommendation links. Claims and source excerpts come first; metadata and operational checks no longer dominate the reader.

The source reader displays the existing API's `excerpts[].summary` text with an explicit excerpt/summary label. That field is not promised to be verbatim quotation or a complete document. Stored Korean title and Korean summary are independent; missing translation is not replaced by keyword-based sector inference. Publication/filing, period and collection dates remain separately labeled. No internal storage URI is exposed and a boolean access flag cannot invent a browser download route.

The thesis reader preserves stored claims, catalysts, risks, latest review notes, conditions and valuation. Only an explicit `triggered` status is counted as triggered. Unknown conditions, absent review dates, currencies and counts remain unknown. The recorded latest review is not called a new prior/current comparison. Existing deep valuation is reused only when its required collection shape and currency are present, without changing its financial calculations. The next review date is shown in the compact header as well as the context panel so it remains discoverable on mobile.

## Integration details

Canonical resource IDs must match the request. Existing numeric/bootstrap thesis aliases and source numeric-to-external-ID resolution are supported with the documented backend resolver and visible alias labeling. Alias acceptance is compatibility with the backend response, not independent proof of document integrity. Evidence links use validated single-segment routes; performance evidence opens a labeled symbol-filtered list rather than claiming an exact-outcome detail page. Unsupported evidence IDs are shown without fabricated deep links.

Professional gates use the actual backend `title`, `decision`, `detail`, `next_step` and `facts` fields; evidence quality gates retain their `label`/`detail` shape. These existing records remain available after the main research content. The browser suite follows the actual company -> thesis -> AI evidence -> source -> thesis route, not just href string assertions. Existing stock and AI evidence pages are integration dependencies, not a complete redesign of those pages.

The raw reader requests are authenticated server-side GET-only, no-store, with redirects refused and a deadline covering JSON body consumption. Response errors are sanitized. Requested invalid identifiers and missing records use the existing not-found page. No synthetic data is returned to the application on API failure.

## Explicit limits

Testing uses saved API examples and clearly synthetic local HTTP fixtures. It does not certify real EC2 data, current host health, document truth, strategy profitability, or the entire backend. Original stock/AI adapter defaults and keyword-based interpretations elsewhere have not all been removed by this task. Actual runtime comparison remains necessary before rollout.

No main, database/schema, scoring/weights, benchmarks/evaluation split, portfolio/order/broker, package lock, production deployment, secret or AWS changes. The GitHub workflow remains read-only with existing high/critical audit gates; no write-enabled runner or alternate upload path is used.
