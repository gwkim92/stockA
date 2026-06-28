# data-health-open-gate-triage-v1 Handoff

## Current Status

- completed: backend open gate recomputation, explicit due gate details, frontend due-now triage bucket, focused tests, local verification, AWH readiness, and browser visual QA are implemented.
- status: ready to commit on `feature/data-health-open-gate-triage-v1`.
- current status: implementation and local verification are complete; merge to `develop` and EC2 deployment are the next operational steps.

## What Changed

- `src/stockanalysis/frontend/live_adapter.py`
  - Added `_set_data_health_open_gate()` so computed gates are explicitly opened or closed on every `/api/data-health` response.
  - Fixed stale gates that previously stayed open when they were present in state but their current condition had resolved.
  - Added specific `open_gate_details` mappings for portfolio feedback, feedback cadence, feedback action router, recommendation outcome calibration, and recommendation outcome due action router.
  - Reclassified overdue recommendation outcome maturity as `outcome_due` instead of managed wait when cadence action says work should run now.

- `apps/web/src/app/data-health/_components/dataHealthGateModel.ts`
  - Added a distinct `due-now` triage bucket for due outcome/feedback work.
  - Kept `outcome_wait` separate as managed waiting.

- `apps/web/src/app/data-health/page.tsx`
  - Updated the command card copy to show `성과 실행` when due work exists.

- Tests
  - Added backend regression tests for stale computed gates and generic fallback detail prevention.
  - Added frontend triage tests for `outcome_due` vs `outcome_wait`.

## Verification

- Red phase confirmed the bug:
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_removes_stale_resolved_open_gates tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_labels_due_open_gates_without_generic_fallback -v` failed before the fix because stale computed gates remained open and due gates fell back to `조건 미충족`.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v` passed: 105 tests.
- `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- `cd apps/web && npm run typecheck` passed.
- `cd apps/web && npm test` passed: 19 files, 44 tests.
- `cd apps/web && npm run build` passed.
- `bash scripts/verify_project_execution_roadmap.sh` passed.
- `bash scripts/verify_frontend_api_contract.sh` passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-open-gate-triage-v1` passed.
- `git diff --check` passed.

## Browser QA

- Verified `http://127.0.0.1:13003/data-health` with Playwright at 375px, 768px, and 1280px.
- Screenshots were captured outside the commit scope:
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-375.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-768.png`
  - `/Users/woody/ai/stockanalysis/output/playwright/data-health-1280.png`
- DOM QA result: all three viewport widths rendered `자동화와 원천 제한 4개 관리 중`, command card, and open item sections without horizontal overflow.
- Fixture data does not contain an `outcome_due` gate, so `성과 실행` copy is unit-tested rather than visible in the local fixture screenshot.

## Remaining Notes

- This task does not fix real current EC2 blockers such as stale alert test, artifact runner failures, or OpenAI quota failures. It makes them easier to distinguish from due/wait/source-limited states.
- EC2 deployment and live `/data-health` route smoke still need to be run after merge to `develop`.

## Exact Next Step

- exact next step: commit the feature branch, merge to `develop`, push, and deploy to EC2 with `git pull --ff-only origin develop`.
