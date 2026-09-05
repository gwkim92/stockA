# Equity research contract v3 — handoff

## Integration record

PR #37 on codex/equity-research-contract-v3, based on develop@9c90f5f7220861a2f57d4ee7e5e5dd72d588fa83 (PR #36). The PR records the final checked head, merge SHA and post-merge verification. This handoff is the only change after the implementation checkpoint below; its final head must pass before integration.

The previously unmodified equity file was updated successfully with normal authorized GitHub update_file calls in this task. There were no denied writes and no alternate/encoded/relocated write route or new source-export workflow.

## Delivered

- Explicit model confidence zero survives parsing, normalization and artifact serialization instead of becoming 0.35. Missing, wrong-type, non-finite and out-of-range values fail the existing research schema instead of being guessed or clipped. Valid optional empty text and empty lists remain valid.
- The same existing schema is enforced at parser, typed/injected-provider completion and artifact boundary. Strings/dictionaries cannot turn into character/key claim lists before checking. Invalid model output is not logged as a successful model invocation. Existing failed-invocation and deterministic-fallback behavior remains explicit; fallback can still write its own artifact.
- Equity Codex instructions use the shared source-data boundary, distinguish financial facts from assumptions/previous model hypotheses, preserve units, and allow 0-7 supported key points rather than requiring filler claims.
- The complete escaped/framed source payload is checked after initial and reduced whole-record selection. A large nested field cannot exceed the budget silently, and JSON/individual source records are not cut. Existing integer budget range 2000-100000 is enforced. The limit is for source characters, not total prompt tokens.
- Provider input, request hash and artifact input-source inventory use the same selected context. A record omitted from model input no longer appears in the inventory merely because it was in the complete fetched context. This is input provenance, not per-claim semantic entailment.
- Template version: 2026-09-06-equity-contract-v3. Existing task name, full_equity_research artifact type, output/storage schema, SQL generation bodies, provider/model selection, financial weights and fallback conventions remain unchanged.

## Verified implementation checkpoint

Head e02c8068a52599e6a42efe77005e349c9bcf578a passed Analysis Prompt Quality run 33985536565:

- Python 3.11 job 101358235103: completed / success.
- Python 3.13 job 101358234881: completed / success.
- Each interpreter ran 186 cases in 15 modules: 159 existing selected regressions plus 27 new equity methods. Zero failures, errors, skips and unexpected IO attempts. This is 186 unique cases on two interpreters, not 372 unique cases.
- Declared package and optional SDK installation, compilation and guarded execution passed. The already-declared agents extra resolved to openai-agents 0.17.8. SDK object checks mock Runner; provider/process tests use mocks and SQL executor tests use in-memory fakes.
- Both report/log archives were downloaded, SHA-256 verified and inspected, including all 27 new method results.

Checkpoint artifacts:

- 3.11 artifact 9975040613: 45eb2e25cab9230b2b8e9d0b2e14da21a36ce1adb8c0c4f442f8aa10b7fbc849.
- 3.13 artifact 9975033693: b46543b6f74e09915a349f923a5b021e054d28acfbe5f3bb0bd54129628ce1d5.

Local targeted execution: 27 new plus seven existing equity methods, all 34 passed under guards denying real socket/process IO. Baseline tests reproduced zero corruption, missing/type/range acceptance, input-budget and injected-provider defects before the fixes. A later typed-collection subtest also failed before the follow-up fix. No full current local checkout or complete local backend regression is claimed: the prior tracked-source archive was used after affected base blobs were matched against GitHub. Clean CI uses the complete current branch and all 15 selected modules.

Verified uploaded file blobs match the local tested bytes:
- Runtime: 634348bea83db09e56dc1eb60d23129d69cb7585.
- Existing equity tests: 6532a4c0e9e8cbbd625bce6e86d94a9582452a0f.
- New equity tests: 55c34c3c2a4fac5c62c305818e95b0cd7b6ff495.

An AST comparison confirmed every render_* SQL function and the output-schema builder unchanged. The prior test requiring confidence 1.3 to clamp to 1.0 now checks valid 0.93 preservation; new explicit tests reject invalid ranges. No golden data, acceptance threshold or evaluation split changed. The final compare has only the expected task/runtime/test/CI files. No independent reviewer approval is claimed.

## Remaining limitations

Read review.md for specifics. Source-side numeric string conversion, deterministic fallback prose/default confidences, model-reported usage, output text/list length truncation and semantic/future-information checks remain. The unchanged latest-thesis SQL does not restrict creation time to the requested historical cutoff; this is not complete point-in-time reconstruction. The output schema has no per-claim source-reference field, so matching input provenance does not prove each statement is supported or causally valid.

An oversized context now aborts the batch before writes, including otherwise usable symbols in the batch. Per-symbol failure isolation and actual-workload rejection rates need separate testing before rollout. No live paid generation, actual database/EC2 data or deployment was used, and no model-quality or injection-immunity claim is made.

No main, dependency/lockfile, migration/seed/schema, scoring weights, benchmark/evaluation split, portfolio/order/broker, account/secrets/AWS, scheduler or deployment changes. Frontend files were unchanged and earlier browser counts are not new verification for this task. Production rollout, broader backend regression and semantic evaluation remain unexecuted.
