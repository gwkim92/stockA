# Equity result check v1 — handoff

Base develop@1981d140bf119045d7fc329736d7deb72126615c (PR #40). Integration PR #41. This document records implementation and checkpoint evidence; the PR contains final-head and post-merge verification.

## Operator command

After installing the existing package, use the dedicated operations entrypoint:

```sh
stockanalysis-equity-result-check --run-id "$RUN_ID" --request-hash "$REQUEST_HASH" --format text
stockanalysis-equity-result-check --run-id "$RUN_ID" --request-hash "$REQUEST_HASH" --format json
```

The same command is available as `PYTHONPATH=src python -m stockanalysis.operations.equity_result_check`. RUN_ID and REQUEST_HASH refer to the actual existing batch diagnostics; do not substitute the synthetic IDs used by tests. The command reuses the existing trusted STOCKANALYSIS_PSQL_COMMAND configuration and does not create or modify credentials. No production execution was performed by this task.

The existing operations package already has dedicated weight-lineage/prospective-evidence CLI entrypoints. This follows that pattern instead of modifying its 4,665-line umbrella CLI, which has no plugin registration hook. pyproject.toml adds only one console script; a parsed-TOML comparison confirms all dependency declarations and other fields are unchanged.

## Output and exit behavior

| Code | State | Meaning |
| --- | --- | --- |
| 0 | matching | Current stored invocation/report/receipt match; not analysis-quality approval. |
| 1 | unavailable | Configuration, database, process timeout or damaged stored response prevents checking. |
| 2 | invalid arguments | No runtime configuration/DB lookup. Raw supplied values are not echoed. |
| 3 | conflicting | Current stored records no longer agree with the receipt. |
| 4 | not_observed | Receipt not visible in this snapshot; not proof of rollback. |

Both text and JSON go to stdout for a valid query; usage errors go to stderr. Exact receipt IDs, outcome, date and fingerprints remain available, but arbitrary provider/model/source text is not included. check_result is the reusable Python entrypoint. It reuses the unchanged PR #40 reconciliation function, so no scoring, report persistence, retry or state repair is invoked.

Database execution uses BEGIN READ ONLY, a fixed SELECT, SET LOCAL statement_timeout=5s, lock_timeout=1s, idle timeout=8s, UTC/ISO date settings and pg_catalog search path, then ROLLBACK. The configured psql subprocess has a 15-second direct-child timeout and -w to prevent interactive password prompts. Read-only transaction restrictions do not replace least-privilege database roles or secure trusted command configuration. The process timeout does not promise to terminate arbitrary configured wrapper descendants. Server-side timeout/permission failures are reported generically as database_unavailable, not guessed from raw error text.

## Verification checkpoint

Code head 9db1d0bedb172df5e2dc9c89ba28f37412229bfa passed all four Analysis Prompt Quality jobs in run 34035870691 and the separate Analysis Integrity job in run 34035870615. The latter was triggered by the console entrypoint addition in pyproject.toml; no weight-review implementation was modified.

Local no-IO guarded run: 267 cases / 19 modules, zero failures/errors/unexpected IO, one optional SDK skip because the package is absent locally. This retains 247 previous tests and adds 20 operator tests. The dedicated DB suite adds eight cases to the existing 22 atomic cases; six execute the actual Python CLI as a separate process against the named ephemeral CI PostgreSQL. They cover matching, overwritten, absent, corrupted, unavailable DB and a matching receipt in an unchanged failed run. Remaining cases verify that READ ONLY rejects an accidental UPDATE and a stalled SELECT is interrupted by the server limit. All 13 previous cutoff SELECT tests remain unchanged.

The final artifact JSON/logs and exact final-head counts must be inspected before merging. A successful test setup against synthetic data is not a current EC2 availability or production integration check. No full backend or new browser regression claim.

## Product assessment and exclusions

Read product-quality-review.md for the candid assessment. The default five-case news evaluation parses stored ai_output; this task does not change it or claim a new live model-quality benchmark. Correct storage, finite numbers and valid quotations do not establish narrative entailment, useful investment judgment or end-user usability.

No main, production DB/EC2, schema/migrations/seeds, dependencies/lockfile, financial scores/weights/thresholds, benchmark/evaluation/golden data, frontend, portfolio/order/broker, secrets/accounts/AWS, scheduler or deployment changes. No live/paid model generation, automatic retry or report regeneration. A temporary read-only tracked-source export was removed from the final diff. No independent reviewer approval is claimed.
