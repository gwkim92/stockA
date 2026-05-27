# alert-destination-free-channel-v1 Handoff

## Status

- current status: implemented locally; unit tests, compileall, typecheck, roadmap verify, and AWH verify passed. EC2 deploy/smoke is pending.
- in progress: EC2 deploy/smoke with repo-outside free alert destination is pending.

## Context

- `auth_rbac` is closed on EC2.
- Remaining open operational gate is `alert_destination`.
- The existing data-health policy closes `alert_destination` only when an external destination target is configured and a recent passed test artifact exists.

## Exact Next Step

- exact next step: deploy to EC2, configure a repo-outside free ntfy/webhook target without printing it, run `stockanalysis-operations alert-destination-test-run --execute`, and confirm `alert_destination` leaves `/api/data-health.open_gates`.

## Implemented

- Added `stockanalysis-operations alert-destination-test-run`.
- Supports generic `webhook`, `ntfy`, `discord`, and `slack` compatible destinations.
- Writes a sanitized status artifact with `last_test_status`, `last_tested_at`, `destination_type`, HTTP status class, and no URL/token.
- Added `STOCKANALYSIS_NTFY_TOPIC_URL` as a recognized target env.
- Preserves `read_only_no_order`, `automatic_order_allowed=false`, and `broker_submit_allowed=false`.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_alert_destination_free_channel tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task alert-destination-free-channel-v1`
