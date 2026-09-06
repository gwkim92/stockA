# Personal review inbox v1

Continue the investor-facing workflow after PR #42, based on develop@b1bbba534d26ee95a1ff612bb66c344107a021b7. The user's continuation authorizes implementation on a feature branch and verified develop integration, not deployment or financial-rule changes.

## Outcome and sequencing

Add /research-notes: find saved company review notes across symbols, prioritize directly chosen next-check dates, read full saved notes without depending on the company API, export notes, then deliberately reopen the company's current research. This follows the recent user-facing research workflow, not the older roadmap's separately gated weight-review pilot. No new diagnostic dashboard or fabricated investment conclusions.

## Boundaries

Reuse the exact v1 local draft schema and keys. No automatic migration, local draft mutation, account binding, new persistence, imports, calendar events or reminders. Reading notes must not fetch each company's API or transmit search/note text in URLs/requests. Search stays in memory. Only validated canonical symbol/instrument keys can generate research links. Malformed/foreign/unsupported drafts remain untouched and visible as unreadable items. Bounded enumeration and read failures must not be presented as a complete empty library. Saving one company in the existing editor must remain compatible with the inbox.

The inbox is a saved human-notes reader, not a current source/claim snapshot. Never invent company names, source contents, fresh analysis or verified checks. Exported notes clearly identify their saved basis and omit live analysis. A browser-local day is explicitly labeled and refreshed; dates are user notes, not scheduled tasks. No offline application/service-worker claim: the app server must remain reachable even when the company API is unavailable.

## Verification

Use model tests for identity/schema integrity, date boundaries, search/sort, corrupt/denied/partial storage and literal export. Production browser tests must cover real editor save -> inbox read -> current review navigation; filters/search, reload, blocked and empty storage, API-down reading, cross-tab changes, exports, no note-bearing requests, mobile keyboard/touch, width and accessibility. Inspect actual screenshots. Retain all existing unit/build/type/audit and six browser suites. Record observed counts rather than expected estimates; correct the prior PR #42 unit count if logs disagree.

## Exclusions

No main, backend, DB/schema/migrations/seeds, financial calculations/weights/thresholds, evaluation/benchmark data, portfolio/order/broker behavior, dependencies/lockfile, paid model calls, accounts/secrets/AWS, production EC2, scheduler or deployment. GitHub connector writes only. Existing browser-local warnings remain. No independent reviewer or live-data/model-quality claims.