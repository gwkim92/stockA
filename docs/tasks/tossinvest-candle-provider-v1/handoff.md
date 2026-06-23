# TossInvest Candle Provider V1 Handoff

## Status

- completed locally: TossInvest read-only candle provider support is implemented and verified.

## Current Decisions

- TossInvest is not fully applied across the service yet.
- The next incremental capability is read-only candle/OHLCV import into the existing market price model.
- Existing providers remain fallback until Toss IP allowlisting and rate-limit stability are proven in EC2.
- Real Toss order submit/modify/cancel remains out of scope.
- Batch market price runs reuse one Toss OAuth token per process run and then call the candle endpoint per symbol.

## Guardrails

- Do not log Toss client secret, access token, account sequence/account number, or Authorization headers.
- Do not call Toss order mutation endpoints.
- Do not change recommendation weights, benchmark definitions, portfolio holdings, or broker order boundary.

## Verification Notes

- passed: `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_source tests.test_market_price`
- passed: `bash scripts/verify_tossinvest_candle_provider.sh`
- passed with repo venv: `PYTHONPATH=src /tmp/stockanalysis-tossinvest-venv/bin/python -m unittest discover -s tests`
- passed: `bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- local `/opt/homebrew/bin/python3.13 -m unittest discover -s tests` without the repo venv failed because `fastapi` is not installed in that interpreter.
- local `python3` points to a Python 3.14 build with a broken `pyexpat` dynamic library; use `/tmp/stockanalysis-tossinvest-venv/bin/python` or `/opt/homebrew/bin/python3.13` for reliable repo verification.

## Residual Risk

- EC2 Toss API access is currently blocked by provider IP allowlisting until `34.206.72.213` is accepted by Toss.
- Production market price scheduler has not been switched to Toss; that should wait until EC2 live Toss candle calls pass and rate-limit headers are observed.

## Exact Next Step

- exact next step: After Toss accepts the EC2 egress IP, run a small EC2 live candle pilot with `--provider tossinvest --max-requests-per-run 5 --skip-if-fresh`, compare results to existing `market.daily_price_bar`, then decide whether to make Toss the default provider with Twelve Data fallback.
