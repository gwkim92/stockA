# cycle-screen-entry-clarity-v1 Handoff

## Current Status

- current status: implemented, merged to `develop`, deployed to EC2, and route/browser smoke passed.
- completed: UI entry-point and API contract alignment implementation is complete.
- completed: EC2 deploy and smoke are complete.
- in progress: none.
- branch: `develop`

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
- passed: `PATH=/usr/bin:/bin bash scripts/verify_frontend_api_contract.sh`
- passed: `python3 -m json.tool docs/api/frontend/contract-index.json`
- passed: `python3 -m json.tool docs/api/frontend/examples/cycle-map.json`
- passed: `git diff --check`
- passed: `npm run build` in `apps/web`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-screen-entry-clarity-v1`
- passed: EC2 `bash scripts/verify_frontend_api_contract.sh`
- passed: EC2 `npm run typecheck` in `apps/web`
- passed: EC2 `npm run build` in `apps/web`
- passed: EC2 `stockanalysis-frontend-api.service` active and `stockanalysis-web.service` active
- passed: Playwright snapshot smoke for `http://127.0.0.1:13000/`, `/cycle-map`, and `/cycles`

## EC2 Evidence

- deployed commit: `cce71a22`.
- `/__health`: `status=ok`, `endpoint_count=20`.
- `/__endpoints`: `endpoint_count=20`, includes `/api/cycle-map?asOfDate=2026-06-05`.
- `/api/cycles?asOfDate=2026-06-06`: `cycle_state_count=15`, first theme `AI_LABOR_PRODUCTIVITY`.
- `/api/cycle-map?asOfDate=2026-06-06`: `node_count=17`, `direct_event_count=478`, `propagated_impact_count=1046`, hot node `AI_LABOR_PRODUCTIVITY`.
- `/api/data-health`: cycle runs include `cycle_state_snapshot` latest status `succeeded`, latest run `pipeline-run-3620`, and `cycle_community_ai_summary` latest status `succeeded`, latest run `pipeline-run-3623`.
- EC2 internal Next routes `/`, `/cycles`, `/cycle-map` returned HTTP 200 and contained `사이클` text.
- local tunnel `http://127.0.0.1:13000/cycle-map` returned HTTP 200.

## Boundaries

- No recommendation score weight changed.
- No cycle scoring formula changed.
- No portfolio position, benchmark, scheduler cadence, broker, or order boundary changed.
- This is visibility and API contract alignment only.

## Next Step

- exact next step: continue the next core quality task; cycle visibility is now closed unless a concrete page bug appears.
