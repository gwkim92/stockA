# portfolio-feedback-calibration-maturity-visibility-v1 Handoff

## Status

- current status: completed.
- completed: local implementation, GitHub push, EC2 deploy, service restart, API smoke, route smoke, and verification are complete.
- in progress locally: API payload, frontend copy, and focused tests are implemented.
- EC2 deploy/smoke: completed on commits `2910de0` and `e1bfbef`.

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
- Updated `/portfolio/coverage` to show the same weight block status, sample gaps, expected maturity date, and block reason.

## Local Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` (`75 tests`).
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- Passed: `cd apps/web && npm run build`.

## EC2 Evidence

- EC2 commits: `2910de0` and `e1bfbef`.
- EC2 services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- EC2 focused tests: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter` passed (`75 tests`).
- EC2 compile: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests` passed.
- EC2 frontend: `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build` passed.
- EC2 roadmap verify: `bash scripts/verify_project_execution_roadmap.sh` passed.
- EC2 AWH: not available because `/opt/stockanalysis/venv/bin/python` has no `awh` module; local AWH passed.
- `/api/data-health`: `portfolio_review_feedback_calibration.maturity_status=waiting_for_outcome_window`, `estimated_maturity_date=2026-06-24`, `days_until_maturity=28`, `feedback_run_gap=2`, `mature_decision_gap=10`, `attention_required=true`, `weight_review_blocked=true`, and gate summary includes `예상 성숙일 2026-06-24(D-28)`.
- `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25`: `risk_budget.review_feedback_calibration` exposes the same maturity fields.
- Route smoke returned `200` for `/data-health` and rendered `성과 표본이 성숙하기 전에는 추천 weight를 바꾸지 않는다`, `2026-06-24`, `왜 막혀 있나`, and `weight 변경 금지`.
- Route smoke returned `200` for `/portfolio/coverage` and rendered `성과 표본이 성숙하기 전에는 weight를 바꾸지 않는다`, `2026-06-24`, `차단 이유`, and `weight 변경 금지`.

## Exact Next Step

- exact next step: continue reducing the remaining operational open gates; the investment feedback gate should stay open until the `2026-06-24` outcome window matures and feedback/calibration can be rerun.

## Guardrails

- Recommendation weights remain unchanged.
- Benchmark composition remains unchanged.
- Portfolio positions remain unchanged.
- Broker submit and automatic orders remain blocked.
