# Equity batch isolation v1 — handoff

## Integration tracking

PR #39 on codex/equity-batch-isolation-v1, base develop@5a76baa63011b984b9cb757cc9492989e2c1b7e0. Final head, merge SHA and post-merge CI are recorded on the PR. Do not describe this checkpoint as testing a later unverified runtime revision.

## Delivered

Per-symbol malformed/missing/oversized and wrong-identity/date inputs are rejected without preventing healthy prepared symbols from reporting. Primary-provider errors use the existing explicitly labeled fallback; fallback failure remains an unreported item. DB/audit/artifact faults stop the batch rather than triggering model fallback. Cancellation propagates. A defensive provider copy protects the selected input snapshot and source IDs.

Incomplete batches raise EquityResearchBatchError with a structured .report after healthy items finish. The actual existing CLI emits JSON diagnostics on stderr and returns 1; the existing coverage parent marks failure. Clean/all-saved-fallback statuses remain compatible. Selected/prepared/primary/fallback/unreported counts, per-symbol stages, provider-attempt flags and acknowledged artifact IDs distinguish partial work from complete success. No fictitious invocation/artifact is created for rejected input. Dry-run is read-only; execution no longer depends on preview generation.

## Verified implementation checkpoint

Head 777b693db729f762b6edad26fd613bab3392c9d7 passed Analysis Prompt Quality run 34020807532:

- Python 3.11 job 101452927399: 226 tests / 17 modules, zero failures/errors/skips/unexpected IO.
- Python 3.13 job 101452927481: the same 226 tests, zero failures/errors/skips/unexpected IO.
- PostgreSQL cutoff job 101452927262: 13 unchanged real SELECT tests, zero failures/errors/skips; 27 SQL process executions including identity and cleanup checks.

The 226 cases retain 196 existing cases and add 30 batch cases. Running them on two interpreters does not double the unique-case count. Both interpreter logs include all 30 batch cases, the real SDK object test (Runner mocked), and actual CLI/parent integration paths with fake executors. New persistence tests use fake SQL recorders/fault injection, not real transactional writes. The PostgreSQL service is the existing disposable no-host-port rollback-only fixture; no production endpoint is used.

Checkpoint archives were downloaded, hashed and inspected:
- Python 3.11 artifact 9985418816; SHA-256 72c334493ae6696b69dbef870523bd21b78157edca887b851c15ca0a6451fecd.
- Python 3.13 artifact 9985416013; SHA-256 590a40bfdfcbe899f482aad73330c56653665ea24a952c324eafd80045d12064.
- PostgreSQL artifact 9985418636; SHA-256 ccfc5febd10ca2d3d570c5411964847ea6f8337259d40802f5906e46d00dbbd5.

CI reports openai-agents 0.17.8 from the unchanged optional dependency declaration; no paid generation occurs. Local full selected execution also passed 226 cases with one optional SDK skip, because that package is absent locally. PostgreSQL was not run locally. No complete application/backend-suite claim is made.

## Exact source and compatibility checks

Uploaded code matches local intended Git blob hashes:
- equity_research_reporting.py: df86a35bba2392f72897a782af8ad9817af3b2d6.
- equity_research_batch.py: 7b93dc0775fbef10d044a05fbbe640fd80f5b0d6.
- test_equity_batch_isolation.py: 56aaadddbcfc202eea655f0bef8e86aa496e91b7.
- test_equity_research_reporting.py: cfc0e93ce60f21f09656655077111522023180b0.
- verify_analysis_prompt_contract.py: 55f9cd8e7802615b4abc0fd61e8fadd51fdaca93.
- analysis-prompt-quality.yml: 8f1b78a3710f6b2069706423acdb203871aeb5ff.

Only the public runner and context loader change within the old runtime module. AST comparison confirms the existing prompt/output schema, SQL read/write builders, financial helpers, template version and provenance functions remain unchanged. Existing test assertions are retained except a raw-error-text expectation changed to require the sanitized code and forbid raw provider text. CI only adds the new test module and triggers; existing guards and cutoff service are unchanged.

## Limits and safe continuation

Read review.md for failure/count semantics. Existing SQL statements are independent: this is not atomic model-log-plus-artifact persistence or durable automatic retry. An acknowledged write is counted; an unacknowledged operation may have committed and is marked uncertain. Reconcile those cases before any rerun. Failure-status marking is still the existing best-effort helper, so CLI error reporting does not prove a failed ops row was durably updated during a database outage.

All-invalid inputs fail without creating a run row; structured diagnostics are available to the caller. Context DB/infrastructure failures remain batch-fatal and preparation is still sequential/eager. No attempt was made to implement parallel scheduling, a persistent per-item ledger, a circuit breaker or a new retry policy. Fallback narratives/confidences retain previous behavior and are not new evidence of model truth.

No frontend, main, production DB/EC2, replacement runtime, dependencies/lockfile, migrations/seed/schema, scoring/weights, benchmark/evaluation/golden data, portfolio/order/broker, accounts/secrets/AWS, scheduler or deployment changes. Temporary read-only tracked source export is removed. No real model call, current-data validation, full historical revision reconstruction, source entailment or independent reviewer approval is claimed.
