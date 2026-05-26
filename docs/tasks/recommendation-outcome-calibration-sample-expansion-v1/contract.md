# recommendation-outcome-calibration-sample-expansion-v1 Contract

## Task Request

- request: Expand recommendation outcome and calibration evidence before any professional-analysis component weight change.
- context: The professional analysis stack now includes financial quality, peer relative, valuation, SOTP, thesis lifecycle gates, portfolio risk budget, position sizing, and ETF/fund source evidence. Weight changes remain blocked until outcome evidence is strong enough.

## Goal

- goal: Recommendation quality review can evaluate professional components against a broader, auditable outcome sample without changing recommendation scores, benchmark splits, or order flow.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/performance/`
  - `src/stockanalysis/signal/`
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/recommendation-outcome-calibration-sample-expansion-v1/*`
  - `docs/plans/2026-05-27-recommendation-outcome-calibration-sample-expansion-v1.md`

## Scope

- Audit current recommendation outcome sample size, horizon coverage, and stale/missing outcome reasons.
- Add or extend a backend CLI runner that backfills reproducible outcome evidence from existing market price history and paper validation records.
- Store component-level calibration diagnostics for zero-weight professional components without changing their weights.
- Expose outcome/calibration readiness on `/api/data-health`, recommendation detail, or portfolio quality views if the DTO already supports it or can be extended safely.
- Keep all generated evidence auditable with run ids, artifact paths, and source data dates.

## Non-Goals

- No recommendation weight changes.
- No benchmark split changes.
- No live broker submit or order write API.
- No paid data providers.
- No fabricated outcomes when market price history is missing.

## Schema Change Disclosure

- Schema changes are allowed only if current performance/eval tables cannot represent component-level calibration diagnostics and missing outcome reasons.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-outcome-calibration-sample-expansion-v1`

## Acceptance Criteria

- Outcome sample size, missing reasons, and horizon coverage are visible in a reproducible report.
- Professional component calibration diagnostics are stored or emitted without mutating score weights.
- Any blocked weight-review condition is explicit and user-facing.
- Existing recommendation, paper safety, and order-boundary guardrails remain unchanged.
