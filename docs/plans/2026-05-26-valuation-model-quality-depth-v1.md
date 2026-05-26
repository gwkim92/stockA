# valuation-model-quality-depth-v1 Plan

## Summary

- Goal: make valuation evidence analyst-readable by showing assumptions, sensitivity, data quality, and limitations for DCF-lite, relative multiple, and scenario range.
- Boundary: no recommendation scoring, benchmark, or order-flow changes.

## Implementation

1. Extend valuation DTO method payloads with:
   - `upside_low`, `upside_base`, `upside_high`
   - `valuation_gap`
   - Korean `evidence_summary`
   - `assumption_items`
   - `sensitivity_cases`
   - `data_quality`
   - `limitations`
2. Add `valuation_quality` to the overall range payload.
3. Enrich future `valuation_snapshot` assumptions JSON in `professional_equity_analysis.py`.
4. Update shared `ValuationTargetRangeCard` to render the deeper evidence across stock/recommendation/thesis pages.
5. Add unit/contract tests for DTO shape, SQL assumption keys, unchanged scoring/order boundary.

## Guardrails

- No `signal.recommendation_score_component` mutation.
- No broker submit or automatic order enablement.
- No benchmark/evaluation split change.
- Missing data remains explicit.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_professional_equity_analysis`
- `PYTHONPATH=src python3 -m compileall -q src tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task valuation-model-quality-depth-v1`
