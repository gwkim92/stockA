# ec2-access-stability-v1 Handoff

## 2026-07-04

Implemented `scripts/verify_ec2_access_stability.sh` to replace repeated manual EC2 health checks with a single secret-free verification command.

The script checks:

- SSH access to `ec2-user@3.211.40.142`.
- EC2 app branch and commit.
- `stockanalysis-web.service` and `stockanalysis-frontend-api.service`.
- FastAPI `/__ready`.
- authenticated `/api/data-health`.
- `data_operations_artifact_runner`, `live_ai_invocation_health`, `auth_rbac`, `broker_submit_allowed`, and `order_boundary`.
- optional local web tunnel at `http://127.0.0.1:13000/` when `STOCKANALYSIS_REQUIRE_LOCAL_TUNNEL=1`.

## Evidence

- passed: `bash -n scripts/verify_ec2_access_stability.sh`
- passed: `STOCKANALYSIS_REQUIRE_LOCAL_TUNNEL=1 bash scripts/verify_ec2_access_stability.sh`
  - EC2 branch `develop`
  - EC2 commit `6ea6766b`
  - web service `active`
  - frontend API service `active`
  - FastAPI readiness `ok`
  - source mode `live`
  - auth mode `read-token`
  - order boundary `read_only_no_order`
  - data-health overall `attention_required`
  - open gates: `benchmark_drift_quality_attention`, `portfolio_review_decision_history_attention`, `portfolio_review_decision_feedback_attention`, `portfolio_review_feedback_calibration_attention`
  - `data_operations_artifact_runner.status=runner_evidence_available`
  - local tunnel returned HTML from `http://127.0.0.1:13000/`

## Boundaries

- No AWS write action.
- No recommendation weight change.
- No benchmark, portfolio position, DB schema, or broker submit change.
