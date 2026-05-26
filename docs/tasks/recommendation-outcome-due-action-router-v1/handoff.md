# recommendation-outcome-due-action-router-v1 Handoff

## Status

- completed: local implementation and verification complete.
- started: 2026-05-27
- current state: local implementation and verification complete; EC2 deployment/smoke pending

## Intent

Move recommendation outcome due handling from a UI-only cadence suggestion into a backend action router. The router should run calibration only when outcome windows are due/ready and should otherwise persist a no-op or blocked audit artifact.

## Guardrails

- No recommendation weight changes.
- No broker submit.
- No portfolio mutation.
- No benchmark mutation.
- Child execution is limited to the existing `recommendation_outcome_calibration_sample_expansion` runner.

## Implemented

- Added `src/stockanalysis/operations/recommendation_outcome_due_action_router.py`.
- Added CLI command `stockanalysis-operations recommendation-outcome-due-action-router-run`.
- Added cadence job `recommendation-outcome-due-action-router-daily`.
- Added decision/full-recovery orchestrator step after `recommendation-outcome-backfill` and before `recommendation-quality-eval`.
- Exposed latest router artifact through `/api/data-health` payload and `/data-health` Korean UI cards.
- Added tests for router decisioning, execution, CLI wiring, cadence registry, orchestrator order, live adapter payload, and frontend type/build coverage.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_outcome_due_action_router`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` with 1095 tests.
- Expected failure on non-venv Homebrew Python: full unittest cannot import `fastapi`; use the project verify venv for full suite.

## Next Step

- exact next step: commit/push, deploy to EC2, run the new CLI smoke, restart services, and verify `/api/data-health` plus `/data-health` render `성과 실행 라우터`.
