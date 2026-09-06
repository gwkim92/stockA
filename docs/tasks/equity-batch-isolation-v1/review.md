# Equity batch isolation — implementation review

Base: develop@5a76baa63011b984b9cb757cc9492989e2c1b7e0. Integration: PR #39. This is a batch orchestration repair, not a new financial model, historical version store or broker execution system.

## Reproduced failure

With synthetic AAPL/NVDA/MSFT contexts and an oversized NVDA thesis, the unchanged baseline raises input_budget_exceeded during eager tuple construction. The injected provider sees zero symbols and the fake executor records zero artifact writes. With the revised public runner, AAPL and MSFT finish, NVDA is explicitly rejected before provider execution, and the batch raises a structured partial-failure error. All six symbol order permutations are tested. Synthetic writes in this test are fake-executor SQL records, not production database writes.

The original runner also built fixture previews before real execution and included success-invocation persistence inside the provider exception handler. A broken preview could prevent a valid primary report; a persistence error could trigger a misleading model fallback. The new module separates these responsibilities.

## Failure boundaries

| Stage | Continue other symbols? | Artifact / invocation behavior |
| --- | --- | --- |
| Malformed JSON, missing/invalid instrument, wrong symbol/date, oversized bounded source | Yes | Fixed input error code. No invented invocation or report for rejected input. |
| Valid primary response | Yes | Existing schema validation and SQL builders. Count only acknowledged artifact writes. |
| Provider/response contract failure | Yes, after valid fallback or recorded item failure | Record a failed invocation with a sanitized code. Use the existing separately labeled deterministic fallback. |
| Deterministic fallback also fails | Yes | Symbol remains unreported; do not substitute an empty or fabricated successful report. |
| DB lookup, prompt registration, invocation audit write, artifact persistence or final success marking failure | No | Stop the batch; never call it a model error or switch to fallback. Mark the stage and possible unknown persistence outcome. |
| KeyboardInterrupt / SystemExit | No | Propagate interruption; do not convert it to an item failure or continue the next symbol. |
| Resource exhaustion | No | Batch-fatal diagnostic rather than further fallback generation. |

Only recognized PromptContractError input faults are item-local during preparation. DB/runtime exceptions are not broadly swallowed. Inputs are still prepared before provider work, so an infrastructure lookup failure deliberately prevents the batch from continuing; this is not a streaming/concurrent job system.

## Caller behavior and counts

An incomplete batch raises EquityResearchBatchError after eligible good items finish. It subclasses the existing ValueError-compatible contract error and exposes .report. The unchanged operations CLI therefore prints structured JSON diagnostics to stderr and exits 1, while the existing professional-coverage parent marks its run failed rather than accepting a partial return as success. Both paths are exercised through their actual handlers with fake external dependencies.

- Clean run: completed; normal return.
- Every selected item has a persisted primary/fallback report, with at least one fallback: completed_with_fallback; existing distinct run status retained.
- At least one report missing after item-local recovery: completed_with_failures (some saved) or failed (none saved); structured exception/nonzero CLI exit.
- Empty selection: completed no-op, run_id=null, complete zero counts.
- All inputs rejected: failed with no invocation, artifact or run writes. Diagnostics remain on the exception/CLI stderr, not a fabricated persistent model record.
- Dry-run: planned when preparation/previews pass, otherwise planned_with_failures via exception. No provider execution or writes. Valid previews remain available through .report even when another item fails.

symbol_count = inserted_artifact_count + unreported_artifact_count; inserted_artifact_count = primary_report_count + fallback_artifact_count. Results preserve selected symbol ordering. The legacy failed_artifact_count continues to include primary-provider failures that produced saved fallbacks; it is not synonymous with missing persisted reports. New explicit counters remove that ambiguity. not_attempted remains separate from failed.

Real execution intentionally returns an empty artifact_preview rather than requiring a redundant fixture preview before real work. Dry-run still previews the first three prepared contexts, with preview_symbols identifying those entries. No preview or model/source text is included in exception messages. Provider errors use fixed codes, not exception bodies. An old test requiring raw provider down text in SQL was updated to require provider_failed and verify the raw text is absent; fallback and success/failure assertions remain.

## Source preservation

The public reporting function keeps its signature/defaults and delegates to equity_research_batch.run_batch. The context loader keeps DB calls outside source parsing, then strictly decodes JSON. Exact query symbol/date and integer instrument ownership are checked before bounding/generation. An injected provider receives a defensive copy so it cannot mutate the selected context used for the request hash, fallback, output normalization or stored source IDs.

AST comparison with the byte-matched baseline shows only run_equity_research_reporting and load_equity_research_context change in the existing runtime file. All SQL builders, output schema, prompt text, template version, hashing/selection helpers and financial functions remain unchanged. The PR #38 UTC cutoff and source-provenance metadata retain their existing 13 real PostgreSQL regressions. No prompt version bump is needed because no prompt text is changed; batch policy is separately identified as per_symbol_failure_isolation_v1.

## Persistence is deliberately not overclaimed

Existing per-operation SQL writes are not atomic as a group. A successful model invocation can be recorded before an artifact fails. A database may commit a write whose acknowledgement is lost. persistence_outcome_unknown marks such stages; confirmed counts exclude the unacknowledged operation and do not assert that the database rolled it back. No automatic retries or new idempotency guarantees are introduced. A deterministic input-only failure can be corrected and explicitly retried for only that symbol; ambiguous persistence requires reconciliation first.

The existing _mark_pipeline_run_failed helper is best effort and can swallow a failure to update ops status. The new runner still raises a nonzero caller error, but does not guarantee that ops status was durably updated during an outage. This limitation is not disguised as transactional recovery. Durable run-item outcomes, transaction boundaries and reconciled retries remain separate work.

## Verification scope and exclusions

The new 30 tests cover permutations, zero/unknown/typed output, provider mutation, fallback failure, input identity/date validation, all-failed/no-op, every persistence stage, interrupts, dry-run, the actual CLI/parent and failed-symbol-only retry. The guarded 17-module suite keeps all 196 prior cases and adds these 30. CI must require the declared SDK extra with zero skips. The existing PostgreSQL job executes only the cutoff SELECT regression against rollback-only synthetic fixtures, not the new artifact write transaction semantics.

The initial local test harness looked for a standalone quoted ticker in artifact SQL when the real SQL uses instrument_id and a report title. Assertions were corrected to match the exact expected instrument ID and source list; product behavior was not weakened. Local selected execution has 226 cases with zero errors/failures/unexpected IO and one optional SDK skip. Final full-checkout CI evidence is recorded on the PR/handoff.

No main, frontend, dependency/lockfile, migration/seed/schema, golden/evaluation split, scoring/weights, portfolio/order/broker, production database/EC2, accounts/secrets/AWS, scheduler or deployment changes. Temporary tracked-source export is read-only and absent from the final tree. No live model calls, source-entailment proof, full historical reconstruction, full-backend regression claim or independent reviewer approval.
