# professional-coverage-refresh-after-source-remediation-v1 Contract

## Task Request

- request: Refresh professional analysis coverage after segment/source remediation and verify stock/recommendation evidence remains coherent.
- context: Segment/source cleanup now classifies AAPL/DIS/FANG/GILD as trend-backed, ADI/AEIS/ALAB/ARM/ELF as single segment/no-detail cases, and EROK as `sec_companyfacts_missing_us_gaap_facts`. The next step is to refresh downstream professional analysis artifacts without changing weights or orders.

## Goal

- goal: Active recommendation/portfolio professional coverage is refreshed from the cleaned source state, and API/frontend evidence shows accurate financial, valuation, SOTP, and source blocker context without score/order mutation.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_coverage_expansion.py`
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/professional-coverage-refresh-after-source-remediation-v1/*`
  - `docs/plans/2026-05-26-professional-coverage-refresh-after-source-remediation-v1.md`

## Scope

- Re-run or verify professional coverage expansion after source cleanup.
- Confirm SOTP/valuation/recommendation detail no longer uses polluted ARM segment labels.
- Confirm EROK is presented as source-data unavailable rather than parser failure.
- Update API/frontend wording only if DTOs expose stale or misleading evidence.

## Non-Goals

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No synthetic segment rows for single-segment companies.

## Schema Change Disclosure

- No schema migration is planned unless the refresh reveals a missing evidence field that cannot be represented in existing DTOs.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_segment_history_coverage_expansion`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-coverage-refresh-after-source-remediation-v1`

## Acceptance Criteria

- Professional coverage refresh runs or is verified on EC2 after source cleanup.
- ARM polluted labels (`Operating expenses`, `Non-staff costs`) do not appear as reported segments.
- EROK is visible as a precise source-data blocker where relevant.
- Recommendation weights and broker/order flow remain unchanged.
