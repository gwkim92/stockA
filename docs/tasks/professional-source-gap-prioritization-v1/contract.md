# professional-source-gap-prioritization-v1 Contract

## Task Request

- request: Rank remaining professional analysis source gaps by investment impact and remediation action.
- context: recommendation outcome windows are not due until 2026-06-20, so the next useful progress is improving professional analysis coverage quality instead of changing weights.

## Goal

- goal: `/data-health` or the relevant professional analysis surfaces should show which symbols still lack financial/valuation/industry/fund source evidence, why they are blocked, and what deterministic backend action should remediate them.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/professional-source-gap-prioritization-v1/*`
  - `docs/plans/2026-05-27-professional-source-gap-prioritization-v1.md`

## Scope

- Use existing professional coverage/source blocker outputs.
- Prioritize gaps by active recommendation exposure and missing layer count.
- Separate true source blockers from fund/company-not-applicable cases.
- Expose the next remediation action without changing recommendation weights.

## Non-Goals

- No recommendation weight changes.
- No synthetic company financials.
- No live broker/order submit.
- No paid data source requirement.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-source-gap-prioritization-v1`

## Acceptance Criteria

- Remaining source gaps are visible and sorted by priority.
- Fund/ETF not-applicable cases are not mislabeled as failed company financial analysis.
- Each gap includes a concrete next remediation action or a reason it cannot be remediated with free public data.
