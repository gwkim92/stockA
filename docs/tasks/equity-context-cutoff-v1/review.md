# Equity context cutoff — correctness review

Base: develop@d7ad05cbd7599d5cdb5fb8782b84b4cdca945448. PR #38. This is a bounded repair of the equity reporting input SELECT, not a full point-in-time storage redesign.

## Concrete defects and selection change

The baseline equity query selected a thesis without a created_at bound and preferred the current active status. It also selected events with an inclusive next-midnight timestamp interpreted in the session timezone. Frozen baseline SQL generated from the byte-matched runtime reproduces both the future-thesis/next-midnight inclusion and different event sets between UTC and Asia/Seoul sessions.

The revised query uses the exclusive bound ((as_of_date + 1)::timestamp at time zone 'UTC') for thesis.created_at and event.event_at. The comparison is between timestamps with timezone, not a session-dependent conversion of a date or a date cast on the indexed source column. It includes the last microsecond of the requested UTC day and excludes the next midnight. An explicitly linked future thesis cannot bypass this predicate.

Among eligible theses, an explicit recommendation link remains preferred, followed by created_at descending and thesis_id descending. Current active status no longer affects the ordering. This is a documented selection change, not recovery of an unknown historic status. If a selected record closes at/after the cutoff, its future closed_at and present status are masked rather than guessed to have been active. A known earlier closure is retained. Selected thesis timestamps and status_scope=current_record_not_versioned make these distinctions available to the prompt.

## Prompt and provenance

The query includes temporal_policy=utc_creation_event_cutoff_v1, cutoff_timezone=UTC, the selection rule and point_in_time_complete=false. The prompt explicitly distinguishes a creation/event cutoff from knowledge-at-the-time reconstruction. Its effective template version is 2026-09-06-equity-cutoff-v1, so the previous template/cache identity is not reused unnoticed. Existing bounded source selection, source serialization and request hashing retain this metadata.

The current stored thesis body can have been changed after creation. Event text, translations, impacts, recommendation content, source availability and other snapshots can also be updated or ingested later. None of those becomes a certified historical version because its creation or event date passed this filter. No valid-time/transaction-time ledger or immutable thesis revision schema is introduced. Other frontend and model context queries are not automatically fixed by changing this equity query.

## Verification depth

Ten new deterministic tests cover SQL boundary construction, date/limit types, no active-state preference, explicit policy/date metadata, read-only/quoted SQL, metadata preservation in the prompt and fingerprint, and template version. The unchanged selected prompt regression suite runs with these additions: 196 cases on each of Python 3.11 and 3.13, with real socket/process guards maintained.

A separate job executes the full production SELECT in a disposable PostgreSQL service. The test schema contains only the typed columns consumed by this query; it is not the complete production migrations or an assertion that every deployment schema is compatible. All schema creation, synthetic rows and case updates occur in rollback transactions. No port is published and the runner addresses only the explicit GitHub service container's Unix socket and stocka_cutoff_test database. No runtime DSN or arbitrary hostname is accepted.

Thirteen PostgreSQL cases cover baseline negative demonstrations, UTC/Seoul/New York/Kiritimati sessions, both US daylight-saving transition dates, midnight/microsecond edges, future and valid explicit links, future batches, mutable status ordering, future/known closure, stable equal-time IDs, cross-instrument isolation and no eligible thesis. Another path carries the real SELECT result through a mocked provider and fake artifact executor to check that selected source IDs, prompt and cutoff metadata agree. The rollback test verifies that test schemas are absent afterward. These tests make real test-database calls; the offline unit suite remains separate and makes no real IO.

Local checks passed for the ten new unit cases and syntax. AST comparison of the final runtime and byte-matched baseline shows only the context SELECT renderer and prompt builder changed (plus the template constant). Other functions, including write SQL, financial/scoring behavior, output schema, provider and fallback code remain unchanged. An unintended standalone function-name expression was caught during upload diff review and removed before the verified implementation head; it is not in the final runtime. The final runtime blob matches local bytes: ea625694eb474ca75b0b69604c09cd768b302837.

## Remaining acceptance limits

No production database or EC2 query, live model call, deployment, main, migration/seed/schema, dependency/lockfile, financial weight, benchmark/evaluation split, portfolio/order/broker, AWS/account/secret or scheduler change. The added database is an isolated CI fixture, not a replacement service or a new environment for the user's data.

The sample schema is synthetic, so query planning and performance on actual row counts remain unmeasured. Neither semantic entailment nor model quality is evaluated here. Mixed-symbol overbudget failure isolation and complete historical versioning remain follow-up tasks. Do not use these results to certify a backtest or claim that all future-information leakage has been removed.