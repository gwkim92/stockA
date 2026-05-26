# portfolio-and-fund-instrument-analysis-v1 Contract

## Task Request

- request: Add a professional analysis lane for ETF/fund-like instruments such as SPY so the system does not force them through company financial statement models.
- context: `professional-coverage-refresh-after-source-remediation-v1` proved SPY is a fund-like product for this workflow. It now has a visible `fund_company_financial_model_not_applicable` blocker, but the next step is to analyze it through holdings, benchmark composition, tracking error, exposure, expense ratio, liquidity, and portfolio role.

## Goal

- goal: ETF/fund-like instruments receive a first-class read-only professional analysis path that explains portfolio role and risks without using company revenue, margin, cash-flow, SOTP, or DCF fields.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/portfolio-and-fund-instrument-analysis-v1/*`
  - `docs/plans/2026-05-26-portfolio-and-fund-instrument-analysis-v1.md`

## Scope

- Detect ETF/fund-like instruments from existing instrument metadata and benchmark/holding evidence.
- Expose fund analysis evidence in API DTOs: holdings coverage, benchmark source, top exposures, sector/theme concentration, tracking/drift proxy, expense/liquidity placeholders where free data is missing, and portfolio role.
- Update stock/recommendation pages to show fund analysis instead of company financial-model missing-state copy for ETF/fund-like instruments.
- Keep all recommendation score components and order boundaries unchanged.

## Non-Goals

- No live broker submit.
- No recommendation weight changes.
- No paid provider.
- No synthetic company financials for ETFs/funds.
- No claim of exact tracking error without sufficient free data.

## Schema Change Disclosure

- Schema changes are allowed only if existing benchmark/portfolio tables cannot represent fund analysis evidence. Any migration must preserve read-only order boundaries and must not change scoring weights.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-and-fund-instrument-analysis-v1`

## Acceptance Criteria

- SPY no longer appears as an unexplained missing company financial model in user-facing investment flow.
- SPY stock/recommendation views show fund-specific analysis and limitations in Korean.
- Fund analysis uses holdings/benchmark/exposure evidence where available and explicit unknown/null states where unavailable.
- Recommendation weights, scoring formulas, automatic order, and broker submit remain unchanged.
