# TossInvest Market Data Agent Context V1 Handoff

## Status

- completed: TossInvest market data snapshots, provider comparison, AI agent Postgres context, paper/live API separation, data-health visibility, and stock-detail candlestick UI are implemented and deployed from `develop`.
- completed: Task-specific backend, CLI, scheduler, frontend adapter, migration, contract, typecheck, and build verification passed.
- completed: EC2 `stockanalysis-mvp-20260520` is on `develop` commit `4c750df3`; FastAPI and Next.js services are active.
- completed: Local `127.0.0.1:13000` is an SSH tunnel to EC2 `127.0.0.1:3000`; `/stocks/AAPL` returns 200 and renders candlestick/Toss/read-only boundary text.
- completed: Live TossInvest AAPL daily candle sync succeeded on EC2 (`run_id=7071`) and wrote 30 US shadow candle rows plus 1 US market calendar row.
- completed: TossInvest provider comparison for AAPL succeeded on EC2 (`run_id=7072`) and wrote 1 comparison row with status `shadow_collecting`.
- completed: Toss real account read-only sync succeeded earlier on EC2 (`run_id=7055`) and populated `Toss Real Readonly` KRW portfolio positions for AAPL/NVDA/TSLA plus FX evidence.
- in progress: Full repository `unittest discover` is still blocked by local Python environment issues unrelated to this task.

## Current Decisions

- `market.daily_price_bar` remains canonical and now carries provider provenance.
- Toss KR candles can populate canonical daily bars; Toss US candles remain shadow provider evidence until a future promotion gate.
- AI agents read `stockanalysis.ai.market_context` Postgres read models only; they do not call TossInvest HTTP.
- Recommendation/scoring context excludes Toss live account data by default.
- `/api/paper-trading/preview` represents simulated paper validation for `Long Term Paper`.
- `/api/trading/readiness` represents Toss live account read-only state and disabled submit adapter status.
- Toss order submit, modify, cancel, and mutation paths remain disabled.

## Verification Already Run

- `bash scripts/verify_tossinvest_market_data_agent_context.sh` passed.
- `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_market_data` passed after adding live Toss market-calendar object-date coverage.
- EC2 `PYTHON_BIN=/opt/stockanalysis/venv/bin/python bash scripts/verify_tossinvest_market_data_agent_context.sh` passed on commit `4c750df3`.
- EC2 live smoke:
  - `tossinvest-market-data-sync-run --symbol AAPL --market-code US --sync-mode daily_candles --outputsize 30 --execute` succeeded with `candle_bar_count=30`, `calendar_market_count=1`, `broker_submit_allowed=false`.
  - `tossinvest-provider-comparison-run --symbol AAPL --lookback-days 30 --execute` succeeded with `comparison_count=1`, `written_count=1`, `shadow_collecting_count=1`.
  - `/api/stocks/AAPL` returned `toss_provider_evidence.status=available`, `latest_trade_date=2026-06-23`, `comparison.status=shadow_collecting`, `matched_bar_count=19`, `missing_canonical_count=1`, and `order_boundary=read_only_no_order`.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter` passed.
- `bash scripts/verify_frontend_api_contract.sh` passed.
- `cd apps/web && npm run typecheck` passed after `npm ci`.
- `cd apps/web && npm run build` passed.
- Temporary fixture API plus built Next server route smoke passed for `/stocks/AAPL` and `/data-health`.
- `bash scripts/verify_migrations.sh` passed and applied migrations through `0034_tossinvest_market_data_agent_context.sql`.
- `PYTHONPATH=src python3 -m unittest` ran 0 tests and exited 5 because this repo requires explicit discovery.
- `PYTHONPATH=src python3 -m unittest discover -s tests` ran 1247 tests and failed due local environment issues:
  - Python 3.14 `pyexpat` dylib mismatch breaks XML parsing tests for XLSX/RSS.
  - `fastapi` is not installed for `tests/test_frontend_api_server.py`.
  - News RSS runner failures are downstream of the XML parser failure.

## Residual Risk

- Live Toss smoke has run for AAPL only. Full tracked-symbol daily collection has not yet been executed in this session.
- Toss stock warnings, orderbook/recent trades, and price limits tables remain empty because the executed live smoke used `sync_mode=daily_candles`; run reference/microdata profiles for those datasets.
- AAPL provider comparison is intentionally `shadow_collecting`, not `candidate_ready`, because canonical prices are missing one Toss date; no canonical provider promotion is allowed.
- KR schedules are represented as operating profiles and cadence metadata; actual systemd timezone deployment should be checked on EC2 before activation.
- `npm ci` reported existing npm audit findings: 1 moderate and 1 high vulnerability. Dependency remediation is outside this task.

## Exact Next Step

- exact next step: Run `tossinvest-market-data-sync-run` for the selected tracked-symbol universe, then run `tossinvest-provider-comparison-run` for the same symbol set and review `shadow_collecting`/conflict rows before any provider promotion.
