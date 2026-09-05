# Research discovery workspace — review

## Product changes

The three entry pages now support actual discovery rather than manufacture a first-choice investment candidate from whether a record is connected to a recommendation or holding. Existing detailed company, recommendation, theme and source-document routes remain unchanged and reachable.

- `/stocks`: company/symbol/market search; recommendation/holding/price-attention filters; actual currency, closing-price date, stored score and record connections. Explicit null means no returned connection; an absent field means unknown, not definitely not held.
- `/cycles`: searchable theme cards with observed state comparisons, normalized news/price/fundamental features, related symbols and actual theme links. A missing/unknown previous or current state cannot count as a transition. Missing features remain missing rather than zero. Summed memberships are labeled overlapping, not unique securities.
- `/market-map`: group filtering and 1/5/20/60-day return selection; individual dates/providers/quality flags; optional 120-day return, 252-day position/drawdown, shock/confidence and source policies remain readable in details. Model regimes, contradictions, correlation tables, source news and provider warnings are distinct from raw observations. XAG proxy context is retained.

Native URL history retains search/filter/window choices across reload and back navigation without changing source data or issuing a mutation. Existing incoming row order and scores are preserved. Invalid-primary-data/HTTP/network/body-timeout failures do not fall back to a synthetic successful market.

## Review decisions

A compact summary is not permission to omit source limitations. Snapshot dates are visible, while repetitive count definitions are moved into an accessible details disclosure to reduce mobile scrolling. Provider freshness labels are identified as provider judgments; a same-day API response is not evidence that every underlying record is current. No new approved horizon/freshness or financial scoring policy is introduced.

The raw loader validates primary list/row identity against repository examples instead of using the older adapter defaults that replace unknown dates and counts. Optional market evidence sections preserve absence versus valid empty lists. HTTP errors and read credentials are not copied into the rendered page. External source links allow HTTP(S) only and reject user-info credentials.

## Runtime boundary

The existing intended EC2/SSH-tunnel handoff was inspected. The current execution session has no configured stockA frontend API base/read token or PostgreSQL command, and no listener on the documented local API/web tunnel ports. Relevant AWS plugin discovery found an available but unconnected provider, not an authenticated current server session. These findings do not establish that the deployed server or database is absent or down.

No actual investment records were read from EC2. No replacement DB, account/secret, infrastructure rule, schema, scheduler, scoring/weight, benchmark/evaluation split, portfolio/order/broker, production deployment, dependency/lockfile or main-branch change took place. Live-data comparison and deployment remain separate outstanding work.

## Verification interpretation

Unit cases use unmodified saved API examples for contract compatibility and synthetic mutations for invalid/missing edge cases. Browser fixtures are synthetic, not current market data or recommendations. The complete frontend suite and production build run on the clean GitHub runner; local verification is limited to syntax, pure model assertions, fixture-server syntax and diff checks because local GitHub/npm DNS is unavailable. No full backend or investment-performance claim follows from these checks.
