# source-blocked-recommendation-guardrail-v1 Contract

## Task Request

- request: Prevent active recommendations from appearing professionally usable when the underlying company financial source is durably blocked.
- context: `/api/data-health` still reports `professional_source_gap_attention`; `EROK` has `active_recommendation_count=1` but raw filing remediation classified it as `durable_exclusion_until_periodic_filing`.

## Goal

- goal: Add a deterministic recommendation guardrail that marks source-blocked operating-company recommendations as blocked for professional decision use until a supported periodic filing or dedicated safe parser exists.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/signal/`
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/`
  - `docs/tasks/source-blocked-recommendation-guardrail-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Identify recommendations whose instrument has a durable source blocker.
- Expose the block in recommendation/data-health/frontend DTOs without changing score weights.
- Keep the recommendation record auditable; do not silently delete historical recommendations.
- Ensure broker/order and paper validation paths cannot treat source-blocked recommendations as executable.

## Non-Goals

- No recommendation score weight changes.
- No live broker submit.
- No fabrication of financial facts from prospectus-only filings.
- No paid data provider requirement.

## Verification Commands

- verification command: focused Python tests for recommendation/source-block guardrail logic.
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task source-blocked-recommendation-guardrail-v1`
- EC2 verification: inspect `/api/data-health`, `/stocks/EROK`, and the linked EROK recommendation detail.

## Acceptance Criteria

- Source-blocked recommendations are visible as blocked, not silently trusted.
- Recommendation scoring weights remain unchanged.
- Broker/order flow remains read-only and blocked.
- EROK no longer looks like a normal professional-analysis recommendation while periodic filing data is unavailable.
