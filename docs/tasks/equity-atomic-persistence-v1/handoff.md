# Equity atomic persistence v1 — handoff

## Integration tracking

PR #40, branch codex/equity-atomic-persistence-v1, based on develop@e6343653fc364641ab0ee09fd75132fa1d538cfc. Final checked head, merge SHA, run IDs and final artifact hashes are recorded on the PR. Do not substitute a checkpoint result for a later unverified revision.

## Delivered

Primary invocation, report UPSERT and a versioned result receipt now use one PostgreSQL statement. Correct running-pipeline identity, valid existing JSON container and absence of a same-run/request receipt are mandatory; failure rolls back the statement. Fallback report/receipt refers to the original failed model invocation without inventing success. Original failed-attempt auditing remains separate.

The batch stores request hashes in result diagnostics, validates the complete acknowledgement before counting a saved artifact, and exposes uncertain acknowledgement/write stages without automatic retry or fallback. Its source/prompt/financial logic and per-symbol failure isolation are unchanged. The report module and psql executor are unchanged.

reconcile_result is a read-only Python function. It compares current receipt, invocation and report fingerprints and returns matching/conflicting/not_observed with automatic_retry_allowed=false. It detects overwritten/changed records but cannot prove rollback, authorize replay, restore old report bodies or certify source truth. Receipt fingerprints are not tamper-proof signatures.

Application record: ops.pipeline_run.config_json.equity_result_receipts_v1; policy equity_atomic_result_v1. Existing config keys are preserved. There is no new database table, migration, CLI recovery action, scheduler or automatic retry mechanism.

## Verified checkpoint and final refinement

Initial implementation head 7a6cbabeb8243dd451d6409fa21ac196ce45eb1d passed Analysis Prompt Quality run 34024393770:
- Python 3.11 job 101462665336 and Python 3.13 job 101462665376: workflow steps success.
- Existing cutoff job 101462665249: success.
- New committed-write PostgreSQL job 101462665288: success.

The atomic archive 9986578119 was downloaded and matched SHA-256 f342bff482aecfbcfa0885221d1684b66f48b1d0e768d1d2649fb520d78b5733. Its JSON and logs were inspected: 21 tests, 187 SQL executions, PostgreSQL 16.15, zero failures/errors/skips. Other checkpoint job success does not replace inspection of the final four reports.

The final refinement leaves write semantics unchanged, avoids text-casting indexed bigint columns, bounds malformed receipt identifiers before casting, adds one real PostgreSQL malformed-ID case and triggers CI when any of the three original write-table DDL files changes. Final expected suites: 247 deterministic cases across 18 modules (226 existing plus 21 new), the existing 13 cutoff SELECT cases, and 22 new committed-write cases. Final exact observed counts and artifacts must be checked and recorded on PR #40 before merge.

Local guarded regression ran 247 cases with zero failures/errors/unexpected IO and one optional SDK skip (SDK not installed locally). Local PostgreSQL execution was unavailable. CI installs the already-declared SDK extra and must report zero skips. Real Agent/schema objects use a mocked Runner. No model request is made. The new PostgreSQL test only accepts its explicitly named isolated CI service and cleans all test schemas after every case.

## Test meaning and limitations

New tests retain the old two-call defect as a real database reproduction and check atomic rollback at invocation/report/receipt failures, failed UPSERT preserving existing content, duplicate/concurrent submissions, fallback audit identity, wrong/closed/missing runs, damaged receipt data, later overwrite conflicts and lost acknowledgement after real COMMIT through the public batch runner. The four write-table definitions come from checked-in migration files; the instrument FK target is a minimal stub. This is not a full schema/migration or application deployment test.

Independent external model generation, failed-attempt audit, prompt registration and final pipeline status are not made atomic with every report. Whole-batch exactly-once completion, automatic idempotent recovery, durable per-symbol scheduling, historical report versions, runtime workloads and semantic source verification remain separate work. Missing receipt never authorizes retry. Existing failure-status marking remains best effort during outages.

No main, frontend, dependency/lockfile, production DB/EC2/replacement runtime, schema/migrations/seeds, prompts/financial scoring/weights, benchmark/evaluation/golden changes, portfolio/order/broker, accounts/secrets/AWS, scheduler or deployment changes. No independent reviewer approval is claimed. Temporary read-only tracked-source export is absent from final changes.