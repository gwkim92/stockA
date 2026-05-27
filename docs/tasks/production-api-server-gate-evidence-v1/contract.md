# production-api-server-gate-evidence-v1 Contract

## Task Request

- request: Replace the stale static `production_api_server` open gate with evidence-based production FastAPI readiness.
- context: EC2 `/__health`, `/__ready`, and `/__live` report production/live/read-token/psycopg_pool readiness, but `/api/data-health` still reports `production_api_server` as a generic unmet condition.

## Goal

- goal: Keep `production_api_server` open only when production FastAPI runtime evidence is missing; close it when production profile, live source, read-token auth, explicit origin, DB config, and psycopg pool boundary are present.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/production-api-server-gate-evidence-v1/*`
  - `docs/plans/2026-05-27-production-api-server-gate-evidence-v1.md`

## Invariants

- Do not claim auth/RBAC is solved.
- Do not change reverse proxy, TLS, public domain, or systemd unit configuration.
- Do not mutate recommendations, theses, outcomes, benchmark composition, portfolio positions, or orders.
- Do not enable broker submit, automatic order, or automatic rebalancing.

## Scope

- Add `production_api_server` payload to data-health.
- Close the static gate when runtime evidence is complete.
- Keep the gate open for local/fixture/no-auth/no-token/no-explicit-origin/no-DB/no-pool states.
- Show the runtime evidence in `/data-health`.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task production-api-server-gate-evidence-v1`
