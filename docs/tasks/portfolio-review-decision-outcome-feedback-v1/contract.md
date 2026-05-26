# portfolio-review-decision-outcome-feedback-v1 Contract

## Task Request

- request: Use persisted portfolio review decisions as an evaluation input after paper validation and recommendation outcomes mature.
- context: `portfolio-review-decision-history-v1` stores read-only portfolio review decisions, but it does not yet evaluate whether those decisions later proved useful.

## Goal

- goal: Create a read-only feedback layer that compares saved portfolio review decisions with later paper validation and recommendation outcome evidence.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/`
  - `apps/web/`
  - `docs/tasks/portfolio-review-decision-outcome-feedback-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Read latest or selected `portfolio_review_decision_history` eval artifacts.
- Join decisions to later paper validation, recommendation outcome, thesis, and price evidence where available.
- Store an audit-only feedback report as `ai.eval_run`.
- Expose whether evidence is `too_early`, `validated`, `contradicted`, or `needs_more_data`.

## Non-Goals

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No benchmark composition or portfolio position mutation.

## Verification Commands

- verification command: focused Python tests for feedback classification and read-only API payloads.
- verification command: `cd apps/web && npm run typecheck`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-review-decision-outcome-feedback-v1`
