# fund-expense-tracking-source-v1 Contract

## Task Request

- request: Add free/explicit-source handling for ETF expense ratio, tracking error/NAV drift, and liquidity evidence in the fund analysis lane.
- context: `portfolio-and-fund-instrument-analysis-v1` made SPY analysis visible through holdings and portfolio role, but expense ratio and tracking error currently show `not_collected`.

## Goal

- goal: ETF/fund analysis can distinguish collected fund metadata from honest unknown states, and SPY-like instruments show expense/tracking/liquidity evidence only when a free public or already-collected source supports it.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/fund-expense-tracking-source-v1/*`
  - `docs/plans/2026-05-26-fund-expense-tracking-source-v1.md`

## Scope

- Inspect available free sources and current DB artifacts for expense ratio, NAV/premium-discount, tracking proxy, average volume, and liquidity.
- Add deterministic backend DTO fields or source ingestion only when the source is free, explicit, and auditable.
- Preserve `not_collected`/`unknown` states where no reliable free source is present.
- Render source, observed date, and limitations in Korean.

## Non-Goals

- No paid provider.
- No live broker submit.
- No recommendation weight changes.
- No guessed tracking error or expense ratio.
- No forced company financial model for ETF/fund-like instruments.

## Schema Change Disclosure

- Schema changes are allowed only if needed to persist auditable fund metadata. Prefer existing artifacts/benchmark tables if sufficient.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task fund-expense-tracking-source-v1`

## Acceptance Criteria

- Fund analysis shows expense/tracking/liquidity source state as collected or explicitly unknown.
- Any collected values include source name/date and do not rely on unverified constants.
- SPY page remains read-only and continues to show holdings-based analysis.
- Recommendation weights and broker/order flow remain unchanged.
