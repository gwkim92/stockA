# segment-sotp-driver-calibration-v1 Handoff

## Status

- completed: contract, plan, implementation, focused tests, regression tests, frontend typecheck, compileall, full Python 3.13 suite, EC2 deploy/write smoke, API smoke, route smoke, review, and roadmap update are complete.

## Current Findings

- Existing segment assumptions are visible and evidence-only but are single-period proxies.
- `research.segment_footnote_evidence` can carry multiple `period_end` rows, so trend calibration can be computed without schema changes.

## Decisions

- Keep calibration deterministic and transparent.
- Use JSON evidence fields rather than a migration in this slice.
- Do not change SOTP totals, recommendation weights, benchmark logic, portfolio guardrails, or order boundaries.

## Exact Next Step

- exact next step: start `segment-history-backfill-v1` to backfill historical reported segment periods from prior SEC filings so segment assumption calibration becomes trend-backed instead of single-period proxy-backed where possible.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter` (`Ran 93 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_frontend_live_adapter tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 181 tests`, `OK`)
- Passed: `cd apps/web && npm run typecheck`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 971 tests`, `OK`)
- Passed on EC2 commit `c4dfbb8`: `sum-of-parts-valuation-run --execute` produced `run_id=1069`, `component_row_count=45`, `balance_sheet_adjustment=12`, `operating_business=16`, `risk_reserve=17`, and `recommendation_scoring_mutated=false`.
- Passed on EC2 commit `c4dfbb8`: `valuation-snapshot-run --execute` produced `run_id=1070`, `snapshot_count=68`, method counts `dcf_lite=16`, `relative_multiple=18`, `scenario_range=18`, `sum_of_parts=16`, and `recommendation_scoring_mutated=false`.
- Passed on EC2 commit `c4dfbb8`: `/api/stocks/AAPL` exposes 5 `reported_segment_assumptions`; first assumption is `Americas`, `driver_template_label=지역 수요·환율·채널 믹스`, `calibration_method=single_period_margin_share_template_proxy`, `history_period_count=1`, `first_period_end=2025-09-27`, `latest_period_end=2025-09-27`, `observed_revenue_cagr=null`, `observed_margin_change=null`, `base_growth_rate=0.06`, `base_multiple=20.0`, `score_policy=recommendation_weights_unchanged`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order`.
- Passed on EC2 commit `c4dfbb8`: `/stocks/AAPL` renders `사업부별 가정`, `동인 지역 수요`, `단일 기간 proxy`, and `Americas`.
- Passed on EC2 commit `c4dfbb8`: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active after deploy.

## Remaining Risks

- If only one reported segment period exists on EC2, the system will correctly label assumptions as `single_period_margin_share_template_proxy` until more period evidence is ingested.
- AAPL currently has one reported segment period on EC2, so trend fields are null and the visible calibration method remains proxy-backed until `segment-history-backfill-v1` adds additional periods.
