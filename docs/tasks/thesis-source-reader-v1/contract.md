# Thesis and source reader v1

Continue the user-requested overall research UX/UI overhaul after PR #31. Base: develop@165f7a722d21539d6ad64a076159e60338e33e9e.

## Goal

Complete the reading path from an existing company/recommendation/holding link to the stored investment thesis and its source evidence. Redesign `/theses/[thesisId]` and `/source-documents/[documentId]` around actual claims, conditions, recorded review, and original excerpts instead of large instructional heroes and inferred summaries.

## Findings to correct

The old source page generates topic sentences from title keywords and substitutes them for untranslated excerpt text. The thesis page counts every invalidation status other than `not_triggered` as triggered, and its normalizer assigns defaults to missing risk, currency and evidence counters. Remove fabricated certainty from these two readers without altering backend financial rules.

## Scope

Read the existing API contracts and identifier-resolution logic. Use bounded authenticated GET reads and explicit unavailable/invalid/unknown states. Present stored Korean summaries only when supplied; label stored excerpt summaries as summaries, not verbatim quotations or complete raw documents. Do not expose internal storage URIs or invent raw-download routes. Preserve source-access policy and valid deep evidence links. Separate unknown condition status from explicitly triggered conditions and a recorded latest review from an invented change history.

Compact article headers, real section navigation, readable original text, source metadata, functional local excerpt filtering, and mobile layouts. Existing company/recommendation scores, financial models, source permissions and deeper routes remain compatible. Preserve detailed thesis gates/valuation evidence as needed without placing operational information ahead of research content.

## Verification and limits

Test saved API examples plus adversarial identities, missing dates/counters/translation, condition statuses, excerpts, URL schemes, access flags, timeouts and failures. Production desktop/mobile tests must follow actual links, use synthetic HTTP fixtures explicitly, and test accessibility, keyboard use, overflow and reading hierarchy. Full existing frontend regression/build/type/audit gates remain required before develop integration.

No main, dependency/lockfile, backend/schema, scoring/weight/benchmark/evaluation split, account/secret/AWS, portfolio/order/broker, scheduler or production deployment changes. The existing EC2 runtime is not connected here; synthetic fixtures do not complete live-data validation. Full execution may use clean GitHub CI because local GitHub DNS is unavailable. Keep edits bounded and record final evidence and remaining limitations in this task handoff.