# Equity context cutoff v1 — handoff

## Integration record

Branch codex/equity-context-cutoff-v1, PR #38, based on develop@d7ad05cbd7599d5cdb5fb8782b84b4cdca945448. This task repairs historical thesis/event selection in equity_research_reporting.py. The exact final feature head, integration SHA and post-merge check are recorded on PR #38. Do not use this implementation checkpoint as evidence of a later untested code change.

## Delivered

- Thesis creation and event occurrence use an explicit UTC-exclusive next-midnight cutoff, independent of the PostgreSQL session timezone.
- A future recommendation-linked thesis cannot bypass the filter. Eligible linked thesis is preferred, then newest creation time/ID; current active status no longer reorders past candidates.
- Preserve creation timestamps, mask future closure/status instead of inventing historic active status, and label current stored fields as unversioned.
- Query and prompt explicitly state the partial temporal policy and point_in_time_complete=false. Existing provider/hash/source-inventory alignment is retained. Template becomes 2026-09-06-equity-cutoff-v1; output/storage schema and other runtime functions are unchanged.
- Add ten offline contract cases and thirteen real PostgreSQL cases. A disposable no-published-port GitHub service is a synthetic rollback-only fixture, not a replacement production database.

## Verified implementation checkpoint

Head 8412c575e5b7e54c133552de64b09f8d5a7b0400 passed Analysis Prompt Quality run 34013926779:

- Python 3.11 job 101434354993: 196 cases, zero failures/errors/skips/unexpected IO attempts.
- Python 3.13 job 101434355036: the same 196 cases, zero failures/errors/skips/unexpected IO attempts.
- PostgreSQL job 101434354877: 13 cases, zero failures/errors/skips; report records 27 SQL process executions including identity/cleanup checks. PostgreSQL reported 16.15 (Debian 16.15-1.pgdg13+2).
- The unit suite is the existing 186 cases plus ten new ones. The database suite has thirteen different cases. Do not sum repeated Python execution into unique-case counts.
- Optional SDK 0.17.8 installed from the already-declared extra; SDK Runner remains mocked. No paid model generation or production data access.

All three checkpoint archives were downloaded, hash verified and their reports/logs inspected:

- 9983314273, Python 3.11: 52ddec86f74a8615a439e2e241e137a82b61574d4b9e2accebd65f803f8cb3fa.
- 9983313750, Python 3.13: 2d913599c310c1c2b5475747b058bd6d91a3364d18c0d713e64229497fab5202.
- 9983314829, PostgreSQL: 91c67db000cbdb468b8517a5466759424a416808010b234df96adbf188a55128.

This handoff and review document are the only additions after that checkpoint. Their final head must still pass all three jobs before integration. The PR holds final artifact/run evidence.

## Local verification and correction

The local source workspace is based on a prior tracked archive. The affected base equity module was reconstructed from actual PR #37 changes and its blob matched GitHub exactly (634348bea83db09e56dc1eb60d23129d69cb7585). The frozen baseline SQL fixture exactly matches that module's generated AAPL / 2026-09-05 / limit-50 SELECT. It is not an imagined baseline.

All ten new local unit tests pass. The final uploaded runtime blob ea625694eb474ca75b0b69604c09cd768b302837 matches intended local bytes. AST comparison identifies only render_equity_research_context_sql and build_codex_oauth_equity_research_prompt as changed definitions. The template constant also changes. A standalone function-name expression accidentally included in the first upload was caught by diff review and removed before the passing checkpoint. No complete local current checkout, PostgreSQL execution or full local regression is claimed; clean GitHub checkout executes the full selected unit suites and real SQL cases.

## Limits and next priorities

Creation/event-time filtering is not full knowledge-at-the-time reconstruction. Current stored thesis body/status, later translations/impacts, source ingestion time, recommendation updates and other mutable snapshots can still contain later information. No historical revision table or schema change was added. The query states this limitation and the prompt must not present these fields as proven contemporaneous knowledge. Other frontend/model query paths are out of scope.

The PostgreSQL fixture validates execution and timestamp semantics for the consumed column types, not full migrations, production query performance or actual data completeness. Full backend regression, historical versioning, semantic claim-to-source evaluation, current workload rejection rate and mixed-symbol failure isolation remain unverified. No frontend changes or new browser verification took place.

No main, production DB/EC2 or replacement runtime, migration/seed/schema, dependency/lockfile, financial scoring/weight, benchmark/evaluation split, portfolio/order/broker, AWS/accounts/secrets, scheduler or deployment modifications. No independent reviewer approval or live model accuracy is claimed. The deliberate disposable test-database calls must not be described as no database execution at all.