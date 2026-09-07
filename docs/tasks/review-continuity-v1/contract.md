# Saved-review continuity v1

Continue user-facing stockA development after PR #43 at develop@80bf691b7a5d4a51485dd508b276c2a84148b3db. The user requests continued implementation. Follow the recent source -> human review -> inbox workflow, not a change to the separately gated investment-weight pilot.

## Reproduced code gap

The inbox validates and retains symbol + instrument ID, including two instrument histories under the same symbol. Its current-research link transmits only the symbol. The current company route therefore cannot know which saved review was selected and can display a different instrument's editor without explaining the lost identity. Fix that handoff and provide a read-only comparison of the selected saved judgment with the current displayed analysis basis.

## Delivery

Include only the validated saved instrument identifier in a dedicated query parameter; do not put note bodies, search terms, checklists or arbitrary storage keys into URLs or requests. Reuse the current company reader and v1 strict draft validation. Load only the explicitly selected canonical local draft key. Missing/corrupt/denied/duplicate/invalid references must not silently select another draft. Distinguish same displayed analysis basis, changed basis and changed instrument. Never attach an old instrument's note to a different current instrument, migrate it automatically, or expose the editor for an unresolved handoff. An explicit link may open the current company review independently; it must not copy the selected old draft.

Show saved human notes separately from current stored analysis and invalidation conditions; a basis match is not evidence truth, source-version equality, investment approval or a historical diff. Old notes do not contain old report bodies, so do not fabricate a before/after report. Source switching must retain the selected identifier and unsaved edits. External storage changes must be visible without silently replacing the comparison baseline. Preserve existing draft storage and explicit migration/reset semantics.

## Verification and visual boundary

Add model/transport-free tests and actual production-browser handoff/failure/identity/source-switch tests in the existing notebook suite on desktop/mobile Chromium and mobile WebKit. Retain all existing unit/build/type/audit/browser gates. No relaxed assertions, blanket retries or skipped existing cases. Record exact observed feature and merge results.

Manual screenshot review from PR #43 remains open: local container execution currently raises ClientError and Files cannot read the ZIP's pixels. Retrieved artifacts are not proof of visual inspection. New captures should be retained, but neither screenshots nor UI polish may be reported visually inspected unless actually opened. Automated accessibility/layout checks are a separate type of evidence.

## Exclusions

No main, backend/schema/migrations/seeds, dependency/lockfile, financial calculations/weights/thresholds, evaluation/benchmark data, portfolio/order/broker, accounts/secrets/AWS, paid model calls, production data/EC2, scheduler or deployment changes. No new persistent storage, imports, reminders, server sync or account encryption. Repository writes use the connected GitHub tool. No independent review or live financial accuracy claim.
