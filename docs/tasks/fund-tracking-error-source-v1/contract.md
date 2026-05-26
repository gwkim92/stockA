# fund-tracking-error-source-v1 Contract

## Task Request

- request: Add free, auditable source handling for ETF/fund tracking error evidence, or keep tracking error explicitly unknown if no acceptable free source exists.
- context: `fund-nav-premium-discount-source-v1` added one-day NAV and market-price/NAV premium-discount evidence. That is not true tracking error.

## Goal

- goal: SPY-like fund analysis can distinguish source-backed multi-period tracking error from one-day NAV premium/discount and show only verified tracking error values.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/fund-tracking-error-source-v1/*`
  - `docs/plans/2026-05-27-fund-tracking-error-source-v1.md`

## Scope

- Research no-cost/public sources for ETF tracking difference or tracking error.
- Prefer source-backed metric import when the provider exposes multi-period fund return and benchmark return or published tracking error.
- If a source provides fund return and benchmark return but not tracking error, store tracking difference only if the metric name and calculation window are explicit.
- Keep one-day premium/discount separate from tracking error.
- Render Korean source-backed tracking error/tracking difference evidence on stock and recommendation detail.

## Non-Goals

- No paid provider.
- No guessed tracking error from one-day NAV premium/discount.
- No recommendation weight changes.
- No live broker submit.

## Schema Change Disclosure

- Schema changes are allowed only if existing `market.fund_metric_snapshot` cannot represent tracking error or tracking difference with source, window, and benchmark metadata.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_fund_expense_ratio_provider`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task fund-tracking-error-source-v1`

## Acceptance Criteria

- Tracking error is shown only when a named public/free source supports the value and window.
- Tracking difference is not mislabeled as tracking error.
- One-day NAV premium/discount remains a separate field.
- SPY fund analysis continues to show holdings, liquidity, expense ratio, and NAV premium/discount evidence.
- Recommendation weights and broker/order flow remain unchanged.
