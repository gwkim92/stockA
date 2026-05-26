# reported-segment-unit-normalization-v1 Contract

## Task Request

- request: Normalize or clearly scale reported segment metric units from SEC filing context before segment-specific valuation assumptions are added.
- context: Apple-style segment rows are now parsed and used in SOTP input/allocation evidence, but EC2 values still show `USD_as_reported` because the phrase `dollars in millions` sits outside the table HTML. This can confuse users even though allocation shares are mathematically correct.

## Goal

- goal: The reported segment parser uses table-neighborhood context to infer `USD_millions_as_reported` or `USD_thousands_as_reported`, stores unit metadata in `research.segment_footnote_evidence`, and the frontend renders a Korean unit label such as `백만 달러 단위`. Recommendation weights, SOTP fair values, broker/order flow, benchmark logic, and portfolio guardrails must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/reported-segment-unit-normalization-v1/*`
  - `docs/plans/2026-05-26-reported-segment-unit-normalization-v1.md`

## Scope

- Infer reported metric unit from table HTML plus nearby preceding/neighbor text.
- Preserve existing simple table parsing.
- Update transposed Apple-style fixture expectation to require `USD_millions_as_reported`.
- Render Korean labels for `USD_millions_as_reported`, `USD_thousands_as_reported`, and `USD_as_reported`.
- Rerun EC2 parser/SOTP/valuation so AAPL segment inputs use the normalized unit.

## Non-Goals

- Do not convert stored values to absolute dollars in this slice.
- Do not change SOTP fair value math or allocation weights.
- Do not change recommendation scores, score weights, benchmark splits, or broker/order flow.
- Do not add a new schema migration.

## Schema Change Disclosure

- No schema migration is planned. Existing `metric_unit` and `assumptions_json` carry the normalized unit metadata.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task reported-segment-unit-normalization-v1`

## Acceptance Criteria

- Apple transposed segment fixture parses all rows as `USD_millions_as_reported`.
- Parser assumptions include unit metadata without recommendation mutation.
- Frontend renders `백만 달러 단위` for `USD_millions_as_reported`.
- EC2 parser rerun updates AAPL segment rows to `USD_millions_as_reported`.
- EC2 `/api/stocks/AAPL` exposes normalized metric units and keeps `score_policy=recommendation_weights_unchanged`, `order_boundary=read_only_no_order`.
