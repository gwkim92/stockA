# portfolio-review-feedback-calibration-v1 Review

## Review Summary

- `portfolio-review-feedback-calibration-v1` adds a read-only calibration layer over accumulated portfolio review feedback artifacts.
- It does not mutate recommendation weights, benchmark composition, portfolio positions, rebalance candidates, broker state, or order flow.
- Sparse feedback is treated as `insufficient_history`, which blocks future weight-pilot consideration until more outcome-backed feedback exists.

## Issues Found

- No correctness issues found in focused local review.
- Important constraint remains: `manual_review_ready` is only an audit status and must not be interpreted as permission to auto-change weights.

## Residual Risks

- EC2 currently has only one recent `portfolio_review_decision_outcome_feedback` artifact, so the first live result is correctly `insufficient_history`.
- Calibration quality depends on enough later outcome, thesis, paper validation, and price evidence being accumulated over time.
- This task does not solve the cadence problem by itself; the next task should keep feedback/calibration refreshed when outcome windows mature.

## Verification Evidence

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_feedback_calibration tests.test_data_operations_cli tests.test_frontend_live_adapter`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` passed: 1066 tests.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-review-feedback-calibration-v1`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-review-feedback-cadence-v1`
- EC2 focused tests: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_portfolio_review_feedback_calibration tests.test_data_operations_cli tests.test_frontend_live_adapter` passed: 161 tests.
- EC2 Next build: `cd /opt/stockanalysis/app/apps/web && npm run build`
- EC2 roadmap verify: `bash scripts/verify_project_execution_roadmap.sh`
- EC2 runner: `portfolio-review-feedback-calibration-run --execute` completed with `run_id=1636`, `eval_run_id=33`, `calibration_status=insufficient_history`, `feedback_run_count=1`, `decision_count=11`, `too_early_count=11`.
- EC2 API smoke: `/api/data-health` and `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25` expose `portfolio_review_feedback_calibration` / `risk_budget.review_feedback_calibration` with `eval_run_id=eval-run-33`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- Route smoke: local tunnel and EC2 web returned `200` for `/`, `/data-health`, and `/portfolio/coverage`.
