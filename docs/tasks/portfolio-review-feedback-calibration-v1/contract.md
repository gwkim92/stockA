# portfolio-review-feedback-calibration-v1 Contract

## Task Request

- request: Use accumulated portfolio review decision feedback to determine whether review decisions are reliable enough for future manual weight-pilot consideration.
- context: `portfolio-review-decision-outcome-feedback-v1` evaluates a single saved review history, but it does not yet aggregate feedback across multiple histories or time windows.

## Goal

- goal: Create an audit-only calibration layer that aggregates portfolio review feedback outcomes over time and reports whether the evidence is still too early, contradictory, or strong enough for manual review readiness.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/`
  - `apps/web/`
  - `docs/tasks/portfolio-review-feedback-calibration-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Read multiple `portfolio_review_decision_outcome_feedback` eval artifacts.
- Aggregate validated, contradicted, too-early, and needs-more-data counts by decision type, family, and symbol.
- Store a read-only calibration artifact as `ai.eval_run`.
- Expose whether portfolio review feedback is `insufficient_history`, `collect_more_feedback`, `contradiction_review_required`, or `manual_review_ready`.

## Non-Goals

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No portfolio position mutation.
- No benchmark composition mutation.

## Verification Commands

- verification command: focused Python tests for calibration aggregation and read-only API payloads.
- verification command: `cd apps/web && npm run typecheck`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-review-feedback-calibration-v1`
