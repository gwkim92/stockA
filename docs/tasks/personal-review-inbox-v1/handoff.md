# Personal review inbox v1 — handoff

Base develop@b1bbba534d26ee95a1ff612bb66c344107a021b7 (PR #42). This is an investor-facing continuation, not investment scoring, model generation or an operations dashboard.

## Implementation

/research-notes lists existing v1 browser-local drafts. A dedicated link from the company notebook and the research navigation opens the inbox. Search is literal and memory-only; note/search text is not added to URLs or transmitted to a company API. A user-chosen date classifies entries as overdue/today/planned/undated relative to the displayed device-local day. The day updates on visibility and once per minute; this is not a scheduler or reminder.

The reader shows the saved person's judgment, opposition, next question, direct checkmarks and original identifiers. It does not manufacture a company name, current source body, live analysis or a snapshot match. Reopening current company research uses the existing editor's exact instrument-scoped draft lookup and snapshot handling. API failure does not prevent this local-notes reader from loading, provided the Next application itself is reachable. No offline app/cache/service worker was added.

Only canonical symbol/instrument v1 keys and the unchanged strict draft schema are accepted. parseDraft's type signature now requires only the identity fields it actually validates; its runtime implementation and stored format are unchanged. No notes are written, migrated or deleted by the inbox. Broken, mismatched and unsupported entries remain as visible problems with a raw text export. Reads are bounded at 2000 total keys, 200 review keys and 1,000,000 counted characters; truncated/failed/changing reads are marked partial, not empty/complete. Observed cross-tab changes reload the reader, and a removed selected item has no remaining current-record link. This is not atomic storage or immutable history.

Individual Markdown export contains saved human notes and original IDs only, with all user text indented literally. Bulk JSON export contains all loaded valid notes, irrespective of the local search filter, with explicit scope/completeness/problem metadata. It is not a full-origin backup, account sync or an import/restore feature. Corrupt raw values are exported separately on demand. Shared-device/unencrypted storage limitations remain visible.

## Verification

Added model tests cover old-format compatibility, canonical/mismatched keys, malformed/oversized values, storage refusal, partial reads and limits, date boundaries, literal search and safe notes-only exports. Eleven additional production browser scenarios run on desktop Chromium, mobile Chromium and mobile WebKit alongside all 69 previous notebook cases. All five other browser suites, all units, production build/typecheck and existing audit gates remain unchanged.

The local container initially allowed source inspection and staging but became unavailable while attempting to open a locked test-runtime export. No complete local unit/build/browser execution is claimed. The temporary credential-free read-only export workflow is removed from the final tree. Clean GitHub CI is the executable verification path. Record actual final-head counts, failures, screenshot inspection status and integration status in the PR; expected totals are not evidence.

Correction to prior reporting: PR #42's job 101519053984 logs show 406 tests across 34 files, including 35 company-review cases. The previously reported 409/38 values were inaccurate. No tests were removed by this task; use observed runner totals.

## Remaining boundaries

No main, backend, DB/schema/migrations/seeds, dependencies/lockfile, financial calculations/weights/thresholds, evaluation/benchmark records, portfolio/order/broker behavior, paid model calls, accounts/secrets/AWS, production EC2, scheduler or deployment changes. No claims of live financial accuracy, physical iPhone certification or independent reviewer approval. Current analysis and recovered notes remain separate; server persistence and restore/import are not implemented.
