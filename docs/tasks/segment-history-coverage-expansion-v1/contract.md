# segment-history-coverage-expansion-v1 Contract

## Task Request

- request: Expand trend-backed reported segment history from the AAPL proof to active recommendation and portfolio symbols, and report unsupported issuer/table layouts as explicit quality gaps.
- context: `segment-history-backfill-v1` proved AAPL can use multi-period segment history, but professional coverage cannot rely on a single-company proof. Active recommendations and portfolio holdings need the same coverage attempt, with per-symbol status showing whether the blocker is missing SEC linkage, missing raw filings, parser layout support, contamination, or insufficient history.

## Goal

- goal: A backend operation can select active recommendation and portfolio symbols, resolve SEC CIKs, run bounded segment history backfill through existing service boundaries, and emit a coverage report with parsed/trend-backed/single-period/unsupported statuses. Recommendation weights, benchmark logic, portfolio guardrails, and broker/order flow must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/segment_history_coverage_expansion.py`
  - `src/stockanalysis/operations/financial_period_source_linkage.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_segment_history_coverage_expansion.py`
  - `tests/test_financial_period_source_linkage.py`
  - `tests/test_data_operations_cli.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/segment-history-coverage-expansion-v1/*`
  - `docs/plans/2026-05-26-segment-history-coverage-expansion-v1.md`

## Purpose

Expand trend-backed reported segment history from the AAPL proof to active recommendation and portfolio coverage, while reporting unsupported issuer/table layouts instead of hiding them behind single-period proxy assumptions.

## Scope

- Use existing `stockanalysis-operations` backend CLI/service boundaries.
- Run bounded historical reported segment backfill for active recommendation and portfolio symbols with known SEC CIK coverage.
- Record coverage counts by symbol: periods parsed, segment labels parsed, unsupported candidate count, single-period fallback count, and bad-label count.
- Keep recommendation scoring weights, benchmark rules, portfolio guardrails, and broker/order flow unchanged.
- Prefer deterministic parser coverage and explicit quality reporting before adding AI extraction for financial tables.

## Non-Goals

- No recommendation weight changes.
- No live broker submit.
- No paid external financial data provider.
- No unbounded SEC archive crawling.

## Schema Change Disclosure

- No schema migration is planned. The coverage runner reports status using existing SEC, financial period source, parser, SOTP, valuation, and pipeline run tables.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_segment_history_coverage_expansion tests.test_segment_history_backfill tests.test_data_operations_cli`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "segment-history-coverage-expansion-run|segment-history-backfill-run"`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-history-coverage-expansion-v1`

## Acceptance Criteria

- A backend runner or existing runner profile can process a bounded active-symbol set and produce a coverage report.
- Unsupported layouts are surfaced as quality gaps, not silent success.
- AAPL remains clean: 4 annual periods, 5 segment labels, bad segment count `0`, trend-backed SOTP assumptions.
- At least one non-AAPL active symbol is attempted and its result is reported as parsed or unsupported.
- Task handoff records EC2 run IDs and API/DB evidence.
