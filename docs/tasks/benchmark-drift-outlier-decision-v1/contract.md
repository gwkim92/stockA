# benchmark-drift-outlier-decision-v1 Contract

## Task Request

- request: Turn current benchmark drift outliers into explicit professional portfolio review decisions.
- context: After `source-blocked-recommendation-guardrail-v1`, `/api/data-health` still reports `benchmark_drift_quality_attention`. The latest benchmark drift quality shows full-enough SPY composition coverage, active share around `0.7785`, and top outliers such as `TSLA`, `MSFT`, and `AAPL`.

## Goal

- goal: Make benchmark drift outliers actionable and auditable without changing recommendation scores, benchmark definitions, or broker/order behavior.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/tasks/benchmark-drift-outlier-decision-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Inspect latest benchmark drift payload and rebalance candidate review state.
- Classify outliers into read-only decisions such as `review_required`, `reduce_watch`, `hold_with_thesis`, or `needs_thesis_update`.
- Expose the decision path in `/api/data-health`, `/api/portfolio/{portfolio}/coverage`, and the portfolio coverage UI.
- Preserve source evidence: benchmark weight, portfolio weight, active weight, related thesis/recommendation, and risk budget policy.

## Non-Goals

- No recommendation score weight changes.
- No automatic rebalance.
- No live broker submit.
- No benchmark composition definition change unless a separate task explicitly approves it.

## Verification Commands

- verification command: focused Python tests for benchmark drift outlier decision payloads.
- verification command: `cd apps/web && npm run typecheck`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task benchmark-drift-outlier-decision-v1`
- EC2 verification: inspect `/api/data-health`, `/api/portfolio/Long%20Term%20Paper/coverage`, `/data-health`, and `/portfolio/coverage`.

## Acceptance Criteria

- Top drift outliers are not only listed as logs; each has an explicit read-only decision and next review action.
- The user can see why a drift item exists: current weight, benchmark weight, active weight, source date, thesis/recommendation link if present.
- Recommendation weights and order boundaries remain unchanged.
