# Company and evidence workspace v1

Continue the user's requested overall UX/UI redesign after PR #32. Base develop@4b8d05aca22a0bedf2dd999f22e2b6ad59480802.

## Product goal

Finish the company -> investment case -> interpreted evidence -> source reading path. Rewrite the primary company and AI evidence detail presentation without making more readiness wrappers the product. Use actual source fields, compact reading hierarchy, date/identity context and working evidence navigation.

## Findings and scope

`stocks/[symbol]` couples primary and optional neighborhood requests through Promise.all, then fetches unverified recommendation position data. Its fallback 1-day return uses the last two non-null observations, which need not be consecutive trading sessions. `ai-evidence/[evidenceId]` still constructs a Korean source-topic narrative from keywords. Correct these presentation and resilience issues without changing financial computations or backend rules.

Keep existing financial/valuation/fund/industry panels reachable; differentiate company from fund data, observed prices from model scores and rejected/uncertain evidence from approved input. Do not infer a thesis link from an unrelated first neighborhood row. Do not treat missing position fields as confirmed non-holdings or unknown evidence as passed. Preserve dates, uncertainty, rejection reasons, source excerpts and source policies.

Use authenticated GET-only bounded reads and exact resource/linked-record validation. Partial or optional failure must not erase usable primary analysis. Preserve existing documented aliases only after inspecting backend resolution. Do not expose internal storage, tokens or raw errors. No new generated investment claims or fictitious charts.

## Acceptance

Saved API contract/model/transport tests; production desktop/mobile browser cases for actual company/evidence links, optional failures/slow bodies/wrong identities, explicit daily return, stock/fund distinctions, missing/rejected/cluster evidence, accessibility and page-width overflow. Run existing unit/build/type/audit and all browser suites; inspect real captures before develop integration. Source export, when needed for the DNS-restricted local sandbox, is temporary, read-only, credential-free and removed from the final diff.

## Boundaries

No main, backend/schema, financial scoring/weights/benchmarks/evaluation changes, orders, portfolio mutations, broker actions, secrets/accounts/AWS, dependency lockfile, scheduler or production deployment. Actual EC2 data comparison remains unverified unless the existing authorized runtime is actually available; synthetic browser fixtures are not live evidence. Record exact verification and remaining limitations in the task handoff.
