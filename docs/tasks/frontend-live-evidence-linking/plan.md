# Frontend Live Evidence Linking Plan

## Steps

1. Add regression assertions for event list, theme detail, source document detail, and AI evidence detail SQL matching.
2. Extend live adapter evidence joins from event-only to event-or-source-document linkage.
3. Extend detail route identifier matching for prefixed external source document IDs and opaque event IDs.
4. Update the static evidence navigation link to a live evidence identifier.
5. Run focused backend tests, frontend type/build checks, API/browser smoke, and update handoff/review.

## Non-Goals

- New AI extraction pipeline behavior
- Schema migration
- Recommendation scoring changes
- Trading or scheduler activation
