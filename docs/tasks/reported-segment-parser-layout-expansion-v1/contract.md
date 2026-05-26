# reported-segment-parser-layout-expansion-v1 Contract

## Task Request

- request: Inspect the ADI raw SEC artifacts surfaced by `segment-history-coverage-expansion-v1` and add deterministic reported segment parser support for the observed non-AAPL segment table layout.
- context: EC2 parent `run_id=1134` proved ADI has 3 linked/raw annual documents, but current parser coverage reports `unsupported_layout` with `parsed_period_count=0`. The next professional-analysis bottleneck is parser layout support, not SEC source linkage.

## Goal

- goal: ADI-like segment table layouts either parse into `reported_segment_metric` rows with focused fixture coverage, or fail with a more specific documented unsupported reason. AAPL must remain `trend_backed` with bad-label filters intact. Recommendation weights, benchmark logic, portfolio guardrails, and broker/order flow must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/fixtures/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/reported-segment-parser-layout-expansion-v1/*`
  - `docs/plans/2026-05-26-reported-segment-parser-layout-expansion-v1.md`

## Purpose

Use the `segment-history-coverage-expansion-v1` evidence to add non-AAPL SEC segment table parser coverage, starting with ADI, so active recommendation symbols can move from `unsupported_layout` to parsed segment metrics where filings contain usable segment data.

## Scope

- Inspect ADI raw SEC artifacts fetched during EC2 `segment-history-coverage-expansion-run` `run_id=1134`.
- Add deterministic parser support only for observed, testable SEC table layouts.
- Keep existing AAPL parser behavior and bad-label filters intact.
- Add regression fixtures/tests for the new layout.
- Re-run segment history coverage for AAPL + ADI and verify AAPL remains `trend_backed` while ADI either parses or reports a more specific unsupported reason.

## Non-Goals

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No AI extraction of financial tables before deterministic parser evidence is exhausted.

## Schema Change Disclosure

- No schema migration is planned. Parser output should use existing `research.segment_footnote_evidence` and downstream SOTP/valuation paths.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_segment_history_coverage_expansion`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task reported-segment-parser-layout-expansion-v1`

## Acceptance Criteria

- New parser layout has a focused fixture test.
- Existing AAPL parser tests still pass.
- ADI coverage status improves from generic `unsupported_layout` to parsed segment evidence or a more specific documented blocker.
- Coverage report remains explicit about bad labels, single-period fallback, and unsupported layouts.
