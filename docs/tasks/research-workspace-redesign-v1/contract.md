# Research workspace redesign v1

User requests continued development and an overall UX/UI/design overhaul, not another isolated memo patch. Base: develop@9aa401882cd9b8b1a5b4a50d0673966c1f2b2e20.

## Product and design

Research-first, information-oriented: market/theme discovery -> company evidence -> investment memo -> holding review -> measured outcomes. Reuse existing analyses and preserve unknown/source-limited/date boundaries. No personal trading advice or new automated financial actions.

Rebuild the global application shell and navigation, design tokens, typography, shared page/section/table/card/status patterns, responsive behavior, home research layout and memo reading navigation. Target a calm professional research workspace with a compact persistent desktop rail, clear page context, white reading surfaces, restrained indigo accent, real data hierarchy, and accessible mobile navigation. Do not add decorative charts, invented market performance, fake search, fake notifications, or non-functional controls.

Use official Koyfin watchlist/dashboard information architecture and Linear's sidebar hierarchy as structural references, not copied branding/assets. Prioritize data legibility, quick research access and concrete source links over oversized landing-page heroes. All existing routes must remain discoverable.

## Scope and verification

Frontend app/shell/shared components and key research views; existing test fixtures extended to cover shared navigation, keyboard/escape/focus, active route hierarchy, responsive layouts, empty/error/loading states and actual rendered paths. Run full frontend unit, production build/typecheck, full/production audit and desktop/mobile Playwright. Inspect real browser captures and revise visible defects. Record exact changes, tests and limitations before merging develop.

Read the existing intended runtime documentation; do not guess a DB or create a replacement. No AWS/account/credential access, production deployment, live database write, schema, scoring/weight/benchmark/evaluation split, portfolio or broker mutation. Existing source-date and exact-thesis protections remain. Main unchanged.

The sandbox cannot resolve GitHub for a clone. A short-lived branch-only read-only source snapshot workflow may export tracked source for local editing; it must be removed from the final tree. No production secret is required.
