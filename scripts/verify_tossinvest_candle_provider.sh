#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-}"

if [ -z "$PYTHON_BIN" ]; then
  if [ -x /opt/stockanalysis/venv/bin/python ]; then
    PYTHON_BIN="/opt/stockanalysis/venv/bin/python"
  elif [ -x /opt/homebrew/bin/python3.13 ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3.13"
  else
    PYTHON_BIN="python3"
  fi
fi

cd "$ROOT_DIR"

export PYTHONPATH=src

"$PYTHON_BIN" -m unittest \
  tests.test_tossinvest_source \
  tests.test_market_price.MarketPriceTests.test_load_market_price_sync_result_from_tossinvest_candles_payload \
  tests.test_market_price.MarketPriceTests.test_resolve_market_price_provider_accepts_aliases \
  tests.test_market_price.MarketPriceTests.test_load_market_price_sync_result_uses_tossinvest_candles_endpoint \
  tests.test_market_price.MarketPriceTests.test_run_market_price_batch_upsert_reuses_tossinvest_oauth_token

"$PYTHON_BIN" -m stockanalysis.ingest.cli market-price-upsert --help >/tmp/stockanalysis-tossinvest-candle-cli-help.txt
rg -q "tossinvest" /tmp/stockanalysis-tossinvest-candle-cli-help.txt

echo "tossinvest candle provider verification passed"
