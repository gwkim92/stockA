# TossInvest Readonly Remaining Endpoints V1 Handoff

## Status

- completed and deployed to EC2: remaining TossInvest read-only endpoint builders, bounded summaries, frontend read-model exposure, and EC2 smoke are implemented and verified.

## Current Decisions

- Remaining Toss endpoints are read-only only.
- New live calls should be folded into the existing manual `tossinvest-readonly-sync-run` before any scheduler activation.
- Full raw orderbook/trades/order history archival is not added in this task; bounded summaries are surfaced through existing read models.
- Order history detail is fetched only for a bounded subset and report output stores status/symbol/side counts, not raw order ids.
- Optional market-data endpoint failures are summarized per symbol and do not fail the core holdings/FX sync.

## Guardrails

- Do not log Toss client secret, access token, account sequence/account number, Authorization header, or full raw order identifiers beyond safe counts/status summaries.
- Do not call Toss order submit, modify, or cancel endpoints.
- Do not change recommendation weights, benchmark definitions, portfolio order flows, or broker submit boundary.

## Verification Notes

- passed: `bash scripts/verify_tossinvest_remaining_readonly_endpoints.sh`
- passed: `bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- passed: `PYTHONPATH=src /tmp/stockanalysis-tossinvest-venv/bin/python -m unittest discover -s tests` (`1255` tests)
- passed on EC2 after `git pull --ff-only origin develop`: `PYTHON_BIN=/opt/stockanalysis/venv/bin/python bash scripts/verify_tossinvest_remaining_readonly_endpoints.sh`
- passed on EC2 after `git pull --ff-only origin develop`: `PYTHON_BIN=/opt/stockanalysis/venv/bin/python bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- passed on EC2 live Toss execute: `tossinvest-readonly-sync-run --env-file /opt/stockanalysis/runtime/data-operations.env --execute`
  - `run_id=7055`
  - `status=succeeded`
  - `market_calendars.KR.status=loaded`
  - `market_calendars.US.status=loaded`
  - `stock_warning_symbol_count=3`
  - `market_microdata_symbol_count=3`
  - `order_history.status=loaded`
  - `order_history.open_order_count=0`
  - `order_history.closed_order_count=20`
  - `order_history.order_detail_loaded_count=5`
  - `broker_submit_allowed=false`
  - `submitted_to_broker=false`
  - `secret_free=true`
- passed on EC2 API smoke:
  - `/api/data-health.data.tossinvest_readonly_sync.latest_run_id=pipeline-run-7055`
  - `/api/trading/readiness.data.tossinvest_order_readiness.latest_run_id=pipeline-run-7055`
  - both payloads expose stock warnings, market microdata, and sanitized order history summaries.
- passed on EC2 route smoke: `http://127.0.0.1:3000/data-health` and `http://127.0.0.1:3000/trading-readiness` returned `200`.
- checked EC2 ports after service restart: `127.0.0.1:3000` and `127.0.0.1:8787` listen locally; `13000` is not listening.

## Residual Risk

- Live Toss rate-limit behavior for a larger holding set still needs observation before scheduler activation.
- Production scheduler and market-data default provider remain unchanged.
- Full raw orderbook/trades/order history archival remains intentionally out of scope; this task exposes bounded read-only summaries only.

## Exact Next Step

- exact next step: If the user wants all Toss market data to replace existing providers, first add a provider comparison/budget pilot that measures rate limits, symbol coverage, freshness, and retry behavior without changing recommendation weights or order boundaries.
