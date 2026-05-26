# portfolio-review-decision-history-v1 Contract

## Task Request

- request: Persist or otherwise audit portfolio review decisions that are currently derived from benchmark drift and position sizing payloads.
- context: `benchmark-drift-outlier-decision-v1` makes drift outliers understandable in the UI, but those review decisions are still read-time DTO derivations.

## Goal

- goal: Create a durable read-only history of professional portfolio review decisions without enabling automatic rebalancing or live broker orders.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `db/migrations/`
  - `tests/`
  - `apps/web/`
  - `docs/tasks/portfolio-review-decision-history-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Decide whether review decisions should be stored as `eval_run` artifacts, a dedicated portfolio review table, or an existing audit envelope.
- Preserve source evidence: benchmark source/date, active weight, policy threshold, thesis/recommendation references, and order boundary.
- Expose latest and recent review decision history in `/api/data-health` or portfolio coverage without changing scores or orders.

## Non-Goals

- No automatic rebalance.
- No recommendation score weight changes.
- No live broker submit.
- No benchmark composition definition changes.

## Verification Commands

- verification command: focused Python tests for decision-history generation and read-only API payloads.
- verification command: `cd apps/web && npm run typecheck`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-review-decision-history-v1`
