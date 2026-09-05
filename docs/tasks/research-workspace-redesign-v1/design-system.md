# stockA research workspace — design decisions

## Information architecture

The application is a research workspace rather than a marketing landing page. Its shared shell separates **탐색과 판단** (home, market, cycles, news, companies, candidates) from **검토와 성과** (holdings, outcomes, paper validation). Secondary evidence/operations routes remain available through the expandable rail and the same quick-navigation dialog. Existing routes and backend contracts remain unchanged.

Desktop has a persistent 216px navigation rail (192px at the intermediate breakpoint), contextual top bar, and bounded reading width. At 760px and below the rail is replaced by a bottom dock; the full navigation is still available in a native modal dialog. Native dialog modality, Escape closing and focus return are tested; Cmd/Ctrl+K and direct ticker navigation use no financial write action. Page search is local navigation filtering, not a claim to search every instrument or document in a database.

## Visual hierarchy

- Canvas `#f6f7fb`, white reading surfaces, primary ink `#18223b`, secondary `#4e5c75`, muted `#626f86`.
- Restrained indigo `#4d46cc` marks navigation/action; green, amber and red communicate distinct semantic states with text, never color alone.
- Shared spacing scale of 4/8/12/16/20/24/32px; 6–12px corner radii and restrained shadows distinguish surfaces without turning every datum into a floating card.
- System/Pretendard/Inter fallback stack and tabular numeric glyphs; no external fonts or decorative media required for the page to render.
- Compact page title and metrics; facts, evidence links and actions appear before detailed operating information.
- Reduced-motion preference disables transitions and animation. Keyboard focus is visible. Mobile bottom navigation reserves safe-area space.

These choices are applied to the shared shell, tokens, common sections/status/table/reading components, home, candidate explorer and memo navigation. They do not imply every deeper page has received an individually bespoke redesign or a new live-data validation.

## Functional improvements

Home arranges actual cycle-state observations, candidates, holding review and news in a two-column workbench. Missing feeds remain local errors; historic/unknown source dates and unknown counts remain visible. Candidate filters operate on the current returned list and preserve its original order, scores, permissions and missing-data semantics. They do not create a new ranking. Memo chapter links scroll to real existing claim/catalyst/risk/invalidation/review/value/source sections.

Error, loading and missing-route states retain useful navigation and never replace errors with fabricated healthy numbers. No fake performance chart, unread notification, user account, favorite action or unimplemented server search has been added.

## References used for structure, not copying

- Koyfin My Watchlists: https://www.koyfin.com/help/mywatchlists/ — visible securities, contextual detail and list organization.
- Linear Search: https://linear.app/docs/search — navigation search and keyboard access.
- Linear Custom Views: https://linear.app/docs/custom-views — coherent hierarchy for filtered work views.

No logos, screenshots, assets or commercial interface were copied. stockA's backend/evidence constraints determine its own interaction and naming.

## Verification boundary

The frontend workflow exercises the production Next build with a localhost HTTP fixture API. Actual browsers test the shell, search/filter interactions, focus/escape, source-failure behavior, memo links, accessibility and overflow at desktop/mobile widths. Visual captures are inspected before integration. Fixture values are synthetic and are never presented as live recommendations. Current EC2 availability, live data quality, backend regression, investment outcomes and production deployment are out of this task's verified scope.
