# fund-nav-premium-discount-source-v1 Contract

## Task Request

- request: Add free, auditable source handling for ETF/fund NAV and market-price/NAV premium-discount evidence.
- context: `fund-expense-ratio-public-source-v1` added official source-backed expense ratio, while tracking error/NAV drift remains unknown.

## Goal

- goal: SPY-like fund analysis can show NAV and premium/discount only when a named free/public source supports the values, otherwise those fields remain explicitly unknown.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/fund-nav-premium-discount-source-v1/*`
  - `docs/plans/2026-05-27-fund-nav-premium-discount-source-v1.md`

## Scope

- Reuse the official State Street SPDR product page or another free auditable source if it exposes NAV, market price, and as-of dates.
- Store source name, URL, observed date, NAV value, market price if available, and premium/discount calculation if both sides are source-backed.
- Render Korean source-backed NAV/premium-discount evidence on stock and recommendation detail.
- Keep true tracking error unknown unless a separate multi-period benchmark-return source is implemented.

## Non-Goals

- No paid provider.
- No guessed NAV, premium/discount, or tracking error.
- No recommendation weight changes.
- No live broker submit.

## Schema Change Disclosure

- Schema changes are allowed only if existing `market.fund_metric_snapshot` cannot represent the required source-backed fund metrics.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_fund_expense_ratio_provider`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task fund-nav-premium-discount-source-v1`

## Acceptance Criteria

- NAV and premium/discount are collected only from named free/public sources.
- Any calculated premium/discount uses source-backed NAV and market price with matching or clearly disclosed dates.
- SPY fund analysis continues to show holdings, liquidity, and expense ratio evidence.
- Tracking error remains explicit unknown unless a source-backed tracking task implements it.
- Recommendation weights and broker/order flow remain unchanged.
