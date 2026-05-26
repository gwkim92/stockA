# portfolio-attribution-monthly-profile-integration-v1 Review

## Review Notes

- Completed. The missing monthly attribution gate was a real orchestration gap: the cadence registry expected `portfolio-attribution-monthly`, but the `performance-monthly` profile never executed it.
- The fix uses the backend operations CLI/service boundary rather than adding shell orchestration.
- The runner is read-only with respect to recommendations, theses, positions, portfolio allocation, broker submit, and scoring weights. It writes only performance attribution artifacts and `ops.pipeline_run` state.
- No schema, benchmark definition, recommendation scoring, or broker/order boundary was changed.

## Verification

- Passed locally: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_operations_portfolio_attribution tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_data_operations_cli tests.test_portfolio_attribution_bootstrap` (`114 tests`).
- Passed locally: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- Passed locally: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli portfolio-attribution-run --help`.
- Passed locally: `operating-data-run --profile performance-monthly --execute=false` reported `["performance-outcome-monthly", "portfolio-attribution-monthly"]`.
- Passed locally: `cd apps/web && npm run typecheck && npm run build`.
- Passed locally: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` (`1103 tests`).
- Passed locally: `bash scripts/verify_project_execution_roadmap.sh`.
- Passed locally: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-attribution-monthly-profile-integration-v1`.
- Passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`.
- Passed on EC2: focused unittest set for portfolio attribution, cadence, orchestrator, CLI, and attribution bootstrap (`114 tests`).
- Passed on EC2: direct `portfolio-attribution-run --execute` returned `status=completed`, `run_id=1704`, `attribution_run_id=1`, `symbol_preview=["NVDA"]`, `broker_submit_allowed=false`, `automatic_order_allowed=false`.
- Passed on EC2: `operating-data-run --profile performance-monthly --execute` returned `run_status=completed`, `failed_step_count=0`, and ran both monthly performance steps.
- Passed on EC2: `/api/data-health` reports `portfolio-attribution-monthly` with `latest_status=succeeded`, `health_status=ok`, `latest_run_id=pipeline-run-1706`.

## Remaining

- `overall_status` remains `attention_required` because unrelated gates remain open: `production_api_server`, `auth_rbac`, `alert_destination`, `data_operations_artifact_runner`, `benchmark_drift_quality_attention`, `portfolio_review_decision_history_attention`, `portfolio_review_feedback_calibration_attention`, and `professional_source_gap_attention`.
- Recommendation weight changes and live broker submit remain intentionally blocked.
- Attribution coverage is only as broad as current eligible paper snapshots and thesis outcome windows. More outcome history is still needed before any recommendation component weight review can be trusted.
