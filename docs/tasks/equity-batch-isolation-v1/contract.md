# Equity research batch isolation v1

User request: continue thorough stockA implementation. Base develop@5a76baa63011b984b9cb757cc9492989e2c1b7e0 (PR #38).

## Concrete defect and goal

The equity runner eagerly constructs all bounded contexts and previews before processing any symbol. One oversized/malformed context or failing preview prevents every valid symbol from progressing. The provider exception scope also includes success-log writes, so a storage error may be mislabeled as a model failure. Make single-symbol input/provider faults explicit without hiding infrastructure/persistence failures.

## Scope

Keep UTC historical cutoff, intact bounded selection, exact provider/hash/artifact source selection, output validation, financial rules and current deterministic fallback identity. Validate requested symbol/context ownership before generating anything. Separate preparation, provider/fallback, and persistence stages. A rejected symbol must not produce a fabricated model invocation or artifact. Valid symbols must retain ordering and continue when an item-local input fails. Preserve cancellation and fatal DB/write failures. Report selected, prepared, reported, fallback and unreported outcomes without calling all-rejected batches successful. Dry-run must be read-only and diagnose the same preparations without model execution. Inspect downstream consumers before choosing compatible statuses.

Add deterministic regressions for permutations of valid/oversized/missing/mismatching contexts, malformed provider objects, fallback failure, all-failed/empty and dry-run behavior, report/count invariants, cancellation, sanitized error codes, and persistence failure boundaries. Re-run the current 196 prompt regressions and 13 real PostgreSQL cutoff cases; do not weaken their assertions. Verify exact uploaded source and final CI head before develop integration.

## Exclusions

No main, frontend, dependency/lockfile, production database or replacement runtime, migration/schema/seed, scoring/weights, benchmark/evaluation split/golden data, portfolio/order/broker, AWS/accounts/secrets, scheduler/deployment configuration, paid model calls or live deployment. Test fake executors and the existing isolated CI PostgreSQL fixture are permitted verification scopes. SQL persistence is not automatically made transactional by this task; document remaining restart/idempotency/atomicity limitations. Do not claim source entailment or full historical versioning.

A temporary read-only export of tracked source/tests/schema may be used in the DNS-restricted sandbox. It must exclude credentials/runtime artifacts and be removed from the final tree. Keep task review/handoff and exact evidence current.
