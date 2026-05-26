# segment-history-backfill-v1 Contract

## Task Request

- request: Backfill historical reported segment periods from prior SEC filings so segment SOTP driver calibration can use multi-period trend evidence instead of latest-period-only proxy evidence.
- context: `segment-sotp-driver-calibration-v1` computes `history_period_count`, observed revenue CAGR, observed margin change, and calibration method, but EC2 currently has one AAPL reported segment period. The current parser candidate query also selects one latest period per instrument by default.

## Goal

- goal: A backend operation can fetch/link/parse multiple historical annual SEC filing periods for a configured filer, and `reported-segment-footnote-parser-run` can parse more than one period per instrument. SOTP/valuation then reuse the existing multi-period trend CTEs. Recommendation weights, benchmark logic, portfolio guardrails, and broker/order flow must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/segment_history_backfill.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_segment_history_backfill.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/segment-history-backfill-v1/*`
  - `docs/plans/2026-05-26-segment-history-backfill-v1.md`

## Scope

- Extend reported segment parser candidate selection with `periods_per_instrument`.
- Add a read-only/planned and executable `segment-history-backfill-run` operation.
- The operation orchestrates existing backend boundaries: financial period source linkage/raw fetch, reported segment parser, SOTP valuation, and valuation snapshot.
- Add the weekly SEC filings profile arguments so automation can parse historical segment periods rather than only the latest period.
- Prove the generated SQL and CLI preserve `recommendation_scoring_mutated=false`.

## Non-Goals

- Do not change recommendation score components or weights.
- Do not change SOTP fair value formulas.
- Do not add live broker submit, benchmark split changes, or paid providers.
- Do not claim every issuer has segment history; missing parser coverage remains explicit.

## Schema Change Disclosure

- No schema migration is planned. Historical rows are stored in existing `research.segment_footnote_evidence` with distinct `period_end`.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_segment_history_backfill tests.test_data_operations_cli tests.test_operating_data_orchestrator`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "segment-history-backfill-run|reported-segment-footnote-parser-run"`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-history-backfill-v1`

## Acceptance Criteria

- `reported-segment-footnote-parser-run` accepts and reports `periods_per_instrument`.
- Candidate SQL selects bounded historical periods per instrument rather than hardcoding one latest period.
- `segment-history-backfill-run` exists in `stockanalysis-operations` and preserves score/order boundaries.
- Weekly SEC filings profile uses historical segment parser mode.
- Tests cover planner/dry-run/execute orchestration without external SEC calls.
- EC2 smoke proves AAPL has more than one reported segment period or records the exact blocker if SEC source coverage/parser coverage is insufficient.
