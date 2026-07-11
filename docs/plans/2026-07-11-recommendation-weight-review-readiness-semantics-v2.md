# Recommendation Weight Review Readiness Semantics V2 Plan

**Goal:** Make it impossible to interpret threshold readiness as manual-review eligibility, explicit pilot authorization, or weight mutation permission.

**Architecture:** Preserve every legacy artifact and decision consumer. A new deterministic shadow evaluator selects the latest or explicitly identified v1 readiness, quality, outcome-calibration, and portfolio-feedback artifacts as of one audit date; validates lineage, future/reference-date coherence, portfolio scope, count partitions, and cohort filters; snapshots aggregate sample/horizon evidence; and appends a v2 semantic report. Legacy evidence has no approved freshness policy, so no arbitrary max-age is invented and freshness remains explicitly unattested. The report is visible as an additive data-health sibling but is not consumed by current gates.

**Tech Stack:** Python 3.11, deterministic JSON models, psycopg/psql SQL, `ai.eval_run`, `ops.pipeline_run`, FastAPI live adapter, unittest.

## Task 1: Characterize the Semantic Failure

1. Add failing pure-model tests for legacy allowed=true versus authorization=false.
2. Add adversarial source booleans and prove every mutation flag stays false.
3. Add partial/mismatched horizon, future-as-of, source-id mismatch, and nested-quality mismatch cases.
4. Add a source snapshot case that preserves filters, observation units, per-horizon rows, aggregate counts, and hashes.
5. Prove all legacy thresholds and portfolio feedback can be ready while missing row identity, feedback deduplication, component snapshot version, horizon policy, and freshness policy still force `manual_review_eligible=false`.

## Task 2: Build the Shadow Evaluator

1. Select v1 readiness, quality, outcome, and portfolio-feedback evals with as-of filters even when an explicit ID is supplied.
2. Validate referenced eval IDs/datasets/dates and canonical nested quality content.
3. Preserve legacy aggregate metrics without claiming stable row identity, deduplicated feedback, approved horizon policy, versioned component snapshots, or an approved freshness policy.
4. Derive separate evidence, eligibility, authorization, pilot, and mutation structures.
5. Render an insert that targets only the new v2 `ai.eval_run` dataset.

## Task 3: Add Runner and CLI

1. Add dry-run and append-only execute paths using the existing pipeline-run helpers.
2. Add a CLI command with source-eval selectors only.
3. Prohibit approval/mutation arguments by construction and static verification.

## Task 4: Additive Operational Visibility

1. Select the latest v2 artifact in live data-health SQL.
2. Normalize a fail-closed sibling payload whose mutation booleans are always false regardless of raw input.
3. Add safe frontend type/default support without changing the current UI or downstream decision composition.
4. Prove the existing v1 readiness/wait/professional/open-gate outputs remain unchanged.

## Task 5: Verify and Review

1. Run focused and adjacent regression suites, compile, CLI help, API contract, roadmap, AWH, and static mutation/migration checks.
2. Obtain independent backend/risk review of source coherence and non-authoritative boundaries.
3. Record residual gaps: row-level cohort identity, feedback deduplication, component versioning, authoritative horizon policy, approved freshness policy, scoped approval, and EC2 deployment remain future tasks.
4. Update handoff/review/QA, stage only intended files, commit, and fast-forward local `develop`.
