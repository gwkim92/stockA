# fund-expense-ratio-public-source-v1 Contract

## Task Request

- request: Add a free, auditable public source path for ETF/fund expense ratio evidence.
- context: `fund-expense-tracking-source-v1` added source-backed liquidity from `market.daily_price_bar`, but expense ratio remains `not_collected` because the current SSGA holdings artifact does not contain it.

## Goal

- goal: SPY-like fund analysis can show expense ratio only when it comes from a named free/public source with observed date and source metadata, otherwise it remains explicitly unknown.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/fund-expense-ratio-public-source-v1/*`
  - `docs/plans/2026-05-26-fund-expense-ratio-public-source-v1.md`

## Scope

- Identify a free auditable source for SPY ETF expense ratio.
- Prefer repo-outside provider artifacts or explicit source-document ingestion over hard-coded constants.
- Store or expose source name, observed date, value, and limitations.
- Keep UI Korean and clear that the value is source-backed, stale, or unavailable.

## Non-Goals

- No paid provider.
- No guessed expense ratio.
- No tracking error/NAV implementation in this slice.
- No recommendation weight changes.
- No live broker submit.

## Schema Change Disclosure

- Schema changes are allowed only if needed to persist auditable fund metadata. Prefer existing source-document/artifact patterns if sufficient.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task fund-expense-ratio-public-source-v1`

## Acceptance Criteria

- Expense ratio is collected only when a named free/public source supports it.
- The value includes source name/date and is not a code constant.
- SPY fund analysis continues to show holdings and liquidity evidence.
- Tracking error/NAV remains explicit unknown unless a separate source-backed task implements it.
- Recommendation weights and broker/order flow remain unchanged.
