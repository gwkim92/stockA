# segment-level-sotp-valuation-allocation-v1 Contract

## Task Request

- request: Use the reported segment inputs from `segment-level-sotp-inputs-v1` to derive explicit segment-level SOTP valuation allocation evidence.
- context: SOTP now exposes SEC-reported segment revenue, operating income, and operating margin. The next gap is that users still cannot see how the existing operating-business SOTP value would be attributed across segments.

## Goal

- goal: `sum-of-parts-valuation-run` derives `reported_segment_allocations` from reported segment revenue and operating income shares, stores those allocations in SOTP assumptions, and the frontend shows the segment allocation in Korean. Existing SOTP total fair values, recommendation weights, benchmark logic, portfolio guardrails, and broker/order flow must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/segment-level-sotp-valuation-allocation-v1/*`
  - `docs/plans/2026-05-26-segment-level-sotp-valuation-allocation-v1.md`

## Scope

- Compute segment allocation weights from reported segment inputs:
  - use operating income share when operating income total is positive;
  - use revenue share when operating income share is unavailable;
  - expose the selected basis and component shares.
- Allocate the existing `operating_business_fcf` low/base/high fair value across segments without changing its total.
- Store allocations in assumptions JSON under `reported_segment_allocations`.
- Carry allocations into valuation snapshot assumptions and live DTOs.
- Render allocation rows in Korean under the SOTP section.

## Non-Goals

- Do not add segment-specific growth, CAPEX, discount rate, or multiple assumptions in this slice.
- Do not change SOTP total fair values.
- Do not change recommendation score components or weights.
- Do not change broker/order submission, paper execution, benchmark, or portfolio guardrails.
- Do not add schema unless existing JSON assumptions cannot carry the evidence.

## Schema Change Disclosure

- No schema migration is planned. The task reuses `market.sum_of_parts_component.assumptions_json` and `market.valuation_snapshot.assumptions_json`.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-level-sotp-valuation-allocation-v1`

## Acceptance Criteria

- SOTP SQL includes `reported_segment_allocations`.
- Allocation sums back to the existing operating-business fair value basis without changing component totals.
- Valuation snapshot assumptions include `reported_segment_allocations`.
- Live adapter exposes `sotp_evidence.reported_segment_allocations`.
- Frontend renders segment allocation rows in Korean.
- EC2 smoke proves `/api/stocks/AAPL` exposes non-empty allocations and keeps `score_policy=recommendation_weights_unchanged` and `order_boundary=read_only_no_order`.
