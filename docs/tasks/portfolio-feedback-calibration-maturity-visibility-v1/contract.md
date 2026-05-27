# portfolio-feedback-calibration-maturity-visibility-v1 Contract

## Task Request

- request: Make the remaining feedback calibration gate understandable instead of leaving it as a vague data-health blocker.
- context: `portfolio_review_feedback_calibration_attention` is still open because outcome feedback is immature. That is correct, but the UI should show the maturity date, missing samples, and exact reason recommendation weights remain blocked.

## Goal

- goal: Explain the weight review blocker as an outcome maturity problem with clear next timing and sample gaps.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/portfolio-feedback-calibration-maturity-visibility-v1/*`
  - `docs/plans/2026-05-27-portfolio-feedback-calibration-maturity-visibility-v1.md`

## Invariants

- Do not close the gate while mature feedback samples are insufficient.
- Do not change recommendation score weights.
- Do not mutate recommendations, theses, benchmark holdings, portfolio positions, outcomes, or paper validation records.
- Do not enable automatic rebalancing, automatic orders, or broker submit.

## Scope

- Add maturity visibility fields to feedback calibration payloads.
- Compute an estimated maturity date from cadence `wait_until`, or from `history.as_of_date + min_horizon_days` when `wait_until` is empty.
- Add explicit `weight_review_block_reason`.
- Update `/data-health` copy to show the blocker in user-facing Korean.
- Cover the blank `wait_until` fallback with tests.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-feedback-calibration-maturity-visibility-v1`
