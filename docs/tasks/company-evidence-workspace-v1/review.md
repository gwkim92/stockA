# Company and evidence workspaces — product review

## Investor workflow

The company overview now connects the stored investment case to recorded prices, company/fund-specific analysis, direct news and source interpretation. It is no longer a sequence of audit panels preceding the research. Existing professional financial, valuation, industry, fund and price components remain reachable through a deliberately opened `/stocks/[symbol]/details` route. Heavy detail links disable prefetch. The detailed route still uses the pre-existing adapter; this task does not claim all legacy defaults or rendering behaviors are repaired everywhere.

The evidence detail distinguishes a stored model interpretation from original excerpt/summary fields. Extracted values link to their exact returned chunk ID. Unknown or conflicting source references do not choose another document. Rejected candidate status overrides a separate pass flag, and successful model execution does not become input approval. Source keyword heuristics and inferred Korean topic summaries were removed from this rewritten detail view. Existing external/event aliases are accepted only in the documented backend shape, with alias labeling rather than a claim of independent identity attestation.

## Data presentation

- Recorded close, currency, observation date and an explicitly supplied one-day return remain separate. No return is inferred from the last two sparse observations.
- Price chart controls select the last 30/90 or all received observations, not calendar or trading-day lookbacks. Date-invalid, duplicate and after-snapshot values are excluded; ambiguous duplicate dates retain a null break. Missing close values split the SVG path rather than become zero. The chart does not invent omitted trading dates or corporate-action adjustments.
- Missing holdings/currency/recommendations remain unknown; explicit zero quantity/null position is distinguished from a missing field. The explicitly linked thesis is used rather than the first neighboring record.
- Company and fund analyses have different primary sections. Company model scores are not shown as return predictions or probability of success. Stored source policies, dates, uncertainties and limitations remain visible.

## Resilience

Primary company/evidence requests are authenticated server-side GET-only, no-store and redirect-refusing, with a five-second deadline including JSON consumption. The optional company neighborhood is a separate streamed section with a three-second deadline and exact symbol/instrument ownership validation. Its absence cannot erase the main research page or change its thesis link. Canonical mismatches and malformed primary identities are unavailable, not synthetic healthy data. Source/API errors are not copied into rendered UI.

## Execution boundary

All browser values and document examples are synthetic. These checks do not validate current EC2 market/account records, host availability, full backend regression or investment outcomes. No replacement database, secret/account/AWS changes or deployment occurred. No scoring/weight/benchmark/evaluation split, schema, portfolio/order/broker, scheduler, package-lock or main-branch edits are included. Repository writes use the GitHub connector, and persistent CI remains contents:read. The short-lived read-only source-export workflow is removed before integration.
