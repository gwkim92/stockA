# recommendation-weight-review-readiness-semantics-v2 Contract

## Task Request

- request: Separate recommendation-weight evidence readiness from explicit user authorization and any weight mutation permission.
- context: legacy quality, outcome, and readiness artifacts reuse `ready_for_*weight_review` and `manual_weight_review_allowed` for different evidence thresholds. The latest explicit 2026-07-04 decision says the pilot was not started, portfolio feedback still blocked weight review, and an exact scoped user approval is required.

## Goal

- goal: Add an append-only, read-only shadow v2 evaluation that records coherent source lineage, sample/horizon semantics, evidence readiness, manual review eligibility, explicit authorization, and mutation boundaries without changing the v1 decision path.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/recommendation_weight_review_readiness_semantics.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - focused Python tests and CLI tests
  - additive data-health frontend types/defaults only; no new action control
  - `scripts/verify_recommendation_weight_review_readiness_semantics_v2.sh`
  - `docs/project-execution-roadmap.md`
  - this task's plan, contract, roles, topology, handoff, review, and QA

## Invariants

- Keep the legacy readiness audit, calibration report, outcome router, open-gate logic, and existing data-health readiness payload authoritative and unchanged.
- Use existing `ai.eval_run.score_json` and `ops.pipeline_run`; do not add a migration.
- The new artifact is `mode=shadow_read_only` and `authoritative=false`.
- `--execute` means persist the audit artifact only. It never means approve a pilot or change a weight.
- The CLI exposes no approve, authorize, component-weight, delta, scoring-cutover, order, or broker argument.
- Do not invent a new authoritative horizon/sample threshold. Preserve every selected horizon row and explicitly label legacy aggregate/identity limitations.
- Missing, future-dated, mismatched, or internally inconsistent source evidence fails source coherence closed. No arbitrary maximum-age rule is invented: because legacy artifacts do not attest an approved freshness policy, temporal freshness remains a separate eligibility blocker.
- `pilot_scope_defined`, `explicit_user_approval_present`, `read_only_pilot_start_allowed`, `proposal_generation_allowed`, `weight_mutation_allowed`, `automatic_weight_change_allowed`, `portfolio_position_mutation_allowed`, `automatic_order_allowed`, and `broker_submit_allowed` remain `false` in this shadow task.
- Recommendation scoring, weights, benchmark definitions, evaluation splits, portfolio positions, paper orders, broker submit, and live deployment state remain unchanged.

## Semantic Contract

- evidence: thresholds and source integrity are diagnostic facts, not authority.
- eligibility: legacy thresholds may be diagnostically ready, but read-only human review remains ineligible until source coherence, portfolio feedback, stable row identity, feedback deduplication, versioned component snapshots, an approved horizon policy, and an approved freshness policy are all attested.
- authorization: explicit scoped user approval is a separate state and is absent in this task.
- pilot: no pilot starts and no proposal is generated.
- mutation: all scoring, weight, portfolio, order, and broker mutations are blocked.

## Acceptance Criteria

- A distinct `recommendation_weight_review_readiness_semantics_v2` eval and `recommendation-weight-review-readiness-semantics-v2` dataset are append-only.
- The artifact snapshots source eval IDs, names, datasets, score dates, created timestamps, legacy statuses, source filters, horizon rows, observation units, aggregate counts, and canonical source hashes.
- The artifact distinguishes recommendation count from recommendation×horizon observations and preserves 30/90/180/365 rows without collapsing to one maximum horizon.
- It exposes that stable row-level sample identity, feedback deduplication, approved horizon policy, versioned component snapshot integrity, and an approved freshness policy are not attested by legacy artifacts.
- Source-reference mismatches, future evidence, portfolio-scope mismatch, missing/invalid counts, horizon row/shape/aggregate mismatch, cohort-filter mismatch, or nested-quality mismatch produce a fail-closed evidence state.
- Legacy `manual_weight_review_allowed=true` can yield `threshold_evidence_ready=true`, but `manual_review_eligible=false` remains fixed while any integrity attestation is missing; user authorization, pilot start, proposal generation, and mutation permission also remain absent.
- The data-health projector reconstructs exact nested allowlists and hard-false authorization/pilot/mutation DTOs; arbitrary nested raw permission keys are never forwarded.
- The data-health API adds a sibling shadow DTO with safe missing defaults; current v1 payload and all downstream decisions remain unchanged.
- Dry-run performs reads only. Execute adds only one pipeline-run record and one `ai.eval_run` artifact.
- Focused tests, relevant regressions, CLI help, frontend API contract, roadmap, AWH, migration diff, compile, and diff checks pass.

## Verification Commands

- verification command: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_recommendation_weight_review_readiness_semantics tests.test_recommendation_weight_review_readiness_audit tests.test_manual_weight_review_calibration_report tests.test_data_operations_cli tests.test_frontend_live_adapter -v`
- verification command: `PYTHONPATH=src .venv/bin/python -m stockanalysis.operations.cli recommendation-weight-review-readiness-semantics-v2-run --help`
- verification command: `bash scripts/verify_recommendation_weight_review_readiness_semantics_v2.sh`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-weight-review-readiness-semantics-v2`
- verification command: `git diff --exit-code -- db/migrations`
- verification command: `git diff --check`
