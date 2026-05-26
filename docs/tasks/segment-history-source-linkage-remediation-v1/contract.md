# segment-history-source-linkage-remediation-v1 Contract

## Task Request

- request: Resolve the remaining `missing_source_document_linkage` blockers from the broader segment history coverage run.
- context: EC2 breadth run `1254` left ARM and EROK as source/companyfacts blockers after AAPL/DIS/FANG/GILD were trend-backed, ADI/ALAB/ELF/AEIS were classified as single reportable segment cases, and AEIS no longer has a generic unsupported parser layout.

## Goal

- goal: ARM and EROK failures are explained by deterministic evidence and, where possible, remediated through supported SEC/source-document linkage or precise non-remediable classifications. Recommendation weights, benchmark logic, portfolio guardrails, and broker/order flow must not change.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/financial_period_source_linkage.py`
  - `src/stockanalysis/operations/segment_history_coverage_expansion.py`
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `tests/test_financial_period_source_linkage.py`
  - `tests/test_segment_history_coverage_expansion.py`
  - `tests/fixtures/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/segment-history-source-linkage-remediation-v1/*`
  - `docs/plans/2026-05-26-segment-history-source-linkage-remediation-v1.md`

## Scope

- Inspect ARM and EROK companyfacts/source-document state on EC2.
- Identify whether the blocker is missing SEC companyfacts data, unsupported ETF/fund/security type, missing raw filing artifact, or linkage mismatch.
- Add deterministic classification or remediation only where supported by actual SEC/source evidence.
- Re-run bounded coverage for the affected symbols and guardrail checks.

## Non-Goals

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No AI extraction of financial tables before deterministic evidence is exhausted.
- No fake fiscal periods or inferred SEC documents.

## Schema Change Disclosure

- No schema migration is planned until the blocker evidence proves one is required.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_segment_history_coverage_expansion`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-history-source-linkage-remediation-v1`

## Acceptance Criteria

- ARM and EROK source/companyfacts blocker causes are documented from EC2 evidence.
- Any remediated symbol moves to a more accurate coverage status without fake data.
- Any non-remediated symbol has a precise deterministic blocker instead of ambiguous failure text.
- Score/order guardrails remain unchanged.
