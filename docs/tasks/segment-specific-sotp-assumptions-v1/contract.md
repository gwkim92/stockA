# segment-specific-sotp-assumptions-v1 Contract

## Task Request

- request: Add segment-specific growth, margin, multiple, and driver assumptions after reported segment metric units have been normalized.
- context: SOTP now carries reported segment inputs, normalized unit labels, and value allocations. The next gap is that users can see segment value distribution but cannot see what segment-level assumptions would be used in a professional SOTP review.

## Goal

- goal: `sum-of-parts-valuation-run` derives conservative, deterministic segment-level assumption rows from reported segment revenue, operating income, margin, and allocation share, stores them in SOTP assumptions JSON, and the frontend renders them in Korean. Recommendation weights, SOTP fair value totals, benchmark logic, portfolio guardrails, and broker/order flow must not change.

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
  - `docs/tasks/segment-specific-sotp-assumptions-v1/*`
  - `docs/plans/2026-05-26-segment-specific-sotp-assumptions-v1.md`

## Scope

- Build segment assumptions from existing reported segment input/allocation evidence:
  - base growth rate;
  - low/base/high multiple range;
  - margin assumption from reported operating margin;
  - key driver label and rationale;
  - source document/run lineage.
- Store assumptions under `reported_segment_assumptions` in SOTP component and valuation snapshot assumptions JSON.
- Expose `sotp_evidence.reported_segment_assumptions` from the live adapter.
- Render a Korean `사업부별 가정` section on valuation target range cards.
- Keep the task read-only with respect to recommendation scoring and order execution.

## Non-Goals

- Do not change SOTP fair value low/base/high totals in this slice.
- Do not use the assumptions to change recommendation score components or weights.
- Do not add live broker submit, order intent mutation, benchmark changes, or portfolio guardrail changes.
- Do not add paid data providers or external valuation services.
- Do not add a schema migration unless existing JSON assumptions cannot carry the evidence.

## Schema Change Disclosure

- No schema migration is planned. The task reuses `market.sum_of_parts_component.assumptions_json` and `market.valuation_snapshot.assumptions_json`.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-specific-sotp-assumptions-v1`

## Acceptance Criteria

- SOTP SQL creates `reported_segment_assumptions`.
- Valuation snapshot assumptions carry `reported_segment_assumptions`.
- Live adapter exposes `sotp_evidence.reported_segment_assumptions`.
- Frontend renders segment-level assumptions in Korean.
- Tests prove no recommendation score mutation and no order boundary change.
- EC2 smoke proves `/api/stocks/AAPL` exposes non-empty segment assumptions and `/stocks/AAPL` renders `사업부별 가정`.
