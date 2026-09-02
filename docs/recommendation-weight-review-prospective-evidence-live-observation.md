# Recommendation Weight Review Prospective Evidence Live Observation

## Purpose

`recommendation-weight-review-prospective-evidence-live-observation-v1` runs the deterministic prospective-evidence foundation against an explicitly identified PostgreSQL target and records an append-only observation of its identity, count, feedback-deduplication, and freshness results.

It is an observation boundary, not a pilot boundary. It cannot approve a policy, generate a weight proposal, change recommendation scoring, mutate a portfolio, rebalance, create an order, submit to a broker, alter a scheduler, deploy, or migrate the schema.

## Exact Inputs

Every observation requires an `as_of_date`, the exact source-lineage reconciliation `eval_run_id`, the exact `Long Term Paper` feedback-calibration `eval_run_id`, a non-secret environment label, and the expected canonical database-identity SHA-256. There is no fallback to independently selected latest lineage or feedback artifacts.

## Database Identity Gate

The initial preflight reads:

- `current_database()`;
- `current_user`;
- PostgreSQL `server_version_num`;
- server address and port when available;
- presence of the required `ai`, `ops`, `signal`, `performance`, and `portfolio` relations.

The canonical payload is hashed with SHA-256. If required relations are missing or the hash differs from the expected target, the runner returns a blocked, zero-write result and does not query the recommendation evidence tables.

`PsqlCommandExecutor` opens a separate `psql` process for each SQL command. To prevent a later connection from reaching a different target, the exact evidence lookup starts with an identity assertion in the same PostgreSQL command. Pipeline insertion, observation insertion, and pipeline status updates also repeat the exact database name, role, version, address, port, and required-relation predicates inside their own SQL statements. A target switch therefore stops inside the affected command.

The output and persisted artifact never contain the PostgreSQL command, DSN, password, or environment-variable values.

### Establishing the Expected Fingerprint

A first dry-run may use 64 zeroes as the expected hash. It stops after the identity query and prints the observed canonical payload and SHA-256 without querying domain evidence or writing anything. Verify the database name, role, version, address, port, and required relations, then rerun with that observed SHA-256.

## Legacy-Surface Stability

The legacy surface binds the exact lineage, quality, outcome, feedback-calibration, and feedback-run eval IDs; canonical hashes of their score payloads; cohort filters and source metadata; recommendation rows, total scores, recommended weights, and component snapshots; outcome observations; deduplicated feedback identity; cohort/freshness snapshots; and every hard-false mutation or trading permission.

During execute mode, the runner computes this surface before creating the pipeline row and again immediately after. If the hashes differ, the guarded pipeline failure update is attempted and no live-observation `ai.eval_run` artifact is inserted.

## Execution Boundary

Dry-run:

1. validate the initial database identity;
2. run one same-command guarded exact-reference evidence lookup;
3. build the foundation and legacy-surface hash;
4. write nothing.

Execute:

1. perform the dry-run preflight;
2. create one guarded `ops.pipeline_run` row;
3. run a second same-command guarded exact bundle lookup;
4. compare legacy-surface hashes;
5. insert one guarded append-only live-observation artifact only when stable;
6. finish the pipeline through a guarded status update.

A successful execute uses three SQL write statements for one pipeline lifecycle and one append-only eval. No existing eval, recommendation, score component, outcome, portfolio, or trading row is updated or deleted.

## Result States

- `live_observation_complete_fresh_read_only`
- `live_observation_complete_stale_read_only`
- `live_observation_blocked_environment_mismatch`
- `live_observation_incomplete_fail_closed`
- `live_observation_incoherent_fail_closed`

All approval, pilot, proposal, scoring, weight, portfolio, rebalance, order, and broker permissions remain false in every state. The order boundary remains `read_only_no_order`.

## Usage

Identity-only blocked preflight:

```bash
stockanalysis-weight-prospective-evidence-live-observation \
  --as-of-date 2026-09-02 \
  --lineage-eval-run-id <exact-lineage-eval-id> \
  --portfolio-feedback-calibration-eval-run-id <exact-feedback-calibration-eval-id> \
  --environment-label stockA-live \
  --expected-database-identity-sha256 0000000000000000000000000000000000000000000000000000000000000000
```

Read-only observation after verifying the fingerprint:

```bash
stockanalysis-weight-prospective-evidence-live-observation \
  --as-of-date 2026-09-02 \
  --lineage-eval-run-id <exact-lineage-eval-id> \
  --portfolio-feedback-calibration-eval-run-id <exact-feedback-calibration-eval-id> \
  --environment-label stockA-live \
  --expected-database-identity-sha256 <verified-sha256>
```

Append the observation artifact:

```bash
stockanalysis-weight-prospective-evidence-live-observation \
  --as-of-date 2026-09-02 \
  --lineage-eval-run-id <exact-lineage-eval-id> \
  --portfolio-feedback-calibration-eval-run-id <exact-feedback-calibration-eval-id> \
  --environment-label stockA-live \
  --expected-database-identity-sha256 <verified-sha256> \
  --execute
```

Verification:

```bash
bash scripts/verify_recommendation_weight_review_prospective_evidence_live_observation_v1.sh
bash scripts/verify_analysis_integrity_ci.sh
```

## Next Boundary

After a real append-only observation exists, review the exact blocker, staleness, duplicate, identity, and count results. Horizon/freshness policy approval and any manual weight-pilot packet remain separate, explicitly authorized tasks.
