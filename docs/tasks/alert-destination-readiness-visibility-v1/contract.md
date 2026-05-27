# alert-destination-readiness-visibility-v1 Contract

## Task Request

- request: Make the remaining `alert_destination` gate evidence-based instead of a static unexplained open gate.
- context: EC2 now has production FastAPI readiness and profile scheduler evidence, but alert delivery is not yet proven. Closing the gate without a reachable external destination would be unsafe.

## Goal

- goal: `/api/data-health` and `/data-health` explain alert destination readiness, keep the gate open for missing or local-only destinations, and close it only when an external destination has a recent passed test artifact.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/alert-destination-readiness-visibility-v1/*`
  - `docs/plans/2026-05-27-alert-destination-readiness-visibility-v1.md`

## Invariants

- Do not print, persist, or expose webhook URLs, email credentials, API keys, or tokens.
- Do not close the gate for local-only journal/file logging.
- Do not change recommendation weights, portfolio positions, benchmark composition, thesis state, or broker/order flow.
- Do not enable live broker submit or automatic rebalancing.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task alert-destination-readiness-visibility-v1`
