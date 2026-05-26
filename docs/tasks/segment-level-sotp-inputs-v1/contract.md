# segment-level-sotp-inputs-v1 Contract

## Task Request

- request: Use the real `reported_segment_metric` rows created by `reported-segment-parser-quality-v1` as explicit SOTP inputs and user-visible valuation evidence.
- context: The project now parses Apple-style SEC segment tables into `research.segment_footnote_evidence`, but SOTP still mainly shows proxy components plus raw segment evidence rows. The next step is to expose segment revenue, operating income, and margin as structured SOTP input without changing recommendation weights.

## Goal

- goal: `sum-of-parts-valuation-run` aggregates reported segment revenue and operating income by segment into `reported_segment_inputs`, carries those inputs into valuation snapshot assumptions, and the frontend shows them in Korean under SOTP so users can see which business segments informed the valuation. Recommendation score weights, broker/order flow, benchmark splits, and portfolio rules must not change.

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
  - `docs/tasks/segment-level-sotp-inputs-v1/*`
  - `docs/plans/2026-05-26-segment-level-sotp-inputs-v1.md`

## Scope

- Aggregate `research.segment_footnote_evidence` rows with `evidence_type='reported_segment_metric'`.
- Pair `segment_revenue` and `segment_operating_income` for the same instrument/segment/period when available.
- Compute `operating_margin` when revenue is positive.
- Include source document, period, confidence, and source run id in the structured input payload.
- Add the structured payload to SOTP component assumptions and valuation snapshot assumptions.
- Expose the structured payload through the live frontend DTO and render it as a Korean segment input list.

## Non-Goals

- Do not create a full sell-side segment-level DCF model in this slice.
- Do not change recommendation scoring weights or score components.
- Do not change broker submit, paper trading execution, benchmark, or portfolio guardrails.
- Do not add paid data providers or external vector/graph/RAG services.
- Do not add schema unless existing JSON assumptions cannot carry the data.

## Schema Change Disclosure

- No schema migration is planned. The task reuses `research.segment_footnote_evidence`, `market.sum_of_parts_component.assumptions_json`, and `market.valuation_snapshot.assumptions_json`.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-level-sotp-inputs-v1`

## Acceptance Criteria

- SOTP SQL references `reported_segment_inputs` and carries segment revenue, operating income, operating margin, period, source document, and confidence.
- Valuation snapshot assumptions include `reported_segment_inputs`.
- Live adapter exposes `sotp_evidence.reported_segment_inputs`.
- The shared valuation card renders reported segment inputs in Korean.
- Tests prove the SQL/DTO shape exists and recommendation scoring remains untouched.
- EC2 smoke reruns SOTP and valuation snapshot after parser data and shows at least one AAPL reported segment input.
