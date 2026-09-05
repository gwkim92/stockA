# News triage and theme review v1 — handoff

## Integration tracking

PR #34 on `codex/news-theme-triage-v1`, based on develop@861f7f09402b342dd94a190b4767a010be906892. The PR records the final verified feature head, merge SHA and post-merge workflow result. Do not treat the checkpoint below as verification of a later untested change.

## Delivered

- `/events`: article-first reading, literal current-page search, missing interpretation/source and restricted-input filters, explicit source/evidence/company/theme links, and retained original titles/source dates.
- Real cutoff-date/symbol/theme API queries and opaque server-returned cursor pagination. Changing server criteria resets pagination; local selection and cutoff date survive refresh, history and page navigation.
- `/themes/[themeKey]`: connected-company search and missing-thesis filtering, actual company/thesis/recommendation links, separate stored cycle history/model features, source-news reading and historical-query limitations.
- Missing versus empty versus failed responses, measured zero, duplicate source relationships and duplicate/unknown history remain explicit. No fabricated transitions, daily freshness, translations or quality approval.
- Body-inclusive five-second deadlines, server-side read authentication, no-store/no-redirect and safe failure presentation. No automatic financial actions or persistent triage writes.

## Verified checkpoint

Feature head `4eac7f0b1efda274c8cb295868699ae8ac9c3887` passed Web Product Quality run `33973185308`, job `101325210385`:

- 33 unit test files / 371 tests (43 new news/theme cases).
- Locked install, production build and generated-route TypeScript check passed.
- Five browser reports: 64 home/discovery, 32 holdings, 34 readers, 44 company/evidence, 36 news/theme; total 210 expected, zero unexpected/flaky/skipped.
- Both complete and production dependency audit inventories contained zero findings at inspection time. Existing high/critical audit gates remain blocking.
- Actual requests verified paging, reset after new server criteria and historical date propagation. Browser clicks verified news -> theme -> company and news -> interpretation -> source. Tests also exercised missing/duplicate state, rejection, literal markup, timeouts, accessibility and width overflow in the tested states/viewports.

Artifact `9971595488` was downloaded, verified against SHA-256 `ad6fe1d077ca43f9bccb187189320d785d9b29269b49de30cd1d2dee20a2ce69`, and inspected. All five HTML report statistics and both audit JSON files were examined. Actual news/theme desktop and mobile captures were reviewed. A follow-up removes repeated top-of-page content so the first mobile news-source action is reached sooner; new browser assertions cover its actual position, a mismatching symbol response and retry preserving the historical date/local query. The final PR-head workflow must verify that refinement and its captures before integration.

## Execution limits

Full locked install, unit/build/type/audit and browser execution runs on the clean GitHub runner, not a claimed complete local npm installation. A source archive from the earlier task was inspected locally for the unchanged event/theme/pagination contracts; it is not a complete current checkout. This task adds no source-export workflow.

The existing event/theme API is read without backend changes. The theme backend may label a requested date while returning its last available cycle, limits related lists, and links the latest active thesis rather than reconstructing its historical state. These limits are stated in the UI. The pagination implementation remains the backend's existing offset cursor and does not guarantee immutability under concurrent ingestion.

No main, dependency/lockfile, backend/schema, financial scores/weights/benchmarks/evaluation split, portfolio/order/broker, account/secret/AWS, scheduler or production deployment changes. Actual EC2 data/host validation, complete backend regression and investment outcome validation are not performed. Browser document/financial values are synthetic. No independent reviewer approval is claimed.

One initial tree write returned an undetermined-security block; an identical normal-tool retry succeeded. No alternate upload path or permission change was used. Further persistent decision history or live-data rollout requires its own bounded task; do not describe this read-only selection workflow as an execution engine.
