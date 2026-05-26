# recommendation-outcome-due-action-router-v1 Handoff

## Status

- completed: local implementation, verification, push, EC2 deployment, and smoke complete.
- started: 2026-05-27
- current state: implemented and EC2-smoked on commit `ba1891b`

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

## EC2 Evidence

- Deployed commit: `ba1891b`.
- EC2 focused verification passed: compileall, 178 focused tests, Next.js build, and project roadmap verification.
- Runner smoke: `recommendation-outcome-due-action-router-run --as-of-date 2026-05-27 --horizon-day 30 --execute`.
- Runner result: `run_id=1654`, `eval_run_id=36`, `action_status=no_op_wait_until_next_due_date`, `route_action=no_op`, `wait_until=2026-06-20`, `child_runner.executed=false`.
- API smoke: `/api/data-health` returns `recommendation_outcome_due_action_router.status=loaded`, `eval_run_id=eval-run-36`, `order_boundary=read_only_no_order`, `broker_submit_allowed=false`.
- Route smoke: `/data-health` returns 200 and renders `성과 실행 라우터`, `다음 측정일까지 대기`, `eval-run-36`, and `주문 경계`.

## Next Step

- exact next step: continue the professional analysis roadmap without changing recommendation weights; likely next work is to let the 2026-06-20 outcome window mature, then rerun this router/calibration and only afterwards reassess manual weight review readiness.
