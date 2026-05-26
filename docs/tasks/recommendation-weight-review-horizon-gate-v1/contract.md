# recommendation-weight-review-horizon-gate-v1 Contract

## Task Request

- request: Make manual recommendation weight review readiness consume the new horizon-grid outcome calibration gate.
- context: `recommendation-outcome-calibration-sample-expansion-v1` found that older quality eval can report `ready_for_weight_review` while the actual 30/90/180/365-day outcome windows are still `not_due`.

## Goal

- goal: Manual or pilot recommendation weight review cannot proceed unless the latest `recommendation_outcome_calibration_sample_expansion` eval is present and not blocked by `no_due_outcome_window`, price gaps, or remaining backfill candidates.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/recommendation_weight_review_readiness_audit.py`
  - `src/stockanalysis/operations/manual_weight_review_calibration_report.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/recommendation-weight-review-horizon-gate-v1/*`
  - `docs/plans/2026-05-27-recommendation-weight-review-horizon-gate-v1.md`

## Scope

- Load the latest outcome calibration eval for the requested date or explicit eval id.
- Block manual weight review when calibration status is `no_due_outcome_window`, `backfill_candidates_remain`, `price_history_gaps_remain`, `no_outcome_sample_available`, or missing.
- Preserve the existing protected component zero-weight checks.
- Expose the blocking reason in audit JSON and user-facing readiness surfaces.

## Non-Goals

- No recommendation weight changes.
- No benchmark split changes.
- No live broker submit.
- No synthetic outcomes.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_recommendation_weight_review_readiness_audit tests.test_manual_weight_review_calibration_report tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-weight-review-horizon-gate-v1`

## Acceptance Criteria

- A `ready_for_weight_review` quality eval alone is not sufficient when outcome calibration says the selected horizons are not due.
- Manual weight review remains blocked and explains the exact horizon-gate reason.
- No score weights, recommendation rows, paper order state, or broker state are mutated.
