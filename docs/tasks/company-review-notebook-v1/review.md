# Company review notebook — product and data boundaries

Base develop@d9a154d6cb70c5e2ef817c755baa7e514bfe7df3. PR #42. This changes the user-facing research workflow, not model generation or investment execution.

## Delivered interaction

The existing company investment case now opens `/stocks/[symbol]/review`. Stored company claims, risks, invalidation conditions and catalysts are read beside one explicitly linked source. A separate personal section records the user's interpretation, opposing evidence, next question/date and manually marked checks. The existing news -> company -> notebook -> source detail route is tested through real clicks, not isolated component snapshots.

Company and fund projections stay separate. Stored model output, fixture/local-rules output and unknown generation mode are labeled differently. No Korean summary is generated from source keywords. A missing claim list is distinct from an explicit empty list. Source document inventory is a connection list, not proof that every listed document supports every displayed claim.

## Source selection and server boundary

Company reads use the existing exact-symbol parser and bounded authenticated GET. Only document IDs present in the returned research source inventory or direct/background events can be selected. A query pointing to an unlinked/invalid/duplicate source is not fetched and is not replaced by a different source. Selecting a valid source changes the URL without resetting the local editor. Source failures are isolated in a streamed section; primary company read failure still prevents this route from loading and this is not an offline-first notebook.

The existing source reader supports documented backend aliases; the UI labels that rather than claiming independent identity attestation. Excerpts are the existing API's stored summaries/excerpts, not guaranteed verbatim full documents. Public/source dates and periods remain visible; sources published after the company cutoff are flagged. Loading a document is not a semantic entailment check or a historical knowledge reconstruction.

## Personal draft semantics

Notes are explicit-save browser localStorage entries, namespaced by exact symbol and instrument. They are not per-account, encrypted, server backed, a persistent audit trail or synchronized between devices. The warning is beside the save interface. Shared-device use is discouraged. A typed next-review date is a note, not a reminder or calendar event. Checkboxes are the user's own marks, not system approval or source-gate overrides.

A SHA-256 fingerprint identifies the displayed analysis bundle: stored summary/groups, source inventory and dates/identity. It deliberately does not assert immutable source content or include every underlying financial/detail field. If the bundle changes, the old draft remains readable but cannot be saved as current. The user can explicitly carry over only note text with all checkboxes reset, then save the new basis. Before that save, the old local draft is retained. Stale exports do not attach the new analysis/source list to an old draft.

Malformed or unsupported local data is preserved instead of overwritten. A raw export is available before explicit deletion. Storage read/write failure leaves in-memory writing and plain-text export available, without claiming local save. Observed cross-tab changes and compare-before-write detect conflicts and stop overwrite; they are not an atomic multi-tab write protocol. Only the company's own key is deleted after confirmation. Other local data is untouched.

Dirty-note warnings are attached to beforeunload and explicit cross-route anchor navigation. They do not guarantee recovery after device/app termination, OS process death or every browser history action. This feature offers explicit save and export, not hidden autosave or a promise of durable unsaved recovery.

## Export and rendering

The `.md` export identifies human notes, the analysis-bundle basis/date and manual checks separately from stored model analysis. Connected IDs/paths are included only for the current bundle and are labeled an inventory, not verified citations. User and source text is indented as literal Markdown content; React escapes markup in the rendered interface. No source text is executed as HTML. The browser download is not uploaded to a server.

## Verification and limits

The feature adds model/transport cases plus production browser tests on desktop Chromium, mobile Chromium and mobile WebKit. Test records are synthetic. WebKit emulation is not a physical iPhone/Safari device certification. The existing locked installation, all/production dependency audit gates, unit regression, build/type checks and five browser suites remain. Final counts, screenshots, failures and integration SHAs are recorded in the handoff and PR only after they are observed.

No backend, dependency/lockfile, main, production DB/EC2, financial rules/weights/thresholds, schema/migration, benchmark/evaluation/golden changes, portfolio/order/broker, accounts/secrets/AWS, scheduler or deployment changes. No paid model call, live-data usability or model-accuracy claim. The temporary tracked-source export is read-only and removed from the final tree. No independent reviewer approval is claimed.

## Initial verification findings

Initial head 1e38bfd8bfa0005f98b71b3bf000a8c6f978c6cd passed unit/build/type/audit and all 216 existing browser cases in run 34042124667. The new suite passed 50/63 cases and failed 13: twelve exact-label lookups across edit/reload/migration/storage tests, and one mobile WebKit width assertion. The failure snapshots still show the expected textarea values; these failures are not evidence that stored notes were lost. Input labels are now separate explicit htmlFor/id associations rather than wrapping a value-bearing textarea, with the exact-value assertions unchanged. WebKit layout is tightened at fieldset/date/select minimum sizes without hiding or clipping the page. The width threshold is retained and geometry is attached for diagnosis. Mobile primary-save layout and reading font size were refined after actual screenshot review.

Persistent storage error/conflict messaging is separated from transient edit status so editing does not hide why saving is disabled. Two additional browser scenarios cover denied reads and cancelling a dirty-note navigation. A full note-section capture is added, not a screenshot-only UI restyle. The corrected final head must pass all browsers and have its captures inspected before integration.
