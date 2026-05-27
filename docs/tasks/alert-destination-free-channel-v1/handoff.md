# alert-destination-free-channel-v1 Handoff

## Status

- current status: implemented, committed, pushed, deployed to EC2, and smoke verified.
- completed: local implementation, unit tests, compileall, typecheck, roadmap verify, AWH verify, GitHub push, EC2 deploy, repo-outside ntfy destination setup, execute smoke, service restart, API smoke, and web route smoke.

## Context

- `auth_rbac` is closed on EC2.
- Remaining open operational gate is `alert_destination`.
- The existing data-health policy closes `alert_destination` only when an external destination target is configured and a recent passed test artifact exists.

## Exact Next Step

- exact next step: continue with `internal-rag-retrieval-foundation-v1`; keep the remaining `portfolio_review_feedback_calibration_attention` gate open until outcome maturity.

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

## EC2 Verification

- deployed commit: `56dff0d`.
- alert env updated outside the repo: `/opt/stockanalysis/runtime/frontend-api.env`.
- status artifact written outside the repo: `/opt/stockanalysis/artifacts/alert-destination/status.json`.
- `stockanalysis-operations alert-destination-test-run --execute` wrote a passed status artifact.
- `stockanalysis-frontend-api.service`: active.
- `stockanalysis-web.service`: active.
- `/api/data-health.alert_destination`: `status=external_destination_verified`, `attention_required=false`, `mode=ntfy`, `destination_type=ntfy`, `target_configured=true`, `last_test_status=passed`, `test_recent=true`.
- `/api/data-health.open_gates`: `['portfolio_review_feedback_calibration_attention']`.
- secret check: data-health alert payload did not contain `ntfy.sh` or `STOCKANALYSIS_NTFY_TOPIC_URL`.
- `/data-health`: HTTP 200 and renders `외부 알림 검증됨` and `ntfy`.
