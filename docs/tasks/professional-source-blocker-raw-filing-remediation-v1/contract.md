# professional-source-blocker-raw-filing-remediation-v1 Contract

## Task Request

- request: Investigate and remediate the remaining true professional source blocker after `professional-source-gap-remediation-decision-v1`.
- context: EC2 data-health now reports only `EROK:source_blocker` and `SPY:fund_not_applicable` after GOOG remediation. `EROK` has SEC companyfacts `facts.us-gaap` missing and must not receive synthetic financial facts.

## Goal

- goal: Determine whether `EROK` can be supported through free raw SEC filing/XBRL or another public filing source, and either implement a safe backend source path or record an explicit durable exclusion from company-financial recommendation coverage.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ingest/sec/`
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/professional-source-blocker-raw-filing-remediation-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Inspect `EROK` SEC identity, filing availability, and current raw filing/XBRL feasibility.
- Use only free public sources.
- If raw filing/XBRL data is usable, add a backend parser/runner path that writes canonical source evidence without bypassing service boundaries.
- If usable public financial facts are not available, persist a clear exclusion/blocker decision so EROK does not look like a fixable coverage gap.
- Keep ETF/fund not-applicable cases separate from operating-company source blockers.

## Non-Goals

- No synthetic EROK financial facts.
- No paid provider requirement.
- No recommendation scoring weight changes.
- No live broker submit.
- No manual DB edits that bypass backend CLI/service boundaries.

## Verification Commands

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_source_gap_remediation_decision tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-source-blocker-raw-filing-remediation-v1`

## Acceptance Criteria

- EROK is no longer ambiguous: it is either supported by a free-public raw filing source path or explicitly excluded with a durable source-blocker decision.
- No EROK synthetic financial values are created.
- `/api/data-health` and `/data-health` clearly distinguish true source blocker from ETF/fund not-applicable cases.
- Recommendation scoring, weight review, and broker/order boundaries remain unchanged.
