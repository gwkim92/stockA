# portfolio-feedback-calibration-maturity-visibility-v1 Handoff

## Status

- current status: local implementation verified; EC2 deployment/smoke pending.
- in progress: local API/UI/test implementation is verified, and EC2 deployment/smoke remains.
- in progress locally: API payload, frontend copy, and focused tests are implemented.
- EC2 deploy/smoke: not done yet.

## Context

- The remaining investment-process data-health gate is `portfolio_review_feedback_calibration_attention`.
- It should remain open because portfolio review outcomes have not matured enough to justify recommendation weight changes.
- The prior UI showed feedback counts, but not the actual maturity timing or why weight review is blocked.

## Implemented Locally

- Added feedback maturity visibility to `portfolio_review_feedback_calibration`:
  - `maturity_status`
  - `feedback_run_gap`
  - `mature_decision_gap`
  - `estimated_maturity_date`
  - `days_until_maturity`
  - `attention_required`
  - `weight_review_blocked`
  - `weight_review_block_reason`
  - `next_calibration_action`
- Added fallback maturity-date calculation when cadence `wait_until` is blank.
- Reused the same maturity visibility in portfolio coverage risk-budget payload.
- Updated `/data-health` to show weight block status, sample gaps, and expected maturity date in Korean.

## Local Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` (`75 tests`).
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.

## Exact Next Step

- exact next step: deploy/pull to EC2, restart FastAPI/Next.js, and smoke `/api/data-health` plus `/data-health` for the new maturity visibility fields.
- Run roadmap verify and AWH verify for this task.
- If local verification stays clean, deploy/pull to EC2, restart FastAPI/Next.js, and smoke `/api/data-health` plus `/data-health`.

## Guardrails

- Recommendation weights remain unchanged.
- Benchmark composition remains unchanged.
- Portfolio positions remain unchanged.
- Broker submit and automatic orders remain blocked.
