# segment-history-coverage-breadth-expansion-v1 Contract

## Task Request

- request: Broaden reported segment history coverage from the AAPL/ADI proof to the active recommendation and portfolio symbol set, and rank remaining segment parser/data blockers.
- context: AAPL is trend-backed and ADI is now correctly classified as a single reportable segment case. The system still needs to know which active symbols have segment history coverage, which do not need segment parsing, and which need deterministic parser/data remediation.

## Goal

- goal: A broader EC2 `segment-history-coverage-expansion-run` produces per-symbol statuses for active recommendations and portfolio holdings, with remaining blockers grouped into actionable remediation categories. Recommendation weights, benchmark logic, portfolio guardrails, and broker/order flow must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/segment_history_coverage_expansion.py`
  - `tests/test_segment_history_coverage_expansion.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/segment-history-coverage-breadth-expansion-v1/*`
  - `docs/plans/2026-05-26-segment-history-coverage-breadth-expansion-v1.md`

## Scope

- Execute a broader active target coverage run on EC2.
- Preserve existing AAPL and ADI classifications.
- Add reporting improvements only if the broader run exposes ambiguous status categories.
- Record the next exact parser/data remediation target from evidence.

## Non-Goals

- No recommendation weight changes.
- No live broker submit.
- No paid external financial data provider.
- No AI extraction of financial tables.

## Schema Change Disclosure

- No schema migration is planned unless the evidence shows that coverage status needs durable storage beyond the existing runner artifact.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_segment_history_coverage_expansion tests.test_professional_equity_analysis`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-history-coverage-breadth-expansion-v1`

## Acceptance Criteria

- EC2 artifact records at least 5 active/portfolio target statuses or documents why fewer are available.
- AAPL remains `trend_backed`.
- ADI remains `single_reportable_segment_no_disaggregated_segment_table`.
- Remaining non-single-segment blockers are ranked for the next deterministic remediation task.
- Recommendation scoring/order guardrails remain unchanged.
