# portfolio-review-feedback-action-router-v1 Contract

## Task Request

- request: Use the persisted portfolio review feedback cadence artifact to decide which safe backend runner should execute next, without relying on ad-hoc manual commands.
- context: `portfolio-review-feedback-cadence-v1` reports whether to wait, run feedback, run calibration, or inspect missing evidence. The next gap is an action router that can consume that report under strict read-only guardrails.

## Goal

- goal: Add a backend action router that reads the latest cadence decision and, only when safe, invokes the indicated feedback or calibration runner through `stockanalysis-operations` service boundaries.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `tests/`
  - `docs/tasks/portfolio-review-feedback-action-router-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Read the latest `portfolio_review_feedback_cadence` artifact.
- If status is `run_feedback_now`, execute `portfolio-review-decision-outcome-feedback-run` with the linked history eval run.
- If status is `run_calibration_now`, execute `portfolio-review-feedback-calibration-run`.
- If status is `wait_for_outcome_window`, `missing_evidence_review_required`, or `calibration_current`, record a no-op action decision.
- Persist a read-only action-router audit artifact.
- Keep decision-daily orchestration deterministic and secret-free.

## Non-Goals

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No portfolio position mutation.
- No benchmark composition mutation.
- No UI write button or manual approval workflow.

## Verification Commands

- verification command: focused Python tests for action-router status handling and no-op behavior.
- verification command: `PYTHONPATH=src python3 -m unittest discover -s tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-review-feedback-action-router-v1`
