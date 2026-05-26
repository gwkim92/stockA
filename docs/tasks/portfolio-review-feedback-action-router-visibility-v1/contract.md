# portfolio-review-feedback-action-router-visibility-v1 Contract

## Task Request

- request: Make the latest portfolio review feedback action-router decision visible to operators and users instead of leaving it only in run history.
- context: `portfolio-review-feedback-action-router-v1` persists whether it executed feedback, executed calibration, or recorded a no-op. The next gap is direct API/UI visibility of that audit artifact.

## Goal

- goal: Expose the latest action-router artifact on data-health and portfolio coverage so the UI clearly shows whether the router waited, ran feedback, ran calibration, or blocked on guardrails.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/tasks/portfolio-review-feedback-action-router-visibility-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Read latest `portfolio_review_feedback_action_router` `ai.eval_run`.
- Add API payloads:
  - `/api/data-health` → `portfolio_review_feedback_action_router`.
  - `/api/portfolio/{portfolio}/coverage` → `risk_budget.review_feedback_action_router`.
- Add Korean UI copy on `/data-health` and `/portfolio/coverage`.
- Preserve read-only order boundary and broker prohibition fields.

## Non-Goals

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No portfolio position mutation.
- No benchmark composition mutation.
- No write button or manual approval flow.

## Verification Commands

- verification command: focused frontend live adapter tests.
- verification command: `cd apps/web && npm run typecheck && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-review-feedback-action-router-visibility-v1`
