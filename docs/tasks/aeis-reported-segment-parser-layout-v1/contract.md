# aeis-reported-segment-parser-layout-v1 Contract

## Task Request

- request: Inspect AEIS raw SEC artifacts and add deterministic parser support or a precise blocker for the remaining true unsupported reported segment layout.
- context: EC2 breadth run `1254` selected 10 active/portfolio symbols. AAPL/DIS/FANG/GILD are trend-backed, ADI/ALAB/ELF are single reportable segment cases, ARM/EROK are source/companyfacts blockers, and AEIS remains `unsupported_layout` with raw/source annual documents.

## Goal

- goal: AEIS coverage improves from generic `unsupported_layout` to parsed reported segment evidence or a more specific documented blocker. AAPL must remain `trend_backed`; ADI must remain `single_reportable_segment_no_disaggregated_segment_table`; recommendation weights, benchmark logic, portfolio guardrails, and broker/order flow must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/segment_history_coverage_expansion.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_segment_history_coverage_expansion.py`
  - `tests/fixtures/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/aeis-reported-segment-parser-layout-v1/*`
  - `docs/plans/2026-05-26-aeis-reported-segment-parser-layout-v1.md`

## Scope

- Inspect AEIS raw SEC filings and table contexts.
- Add a fixture and parser regression for the observed layout if there is usable segment data.
- Otherwise add a precise deterministic skip reason.
- Re-run bounded EC2 coverage for AAPL/ADI/AEIS.

## Non-Goals

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No prompt-only financial table extraction.

## Schema Change Disclosure

- No schema migration is planned.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_segment_history_coverage_expansion`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task aeis-reported-segment-parser-layout-v1`

## Acceptance Criteria

- AEIS raw SEC table shape is documented by fixture or evidence notes.
- AEIS no longer appears as generic `unsupported_layout` without explanation.
- AAPL and ADI regressions remain stable.
- Score/order guardrails remain unchanged.
