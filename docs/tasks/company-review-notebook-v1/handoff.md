# Company review notebook v1 — handoff

## Integration tracking

PR #42 on codex/company-review-notebook-v1, based on develop@d9a154d6cb70c5e2ef817c755baa7e514bfe7df3. The PR records the final verified feature head, merge SHA and post-merge run. Do not treat the initial failed run below as verification of a later revision.

## Delivered workflow

The company investment case links to `/stocks/[symbol]/review`. Stored claims, risks, invalidation conditions and catalysts appear beside one explicitly linked source. A human review section provides judgment notes, opposing evidence, next-check text/date and manual checkboxes. The existing news -> company -> notebook -> source detail navigation is retained and browser-tested. Fund exposure/cost/limits remain distinct from company claims.

Only source document IDs in the returned company research/direct-event/background inventory can be requested. Invalid, unrelated or repeated source query parameters do not fetch or substitute another document. Source reading uses the existing authenticated bounded server reader, separated with Suspense so a source failure does not erase primary analysis or the editor. Existing backend aliases and source-summary/partial-history limitations remain visible. No source-to-claim entailment, model output or investment conclusion is manufactured.

## Draft storage and export

Explicit-save localStorage drafts are namespaced by symbol and instrument. They are not account-scoped, encrypted, server-backed, synchronized, durable audit history or calendar reminders. The interface warns against shared-device storage. Data clearing/private browsing may remove drafts. Primary company API failure still prevents this route from opening; the feature is not offline-first.

The SHA-256 bundle fingerprint covers the displayed analysis and connected-document inventory/dates, not immutable source text or all underlying financial fields. When it changes, old notes remain readable, save is blocked until explicit text migration, and manual checks are reset on migration. Previous stored data remains until the user explicitly saves. A stale export excludes the new bundle's analysis/source inventory rather than attributing it to the older note.

Corrupt local drafts are preserved and can be exported as raw text before explicit deletion. Storage refusal leaves in-memory writing and export available without claiming save. Observed cross-tab changes and a pre-write/pre-delete comparison block silent overwrite, but this is not an atomic multi-tab transaction. Only the selected company's key is deleted. Beforeunload and explicit cross-route navigation warnings do not guarantee survival after OS/app termination or every browser-history action.

Markdown export separates the person's writing from stored analysis; user/source strings are literal indented text, and source IDs form a connection inventory, not verified citations. No note or export is sent to the API. Manual checks never override source blockers or authorize trading.

## Observed verification and fixes

Initial feature head 1e38bfd8bfa0005f98b71b3bf000a8c6f978c6cd ran Web Product Quality 34042124667, job 101510669170. It passed 34 unit files / 409 tests (371 previous plus 38 new), production build, generated-route TypeScript check, both audit gates and all 216 existing browser cases.

The initial notebook suite passed 50 of 63 cases and failed 13. Twelve failures were exact-label lookup problems after value-bearing textareas changed; actual failure snapshots still show the expected notes. Inputs now have separate explicit label htmlFor/id associations, while exact-value assertions remain. One mobile WebKit layout check detected width overflow; date/select/fieldset sizing is tightened without hiding/clipping the page or relaxing the width threshold. Geometry is attached to the check for diagnosis.

Initial archive 9992136252 was downloaded and verified against SHA-256 a6e01689da85e66c6ba28a63c452fdefd06fc02f47a45228a1c0301c0b3270d4. All six report statistics and both audit JSON files were inspected; initial audits had zero findings. Desktop and mobile captures were reviewed. The mobile primary-save button was too compressed, so its full-row layout and reading font sizes were improved in actual UI styles. Persistent storage-error/conflict warnings now remain visible during further edits.

Refinement code is at fb7e92d70b7ce09295566a54136f3a7be276287a. It adds two scenarios (denied storage reads and cancelling dirty navigation), giving 23 notebook cases per tested browser, 69 total across desktop Chromium, mobile Chromium and mobile WebKit. Together with the existing 216, the expected browser total is 285; these are expectations until final reports are observed. No skips, retries or relaxed assertions are introduced. Final captures must be inspected before integration.

Local verification consists of strict TypeScript for model/data dependencies, TSX/test syntax, fixture syntax and focused compiled assertions. A full local npm install/Next build/browser run was not possible with the local DNS restrictions; clean GitHub runners execute the full workflow. WebKit device emulation is not physical iPhone/Safari certification. All browser company/document values are synthetic.

## Scope and safe continuation

Read review.md for the exact source/draft failure behavior. No backend, main, dependencies/lockfile, production DB/EC2, financial rules/weights/thresholds, schema/migration, benchmark/evaluation/golden data, portfolio/order/broker, account/secrets/AWS, scheduler or deployment changes. No paid model generation, live-data usability or model-accuracy claim. Temporary credential-free tracked-source export is removed from the final tree. No independent reviewer approval is claimed.

The next product evaluation should examine this connected review with authorized representative records and real user decisions, rather than treating passing synthetic browser tests as proof of useful investment analysis. Server-synced/account-scoped notes, source-version history, claim-level provenance and genuine reminders are explicitly separate features, not implied by this browser-local notebook.
