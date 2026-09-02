# recommendation-weight-review-prospective-evidence-live-observation-v1 Contract

## Goal

Run the merged prospective-evidence foundation against an explicitly identified PostgreSQL target using exact source IDs, record the observed identity/count/freshness result, and prove the legacy recommendation evidence surface remains unchanged.

This task is observation-only. It does not approve a policy, start a weight pilot, generate a proposal, change scoring, mutate a portfolio, submit an order, call a broker, alter a scheduler, deploy, or migrate the schema.

## Required Inputs

- `as_of_date`
- exact `lineage_eval_run_id`
- exact `portfolio_feedback_calibration_eval_run_id`
- non-empty `environment_label`
- exact expected database-identity SHA-256

The runner never falls back to an independently selected latest lineage or feedback-calibration artifact.

## Database Identity Contract

The target is identified from `current_database()`, `current_user`, `server_version_num`, server address/port when available, and required relation presence. The canonical payload is SHA-256 hashed.

The observation fails closed before domain reads or writes unless the identity is complete and equals the operator-supplied expected SHA-256. PostgreSQL commands, DSNs, passwords, and environment variables are never persisted.

## Legacy Surface Contract

The canonical legacy surface includes exact source eval IDs and source score hashes, recommendation rows and component snapshots, recommendation scores and recommended weights, outcome identities, feedback deduplication, cohort/freshness snapshots, and hard-false mutation boundaries.

Execute mode computes the surface before and after creating the allowed pipeline row. A changed hash fails the pipeline and prevents insertion of the final live-observation eval.

## Read/Write Boundary

Dry-run performs an identity read plus one exact-reference evidence read and no writes.

Execute may write only one `ops.pipeline_run` lifecycle and one append-only `ai.eval_run` artifact. No other write is allowed.

## Result States

- `live_observation_complete_fresh_read_only`
- `live_observation_complete_stale_read_only`
- `live_observation_blocked_environment_mismatch`
- `live_observation_incomplete_fail_closed`
- `live_observation_incoherent_fail_closed`

No state grants pilot, proposal, scoring, weight, portfolio, rebalance, order, or broker permission.

## Acceptance Criteria

- exact source IDs and expected database SHA-256 are mandatory;
- wrong or incomplete targets stop before domain reads and writes;
- dry-run is zero-write;
- execute writes only the allowed pipeline lifecycle and one append-only eval;
- recommendation score, recommended weight, component, source score, cohort, outcome, feedback, or permission drift changes the legacy hash;
- drift between reads prevents eval insertion;
- credentials and connection strings are absent from reports and persisted score JSON;
- all permission and mutation flags remain false;
- focused tests, verifier, compile, package entry point, migration diff, and Analysis Integrity CI pass.
