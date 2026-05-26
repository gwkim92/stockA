# segment-history-backfill-v1 Handoff

## Status

- completed: contract, plan, parser history mode, multi-year segment block parser coverage, non-segment table filter, CLI, weekly profile changes, segment history backfill runner, focused tests, CLI help check, compileall, roadmap/AWH verification, commit, EC2 deploy, and EC2 smoke are complete.

## Current Findings

- `reported-segment-footnote-parser-run` currently selects one period per instrument by default, so historical raw SEC filings are not parsed even when source linkage can find them.
- `segment-sotp-driver-calibration-v1` already has the downstream trend CTEs. The missing piece is historical reported segment rows in `research.segment_footnote_evidence`.

## Decisions

- Add bounded history parsing rather than unbounded full archive parsing.
- Keep all writes inside existing backend CLI/service boundaries.
- Keep recommendation weights, SOTP formulas, benchmark logic, portfolio guardrails, and broker/order flow unchanged.

## Exact Next Step

- exact next step: start `segment-history-coverage-expansion-v1` to expand trend-backed segment history beyond AAPL and report unsupported issuer/table layouts instead of silently falling back to single-period proxies.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_segment_history_backfill tests.test_data_operations_cli tests.test_operating_data_orchestrator` (`Ran 119 tests`, `OK`).
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "segment-history-backfill-run|reported-segment-footnote-parser-run"`.
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`.
- Passed on EC2 commit `a2ad9df`: `segment-history-backfill-run --execute` completed with parent `run_id=1086`, parser `run_id=1090`, SOTP `run_id=1091`, valuation `run_id=1092`.
- EC2 parser evidence: `candidate_count=4`, `periods_per_instrument=4`, `reported_segment_metric_count=40`, `removed_stale_metric_count=7`, `metric_code_counts.segment_revenue=20`, `metric_code_counts.segment_operating_income=20`.
- EC2 DB evidence for AAPL: reported segment rows now cover `2025-09-27`, `2024-09-28`, `2023-09-30`, and `2022-09-24`; each period has 5 segment labels: `Americas`, `Europe`, `Greater China`, `Japan`, `Rest of Asia Pacific`.
- EC2 contamination check: `reported_net_sales` and `reported_deferred_tax_assets` count is `0` after rerun.
- EC2 API evidence: authenticated `/api/stocks/AAPL` exposes SOTP `sum_of_parts` method with 5 `reported_segment_inputs`, 5 `reported_segment_assumptions`, first assumption `Americas`, `calibration_method=multi_period_segment_trend_template`, `history_period_count=4`, `observed_revenue_cagr=0.01674948697333`, `observed_margin_change=0.03691828054287135`.

## Remaining Risks

- Older SEC filings and non-Apple issuers may use different segment table layouts; parser coverage may still block some historical periods.
- SEC raw fetch depends on `STOCKANALYSIS_SEC_USER_AGENT` and SEC availability.
- Current EC2 proof is AAPL-focused. The next task must expand coverage to active recommendation/portfolio symbols and report single-period fallback cases explicitly.
