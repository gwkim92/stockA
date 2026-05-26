# cycle-ai-quality-audit-contamination-remediation-v1 Contract

## Task Request

- request: Reduce the remaining AI evidence quality issues reported by `cycle_ai_quality_audit`.
- context: EC2 data-health still reports `cycle_ai_quality_audit.status=attention_required`, with ungrounded direct tickers, macro false tickers, and duplicate RSS title issues.

## Goal

- goal: Identify the highest-impact contamination source in AI/news evidence, implement a deterministic validator or dedupe fix, rerun the quality audit, and reduce the reported issue counts without hiding real warnings.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ingest/news/`
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/`
  - `docs/tasks/cycle-ai-quality-audit-contamination-remediation-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Inspect latest EC2 `cycle_ai_quality_audit` payload and samples.
- Prioritize one root cause at a time: ungrounded direct ticker, macro false ticker, or duplicate title contamination.
- Add deterministic guardrail, validator logic, or dedupe at the data boundary.
- Rerun audit and confirm counts move in the right direction.

## Non-Goals

- No recommendation score weight changes.
- No broker/order enablement.
- No paid AI/provider requirement.
- No deleting warnings just to make the dashboard green.

## Verification Commands

- verification command: focused Python tests for changed news/AI/audit code.
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-ai-quality-audit-contamination-remediation-v1`
- EC2 verification: rerun `cycle-ai-quality-audit-run --execute` and inspect `/api/data-health`.

## Acceptance Criteria

- Root cause and chosen contamination class are documented.
- A deterministic fix or guardrail is implemented with tests.
- EC2 quality audit rerun shows reduced or more accurately classified issue counts.
- Recommendation weights and broker/order boundaries remain unchanged.
