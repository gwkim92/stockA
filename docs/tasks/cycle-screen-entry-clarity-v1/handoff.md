# cycle-screen-entry-clarity-v1 Handoff

## Current Status

- current status: local implementation complete, EC2 deploy pending.
- completed: UI entry-point and API contract alignment implementation is complete locally.
- in progress: commit, develop merge, push, EC2 deploy, and route smoke remain.
- branch: `codex/cycle-screen-entry-clarity-v1`

## What Changed

- Added top-level `사이클` navigation entry pointing to `/cycle-map`.
- Added clearer home entry points:
  - `/cycle-map`: 사이클 지도, 상위 흐름 전파 경로
  - `/cycles`: 사이클 상태표, 테마별 상태 변화
- Clarified `/cycle-map` hero copy so users know `/cycles` and `/cycle-map` are different screens.
- Registered `/api/cycle-map?asOfDate=2026-06-05` in the frontend API contract index.
- Added `docs/api/frontend/examples/cycle-map.json`.
- Added fixture alias for current-date `/api/cycle-map?asOfDate=...`.
- Updated frontend API adapter, fixture server tests, and contract verifier for 20 read endpoints.

## Runtime Evidence Before Change

- EC2 FastAPI health: `/__health` returned ok.
- EC2 `/api/cycles?asOfDate=2026-06-06` returned 15 cycle states.
- EC2 `/api/cycle-map?asOfDate=2026-06-06` returned 17 nodes, 478 direct event impacts, 1046 propagated impacts, 166 recommendation links.
- EC2 `/api/data-health` showed:
  - `cycle_state_snapshot` latest status `succeeded`, latest run `pipeline-run-3620`
  - `cycle_community_ai_summary` latest status `succeeded`, latest run `pipeline-run-3623`
- EC2 Next.js service is active on `127.0.0.1:3000`; `127.0.0.1:3001` is not the active service port.

## Verification

- passed: `npm run typecheck` in `apps/web`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_api_adapter tests.test_frontend_fixture_server`
- passed: `bash scripts/verify_frontend_api_contract.sh`
- passed: `python3 -m json.tool docs/api/frontend/contract-index.json`
- passed: `python3 -m json.tool docs/api/frontend/examples/cycle-map.json`
- passed: `git diff --check`
- passed: `npm run build` in `apps/web`

## Boundaries

- No recommendation score weight changed.
- No cycle scoring formula changed.
- No portfolio position, benchmark, scheduler cadence, broker, or order boundary changed.
- This is visibility and API contract alignment only.

## Next Step

- exact next step: run AWH verification again, then commit, merge to `develop`, push, deploy EC2 by pulling `develop`, rebuild/restart Next.js, restart FastAPI if contract endpoint metadata needs refresh, and smoke `/`, `/cycles`, `/cycle-map`, `/api/cycles?asOfDate=2026-06-06`, `/api/cycle-map?asOfDate=2026-06-06`, `/__endpoints`.
