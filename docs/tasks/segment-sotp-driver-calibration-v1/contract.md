# segment-sotp-driver-calibration-v1 Contract

## Task Request

- request: Calibrate segment-specific SOTP assumptions with multi-period segment trends and industry/segment driver templates.
- context: `segment-specific-sotp-assumptions-v1` added visible growth, margin, valuation multiple, and driver assumptions, but those assumptions are single-period deterministic proxies. Professional analysis needs to distinguish observed trend evidence from one-period margin/share heuristics.

## Goal

- goal: SOTP assumptions include historical segment period count, observed revenue CAGR, observed margin change, calibration method, and driver template labels. The frontend renders those fields in Korean so users can tell whether each segment assumption is trend-backed or single-period proxy-backed. Recommendation weights, SOTP totals, benchmark logic, portfolio guardrails, and broker/order flow must not change.

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
  - `docs/tasks/segment-sotp-driver-calibration-v1/*`
  - `docs/plans/2026-05-26-segment-sotp-driver-calibration-v1.md`

## Scope

- Add historical segment CTEs using `research.segment_footnote_evidence` across available `period_end` rows.
- Calculate observed segment revenue CAGR and margin change when at least two periods exist.
- Select a deterministic driver template from the segment label, such as services installed base, hardware product cycle, geographic demand cycle, AI/cloud cycle, or energy cycle.
- Add calibration fields to `reported_segment_assumptions`.
- Expose calibration fields through the live adapter and TypeScript DTOs.
- Render trend-backed vs proxy-backed assumption context in Korean.

## Non-Goals

- Do not change SOTP fair value totals.
- Do not change recommendation score components or weights.
- Do not add broker/order submit, benchmark changes, portfolio guardrail changes, or paid data providers.
- Do not claim this is a full segment DCF or segment CAPEX model.

## Schema Change Disclosure

- No schema migration is planned. Existing SOTP and valuation assumptions JSON carry calibration evidence.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-sotp-driver-calibration-v1`

## Acceptance Criteria

- SOTP SQL includes multi-period segment history and trend CTEs.
- `reported_segment_assumptions` include `calibration_method`, `driver_template_label`, `history_period_count`, `observed_revenue_cagr`, and `observed_margin_change`.
- Live adapter exposes the calibration fields.
- Frontend renders Korean trend/proxy context under `사업부별 가정`.
- Tests prove score/order boundaries remain unchanged.
- EC2 smoke proves `/api/stocks/AAPL` and `/stocks/AAPL` expose calibration context.
