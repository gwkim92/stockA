# portfolio-review-feedback-cadence-v1 Handoff

## Status

- completed: backend cadence runner, CLI, data-health API payload, portfolio coverage payload, and frontend visibility are wired locally.
- EC2 deploy/smoke: completed on commit `77ffb0c`.

## Context

- Portfolio review decision history, single-run outcome feedback, and accumulated calibration now exist as read-only audit artifacts.
- The cadence policy now tells operators and scheduler profiles when feedback and calibration should be rerun.
- The cadence policy must not change recommendation weights, portfolio positions, benchmark composition, or orders.

## Exact Next Step

- exact next step: start `portfolio-review-feedback-action-router-v1` so the persisted cadence artifact can safely route the next feedback/calibration runner without ad-hoc manual follow-up.

## Local Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_feedback_cadence tests.test_data_operations_cli tests.test_frontend_live_adapter tests.test_data_operations_cadence tests.test_operating_data_orchestrator`: 174 tests passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: 1075 tests passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `bash scripts/verify_project_execution_roadmap.sh`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-review-feedback-cadence-v1`: passed.

## EC2 Evidence

- EC2 commit: `77ffb0c`.
- Services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- EC2 focused tests: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_portfolio_review_feedback_cadence tests.test_data_operations_cli tests.test_frontend_live_adapter tests.test_data_operations_cadence tests.test_operating_data_orchestrator`: 174 tests passed.
- EC2 Next build: `npm --prefix apps/web run build` passed.
- EC2 roadmap verify: `bash scripts/verify_project_execution_roadmap.sh` passed.
- Runner: `stockanalysis-operations portfolio-review-feedback-cadence-run --portfolio-name "Long Term Paper" --as-of-date 2026-05-27 --execute` completed with `run_id=1637`, `eval_run_id=34`.
- Runner output: `cadence_status=wait_for_outcome_window`, `history_age_days=2`, `decision_count=11`, `recommendation_link_count=6`, `recommendation_outcome_count=0`, `price_evidence_count=10`, `should_run_now=false`, `automatic_weight_change_allowed=false`, `automatic_rebalance_allowed=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- `/api/data-health`: `portfolio_review_feedback_cadence.status=loaded`, `eval_run_id=eval-run-34`, `cadence_status=wait_for_outcome_window`, `should_run_now=false`, `broker_submit_allowed=false`.
- `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25`: `risk_budget.review_feedback_cadence.status=loaded`, `eval_run_id=eval-run-34`, `cadence_status=wait_for_outcome_window`, `should_run_now=false`, `broker_submit_allowed=false`.
- Route smoke returned `200` for `/`, `/data-health`, and `/portfolio/coverage`.

## Implemented

- Added `stockanalysis.operations.portfolio_review_feedback_cadence`.
- Added CLI command `portfolio-review-feedback-cadence-run`.
- Added daily cadence registry entry `portfolio-review-feedback-cadence-daily`.
- Added decision-daily/full-recovery orchestrator step `portfolio-review-feedback-cadence`.
- Added live API payloads:
  - `/api/data-health` → `portfolio_review_feedback_cadence`.
  - `/api/portfolio/{portfolio}/coverage` → `risk_budget.review_feedback_cadence`.
- Added frontend copy on `/data-health` and `/portfolio/coverage` that explains whether to wait, run feedback, run calibration, or inspect missing evidence.

## Cadence Statuses

- `missing_evidence_review_required`: latest history is missing or mature feedback has no usable outcome/price/paper evidence.
- `wait_for_outcome_window`: saved review decisions are too recent to judge.
- `run_feedback_now`: outcome window is mature and latest feedback is missing or stale.
- `run_calibration_now`: feedback exists but accumulated calibration is missing or stale.
- `calibration_current`: feedback and calibration are current.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat insufficient evidence as a blocker, not as readiness.
