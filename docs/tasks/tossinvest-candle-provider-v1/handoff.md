# TossInvest Candle Provider V1 Handoff

## Status

- completed locally: TossInvest read-only candle provider support is implemented and verified.

## Current Decisions

- TossInvest is not fully applied across the service yet.
- The next incremental capability is read-only candle/OHLCV import into the existing market price model.
- Existing providers remain fallback until Toss candle rate-limit stability is proven in EC2.
- Real Toss order submit/modify/cancel remains out of scope.
- Batch market price runs reuse one Toss OAuth token per process run and then call the candle endpoint per symbol.
- EC2 live dry-run confirmed Toss IP allowlist is now accepted; the first live execute attempt surfaced and fixed a readonly sync SQL alias bug in `resolved_issuer`.
- EC2 readonly execute succeeded after the fix with `run_id=7041`, `position_count=3`, `fx_rate_snapshot_id=1`, `broker_submit_allowed=false`, and `submitted_to_broker=false`.
- EC2 live candle smoke normalized `AAPL` Toss daily candles with `bar_count=5`, oldest `2026-06-16`, latest `2026-06-23`, and `price_adjustment_mode=adjusted_provider`.

## Guardrails

- Do not log Toss client secret, access token, account sequence/account number, or Authorization headers.
- Do not call Toss order mutation endpoints.
- Do not change recommendation weights, benchmark definitions, portfolio holdings, or broker order boundary.

## Verification Notes

- passed: `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_source tests.test_market_price`
- passed: `bash scripts/verify_tossinvest_candle_provider.sh`
- passed with repo venv: `PYTHONPATH=src /tmp/stockanalysis-tossinvest-venv/bin/python -m unittest discover -s tests`
- passed: `bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- passed on EC2 after deploy: `PYTHON_BIN=/opt/stockanalysis/venv/bin/python bash scripts/verify_tossinvest_candle_provider.sh`
- passed on EC2 after deploy: `PYTHON_BIN=/opt/stockanalysis/venv/bin/python bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- passed on EC2: `/api/data-health` exposes `tossinvest_readonly_sync.status=succeeded`, `latest_run_id=pipeline-run-7041`, and secret-free metadata.
- passed on EC2: `/api/trading/readiness` exposes `tossinvest_order_readiness.status=succeeded` and `submit_adapter_status=disabled_stub`.
- local `/opt/homebrew/bin/python3.13 -m unittest discover -s tests` without the repo venv failed because `fastapi` is not installed in that interpreter.
- local `python3` points to a Python 3.14 build with a broken `pyexpat` dynamic library; use `/tmp/stockanalysis-tossinvest-venv/bin/python` or `/opt/homebrew/bin/python3.13` for reliable repo verification.

## Residual Risk

- Production market price scheduler has not been switched to Toss; that should wait until EC2 live Toss candle calls pass and rate-limit headers are observed.
- Toss candle live smoke passed, but a multi-symbol scheduler-sized run has not yet been observed across multiple market days.

## Exact Next Step

- exact next step: Run a small scheduler-shaped live candle pilot with `--provider tossinvest --max-requests-per-run 5 --skip-if-fresh`, compare results to existing `market.daily_price_bar`, and decide whether to make Toss the default provider with Twelve Data fallback.
