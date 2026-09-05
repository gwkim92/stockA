# Investor Home Reliability v1

## Request and product goal

Re-review what stockA was intended to build, then improve the actual product. The source of intent is `docs/project-foundation.md`: continuous market understanding -> independent theme/sector cycles -> company thesis -> recommendation -> ongoing holding review -> measured outcomes. Medium (about 3 months), medium/long (3-12 months), and long (1 year+) horizons; paper-first, not autonomous trading.

## Review finding

The previous analysis understated the repository: live API adapters, professional equity/fund analysis, AI providers, and EC2/systemd operating evidence already exist. Repository evidence is not proof that the remote deployment is healthy today. Absence of a stockA Neon connection does not establish absence of the documented EC2 database.

Recent work improved weight-review audit plumbing, but more lineage/approval/observation wrappers are not the immediate product bottleneck. The existing home page fails as a whole when any of seven API calls fails; ignores fetched health; maps missing failed-job counts to zero; labels any non-blocked trading state as validation-ready; and calls undated evidence "new". Improve this user-facing path before expanding audit layers.

## Scope

- Home page: market-cycle changes, investment candidates, supporting news, holding-review priorities.
- Independent, bounded, read-only source requests: one failing or slow feed must not discard successful feeds.
- Explicit unavailable, invalid, historical, future-date, and unknown-date presentation; do not turn unknown into zero/healthy/ready.
- Preserve backend recommendation ranking and permissions; source-blocked status takes precedence over paper-input flags.
- Display evidence dates separately from response-generation time. Historical is a date label, not a newly approved investment freshness policy.
- Replace unused/irrelevant home dependencies with the existing cycles endpoint.
- Unit tests, production type/build checks, and desktop/mobile browser tests using an isolated HTTP fixture server.

## Non-goals

No scoring formula/weight/benchmark/evaluation split/schema changes; no broker, order, allocation, scheduler, credentials, production deployment, live DB query, or new backend gate. No new database required. Existing API DTOs and deeper pages stay compatible.

## Acceptance

Home renders when one/all feeds fail; request time budget includes response body; no raw service error/secret reaches the UI; null counts remain unknown; genuinely empty successful responses differ from failed responses; past/future/missing evidence dates remain visible; theme transitions require both previous and current states; frontend never infers live-trading permission. CI covers frontend files rather than only weight-audit modules. Record actual results and limitations in handoff before integration into develop.
