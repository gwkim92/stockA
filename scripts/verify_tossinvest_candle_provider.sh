#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH=src

python3 -m unittest \
  tests.test_tossinvest_source \
  tests.test_market_price.MarketPriceTests.test_load_market_price_sync_result_from_tossinvest_candles_payload \
  tests.test_market_price.MarketPriceTests.test_resolve_market_price_provider_accepts_aliases \
  tests.test_market_price.MarketPriceTests.test_load_market_price_sync_result_uses_tossinvest_candles_endpoint \
  tests.test_market_price.MarketPriceTests.test_run_market_price_batch_upsert_reuses_tossinvest_oauth_token

python3 -m stockanalysis.ingest.cli market-price-upsert --help >/tmp/stockanalysis-tossinvest-candle-cli-help.txt
rg -q "tossinvest" /tmp/stockanalysis-tossinvest-candle-cli-help.txt

echo "tossinvest candle provider verification passed"
