# segment-history-backfill-v1 Review

## Review Summary

- Accepted. The task now backfills historical reported segment periods through backend CLI/service boundaries, extends Apple segment evidence from a single period to four annual periods, and converts SOTP segment assumptions from single-period proxy calibration to trend-backed calibration without changing recommendation weights or order flow.

## Issues Found

- Found during EC2 smoke: the first multi-year parser expansion also captured non-segment labels (`Net sales`, `Deferred tax assets`) as reported segments.
- Fixed in commit `a2ad9df`: multi-year block parsing now requires an operating-income row and explicitly rejects total/sales/tax labels as segment labels.
- Verified on EC2 rerun: `removed_stale_metric_count=7` and DB bad segment count is `0`.

## Residual Risks

- Evidence is strongest for Apple-style annual 10-K segment tables. Other issuers may use product, geography, consolidated note, or image/XBRL-only layouts that need additional parser adapters.
- SEC raw fetch availability and rate limiting remain external dependencies.
- Trend-backed calibration is still read-only evidence. Recommendation scoring weights and live broker submit remain unchanged.

## Verification Evidence

- Local: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_segment_history_backfill tests.test_data_operations_cli tests.test_operating_data_orchestrator` ran `119` tests with `OK`.
- Local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- EC2 deploy: `/opt/stockanalysis/app` fast-forwarded to `a2ad9df`; FastAPI and Next services remained `active`.
- EC2 runner: `segment-history-backfill-run --execute` completed with parent `run_id=1086`, parser `run_id=1090`, SOTP `run_id=1091`, valuation `run_id=1092`.
- EC2 DB/API: AAPL has 4 annual reported segment periods, 5 clean segment labels per period, bad segment count `0`, and authenticated `/api/stocks/AAPL` exposes 5 SOTP segment inputs/assumptions with `multi_period_segment_trend_template` and `history_period_count=4`.
