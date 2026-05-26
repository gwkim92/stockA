# portfolio-review-feedback-cadence-v1 Contract

## Task Request

- request: Keep portfolio review decision feedback and calibration fresh as outcome windows mature, without changing weights or enabling orders.
- context: `portfolio-review-feedback-calibration-v1` can aggregate feedback, but it still needs an operating cadence so stale or missing feedback does not block professional review indefinitely.

## Goal

- goal: Add a backend cadence/readiness layer that decides when `portfolio-review-decision-outcome-feedback-run` and `portfolio-review-feedback-calibration-run` should run again based on saved decision history age, outcome maturity, and existing calibration state.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/`
  - `apps/web/`
  - `docs/tasks/portfolio-review-feedback-cadence-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Read latest portfolio review history, feedback, calibration, recommendation outcome maturity, paper validation, and price evidence availability.
- Report whether to wait, run feedback now, run calibration now, or investigate missing evidence.
- Persist the cadence decision as read-only audit evidence.
- Expose the cadence state on data-health and portfolio coverage.

## Non-Goals

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No portfolio position mutation.
- No benchmark composition mutation.

## Verification Commands

- verification command: focused Python tests for cadence decision policy and read-only API payloads.
- verification command: `cd apps/web && npm run typecheck`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-review-feedback-cadence-v1`
