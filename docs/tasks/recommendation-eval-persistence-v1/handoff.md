# Recommendation Eval Persistence v1 Handoff

## Status

Implementation complete on `codex/recommendation-eval-persistence-v1` and proposed in PR #48 against `develop`.

No production migration, deployment, scheduler, broker, order, secret, recommendation weight, scoring threshold, or benchmark-policy change was executed.

## Delivered

- Migration `0035_recommendation_eval_persistence.sql` extends the existing `ai.eval_run` lineage with `pipeline_run_id`, `as_of_date`, `horizon_days`, and `config_json`.
- Added append-only `ai.recommendation_eval_snapshot` with source recommendation/batch/thesis/outcome IDs, queryable decision fields, complete snapshot JSON, and canonical SHA-256.
- Existing recommendation quality scoring implementation is preserved byte-for-byte in `recommendation_quality_eval_legacy.py`.
- Public `recommendation_quality_eval.py` remains the CLI/API import surface and only wraps the old scorer with snapshot capture and persistence.
- Evaluation lookup now returns recommendation source snapshots in the same read-only SQL statement as the score inputs.
- Snapshot JSON freezes recommendation, batch, instrument, thesis entry/invalidation/exit conditions, all score components, and the exact selected eligible outcome.
- Executed eval persists `ai.eval_run` and all child snapshots in one PostgreSQL data-modifying CTE statement. There is no snapshot upsert/update/delete path.
- Analysis Integrity CI path coverage now includes recommendation quality evaluation persistence files and tests.
- Main operations CLI regression is included so the wrapper cannot silently break command registration or dry-run behavior.

## Verification Evidence

Analysis Integrity run `34094775478` completed successfully on the PR merge ref.

- package install: passed on CPython 3.11
- compileall for evaluator/persistence and existing protected analysis modules: passed
- recommendation quality + weight review integrity suites: 93 tests passed
- `tests.test_data_operations_cli`: 107 tests passed
- workflow capability policy checks: passed
- `git diff --check`: passed
- total explicitly executed unittest cases in this CI run: 200 passed

The earlier run `34094623875` also passed the 93-test integrity set before CLI regression was added.

## Persistence Semantics

The evaluator does not re-read mutable source tables after scoring. The source state used to build snapshots is returned inside the original evaluation lookup payload. Python canonicalizes each snapshot using sorted keys and compact UTF-8 JSON, computes SHA-256, then injects those exact values into the atomic persistence statement.

Historical source IDs in `ai.recommendation_eval_snapshot` intentionally are not cascading foreign keys. This prevents later source deletion or mutation from rewriting evaluation history.

## Next Recommended Slice

Build a read-only evaluation-history query/API and UI over `ai.eval_run` + `ai.recommendation_eval_snapshot` so an operator can choose any historical eval and compare:

- recommendation state then vs now
- score-component drift
- thesis/invalidation drift
- outcome known then vs later matured outcomes
- snapshot SHA identity and source lineage

That read surface should not modify or backfill snapshots.