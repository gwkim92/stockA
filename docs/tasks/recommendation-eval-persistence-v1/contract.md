# Recommendation Eval Persistence v1 Contract

## Objective

Make every executed recommendation quality evaluation reproducible after the source recommendation, thesis, score components, or outcome rows later change.

The existing `ai.eval_run` remains the evaluation-run identity. This task adds lineage metadata to that row and persists immutable per-recommendation snapshots beneath it.

## Scope

- Add migration `0035_recommendation_eval_persistence.sql`.
- Extend `ai.eval_run` with nullable execution lineage needed by recommendation quality evaluations.
- Add append-only `ai.recommendation_eval_snapshot` rows keyed by `(eval_run_id, source_recommendation_id)`.
- Extend `recommendation_quality_eval` lookup to return the exact source state used by the evaluation.
- Canonicalize and SHA-256 fingerprint those source snapshots in Python.
- Persist the eval row and all snapshots atomically in one SQL statement.
- Add regression tests and task handoff evidence.

## Snapshot Contract

Each snapshot freezes the evaluation-time state for one recommendation:

- recommendation identity, bucket, action, rank, total score, recommended weight, status
- recommendation batch identity, as-of date, market, strategy, horizon type, universe version and source run
- instrument identity and primary symbol
- linked thesis identity and decision fields, including entry, invalidation and exit conditions
- all recommendation score components with score, weight, explanation and creation timestamp
- the exact latest eligible performance outcome selected by the evaluation, including outcome identity, measurement dates, returns, alpha, drawdown, label and source run

The source IDs stored in the snapshot are historical values, not cascading foreign keys. Deleting or mutating a source row must not rewrite the historical snapshot.

## Invariants

- Dry-run evaluation remains read-only.
- Executed evaluation does not mutate recommendation scores, weights, theses, outcomes, paper validation, portfolios, orders, broker state, or source evidence.
- No new weight-review threshold or benchmark rule is introduced.
- No production migration or deployment is performed in this task.
- Snapshot rows are insert-only; no upsert/update path is added.
- Snapshot fingerprint is SHA-256 over canonical JSON (`sort_keys=True`, compact separators, UTF-8).
- `ai.eval_run` plus all child snapshots are inserted atomically; partial snapshot persistence must fail the statement.

## Acceptance Criteria

1. Executed recommendation quality eval records pipeline run ID, as-of date, horizon days and execution config on `ai.eval_run`.
2. Every recommendation read by that eval produces exactly one immutable snapshot row.
3. Snapshot content contains the same recommendation/outcome/component state returned by the evaluation lookup, rather than re-reading mutable tables after scoring.
4. The selected outcome is frozen by value and by source outcome ID.
5. Snapshot fingerprints are deterministic and change when source state changes.
6. Existing scoring and dry-run behavior remain unchanged.
7. Unit regression verifies schema contract, read-only lookup, canonical fingerprinting, atomic insert SQL and execute-path lineage.
