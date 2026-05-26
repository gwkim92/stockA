# professional-source-gap-remediation-decision-v1 Contract

## Task Request

- request: Use the live ranked professional source gap list to decide and execute the next safe deterministic remediation step.
- context: `professional-source-gap-prioritization-v1` exposed live gaps on EC2. Current top examples are `EROK:source_blocker`, `GOOG:coverage_gap`, and `SPY:fund_not_applicable`.

## Goal

- goal: Resolve or explicitly classify the top live professional source gap without fabricating data, changing recommendation weights, or enabling broker/order flow.

## Scope

- Inspect `/api/data-health` `professional_source_gap_prioritization`.
- For true source blockers such as `sec_companyfacts_missing_us_gaap_facts`, record whether free public data can remediate the gap.
- If the top blocker cannot be remediated with free public data, leave it blocked and move to the next deterministic coverage gap.
- Run only existing backend CLI/service-boundary remediation commands.
- Refresh source-gap visibility after the remediation decision.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_source_gap_remediation_decision.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_professional_source_gap_remediation_decision.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/professional-source-gap-remediation-decision-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Non-Goals

- No synthetic company financial facts.
- No recommendation scoring weight changes.
- No live broker submit.
- No paid data provider requirement.
- No manual DB edits that bypass backend CLI/service boundaries.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-source-gap-remediation-decision-v1`

## Acceptance Criteria

- Top live source gap is classified as remediated, non-remediable with current free public data, or queued for a specific backend remediation command.
- ETF/fund not-applicable cases remain excluded from failed company-financial remediation.
- `/api/data-health` and `/data-health` still show source-gap state after the decision.
- Recommendation scoring, weight review, and broker/order boundaries remain unchanged.
