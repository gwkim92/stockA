# data-health-attention-classification-v1 Contract

## Task Request

- request: Clarify remaining `/data-health` attention states so the professional investment system separates real operating blockers from expected investment-review or outcome-wait states.
- context: EC2 `/api/data-health` currently reports `overall_status=attention_required` with gates such as `benchmark_drift_quality_attention`, `portfolio_review_decision_history_attention`, `portfolio_review_feedback_calibration_attention`, and `professional_source_gap_attention`. These are not all runtime failures; some mean "review concentration", "wait for outcome maturity", or "known source limitation".

## Goal

- goal: Keep existing `open_gates` for compatibility, but add structured `open_gate_details` with category, severity, status label, user action, and order-boundary explanation. Render those details on `/data-health` so a Korean user can distinguish what is broken, what needs investment review, and what is intentionally waiting for more evidence.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/data-health-attention-classification-v1/*`

## Invariants

- Do not remove or rename existing `open_gates`.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions.
- Do not enable broker submit, order writes, or automatic rebalancing.
- Do not hide real failures. Classification must add context, not suppress gates.

## Scope

- Add deterministic mapping from gate id to Korean label, category, severity, and next action.
- Derive dynamic details from existing payloads where useful, such as active share, source blocker count, calibration status, and outcome wait state.
- Add a `/data-health` section that shows gate details before raw gate chips.
- Add frontend contract tests for the new payload field.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-attention-classification-v1`
