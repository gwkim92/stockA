# Equity atomic persistence — implementation review

Base: develop@e6343653fc364641ab0ee09fd75132fa1d538cfc. PR #40. This task repairs the persistence boundary after per-symbol isolation; it does not modify model instructions, financial calculations, or production infrastructure.

## Reproduction and change

The old runner used separate PsqlCommandExecutor calls to insert a successful model invocation and upsert its equity report. Each call has its own psql process/connection. The committed-write regression reproduces an invocation row surviving when the subsequent report insert violates a constraint.

The new primary path composes the existing invocation and report SQL builders into one data-modifying CTE statement, then writes a result receipt in the same statement. An error in any part rolls back all three. The correct running pipeline row and a valid receipt container are mandatory. If the guard update writes zero rows, a runtime aggregate-based assertion raises a statement error; returning an empty result would not be sufficient because data-modifying CTE writes can still execute. Tests check a missing/wrong/closed run, invalid JSON containers and duplicate request receipts.

The renderer replaces only the known RETURNING tail of the existing SQL, not semicolons or arbitrary source substrings. A changed builder shape fails explicitly. All existing report fields, source IDs, UPSERT conflict key, invocation columns, output validation and financial semantics remain. No migration or new table is introduced.

## Durable record and acknowledgement

Application receipt policy: equity_atomic_result_v1. Storage namespace: ops.pipeline_run.config_json.equity_result_receipts_v1, keyed by the existing request hash. This is a new application-level record inside an existing JSON column, not a database-schema change. Other configuration keys are preserved.

The receipt records run/request identity, primary or fallback outcome, the corresponding invocation ID, artifact ID, instrument/date, provider/model, and SHA-256 fingerprints of the returned stored invocation and report rows. Fingerprints use PostgreSQL JSONB text, excluding created_at because it is not content and its serialization is session-time-zone-dependent. They detect changes relative to the stored receipt; they are not signatures, an immutable archive or evidence that the underlying analysis is true.

The batch counts a report only after a strict acknowledgement and receipt validation: exact keys, integer identities (not booleans), matching run/hash/instrument/date/provider/model/outcome and correctly shaped fingerprints. Request hash remains in structured error results for subsequent diagnosis. Receipt provider/model labels are excluded from exception text alongside existing top-level redaction. Lost or malformed acknowledgements remain uncertain, do not trigger a new model or fallback call, and do not increment confirmed-write counts.

## Fallback and failure semantics

A failed primary invocation is an actual failed attempt and remains an independently recorded audit entry. When deterministic fallback succeeds, its report and receipt commit atomically, referring to the exact existing failed invocation in the same run/request/template. No successful model invocation is invented. If fallback generation or persistence fails, the earlier failed attempt can still exist; no fallback result is falsely acknowledged.

The prior per-symbol rules remain: input faults and unsuccessful fallback are item-local, storage failures and cancellation stop the batch, and partial batches do not become complete successes. Final pipeline status updates, prompt registration, preparation and external model generation are not part of the per-item persistence statement.

## Read-only reconciliation

reconcile_result(executor, run_id=..., request_hash=...) issues one read-only snapshot SELECT. It compares the receipt with the exact invocation status/task/hash, report identity/source run, and both current fingerprints. It reports matching, conflicting or not_observed. Every result has automatic_retry_allowed=false.

No receipt is not proof that no operation committed: this can be a legacy run, a missing record, a concurrent transaction not visible to the read, or incomplete evidence. A matching receipt establishes a current record match, not permission to replay the model or mutate pipeline status. A later run can overwrite the existing natural-key report; its earlier receipt then becomes conflicting. Database outage is an exception, not a not_observed result. Damaged receipt IDs fail validation without unsafe SQL casts.

The refined query casts only a validated, bounded receipt value to bigint; it does not cast the indexed invocation/artifact primary-key columns to text. This preserves index eligibility but is not a claimed measured performance improvement. Actual workload query-plan/latency testing remains outside this task.

## Duplicate and concurrent writes

A second result with the same run/request hash cannot replace the receipt. The whole duplicate statement, including any speculative log or report write, is rolled back. Concurrent same-key tests require one committed log/report/receipt pair. Concurrent different-symbol tests verify both receipt entries survive the JSON update. The database may consume sequence IDs during rolled-back attempts; gapless IDs are not promised.

This refusal is not an idempotent replay API, automatic retry policy, or cross-run exactly-once model execution guarantee. A new run retains the pre-existing report UPSERT semantics. Recovery operators must account for in-flight work and conflicting/overwritten records before retrying. No new operations CLI or UI for reconciliation is added; the implemented API is the read-only Python function.

## Verification scope

The existing 226 deterministic cases are retained, with 21 new SQL-shape, acknowledgement, reconciliation and batch-integration cases. Fake executors now return synthetic atomic acknowledgements; they do not claim SQL execution. The old two-write failure injection is replaced by a single result-write failure at the batch boundary, while individual subwrite failures move to real PostgreSQL tests rather than being dropped.

The dedicated PostgreSQL suite uses the original checked-in table definitions for ops.pipeline_run, ai.prompt_template, ai.model_invocation and research.equity_research_artifact. Only the ref.instrument foreign-key target is a minimal test stub. This is not a full migration graph or full production schema test. Every case starts in the specifically named disposable CI database, performs committed writes on separate connections, and removes its schemas with a cleanup assertion. Runtime DB URLs/hosts are not accepted and no host database port is exposed.

Cases cover old-defect reproduction; primary/fallback success; each subwrite constraint failure; existing-report preservation on failed UPSERT; missing/closed/wrong runs; malformed receipt containers/identifiers; duplicate/concurrent submission; report/invocation mutation; later-run overwrite; literal source text/time zones; and the actual batch runner with an acknowledgement failure injected only after the real database COMMIT. The last case proves a current matching result can be observed despite a failed caller acknowledgement; it does not simulate every network/crash failure mode.

Checkpoint head 7a6cbabeb8243dd451d6409fa21ac196ce45eb1d passed all four CI jobs in run 34024393770. Its atomic report contains 21 tests and 187 SQL executions, zero failures/errors/skips. Subsequent refinement adds one malformed-ID SQL case (22 cases total), bounds receipt-side casts and adds workflow triggers for the referenced DDL files. The final refined head must pass again before integration.

## Explicit limitations

No main, frontend, dependencies/lockfile, production database/EC2, migrations/schema/seeds, prompts/scoring/weights, benchmark/evaluation/golden changes, portfolio/order/broker, accounts/secrets/AWS, scheduler or deployment changes. The temporary read-only tracked-source export is removed. Existing prompt hashes, source cutoff and model/fallback policy are unchanged.

No live model calls or investment performance claim. This is per-item atomic persistence plus explicit read-only reconciliation, not durable scheduling/retry of every batch item, an atomic external API call, atomic whole-batch completion, immutable report history, or proof of semantic source entailment. The existing failed-run status helper is still best effort. No independent reviewer approval or complete backend regression is claimed.