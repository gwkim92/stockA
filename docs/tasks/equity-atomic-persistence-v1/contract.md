# Equity atomic persistence v1

Continue after PR #39. Base develop@e6343653fc364641ab0ee09fd75132fa1d538cfc. User requests thorough continued implementation.

## Goal and bounded scope

Prevent a successful primary invocation being durably recorded without its equity report when the subsequent write fails. Reuse the existing SQL builders inside a single PostgreSQL data-modifying CTE statement. Store a versioned result receipt in the existing ops.pipeline_run.config_json alongside the report, without changing database schema. Require the expected running pipeline row. Keep failed primary invocation audit records when fallback generation fails; do not invent a successful model call for a deterministic fallback.

Implement strict acknowledgement validation and a read-only reconciliation function keyed by run ID/request hash. Reconciliation compares durable receipt, exact invocation identity/status and current report content fingerprint. Missing/conflicting/overwritten results are not proof of rollback or safe automatic retry. No implicit retry, paid model call, new scheduler or exactly-once claim.

Preserve per-symbol isolation, fatal storage-error and cancellation behavior, UTC cutoff, input/output/prompt contracts, report source inventory, provider/fallback selection and scoring semantics. Add actual PostgreSQL committed-write/rollback tests using existing table definitions in a dedicated ephemeral CI service, not only fake-executor assertions. Verify primary and fallback paths, insert/update failures, receipt failure, lost acknowledgement, tampered/overwritten records and missing/mismatching reconciliation. Existing prompt and cutoff regression gates remain intact.

## Boundaries

No main, production DB or replacement runtime, migrations/schema/seeds, dependencies/lockfiles, prompts/weights/benchmarks/evaluation split/golden changes, frontend, portfolio/order/broker, accounts/secrets/AWS, scheduler or deployment changes. The new JSON receipt is an explicitly documented application record in an existing config column, not a schema migration. Existing failed-run status marking and full run lifecycle remain separate, not atomically finalized with each item. No full historical reconstruction or source-entailment claim.

A temporary read-only tracked-source export for local work may be used and removed from final changes. No credentials or runtime files. Record exact verified head, test evidence, failure cases and limitations before develop integration.