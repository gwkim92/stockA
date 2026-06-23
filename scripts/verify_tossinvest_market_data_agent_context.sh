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

echo "Verifying Toss market data snapshots, provider comparison, and agent context"
"$PYTHON_BIN" -m unittest \
  tests.test_tossinvest_market_data \
  tests.test_agent_market_context \
  tests.test_tossinvest_order_adapter \
  tests.test_market_price.MarketPriceTests.test_render_market_price_upsert_sql \
  tests.test_market_price.MarketPriceTests.test_load_market_price_sync_result_from_tossinvest_candles_payload

echo "Verifying Toss operating-data profiles and CLI boundaries"
"$PYTHON_BIN" -m unittest \
  tests.test_operating_data_orchestrator \
  tests.test_operating_data_profile_scheduler \
  tests.test_tossinvest_market_data.TossInvestMarketDataTests.test_cli_dry_run_is_secret_free_and_accepts_fixture \
  tests.test_tossinvest_market_data.TossInvestMarketDataTests.test_provider_comparison_cli_dry_run_keeps_canonical_promotion_blocked

echo "Verifying frontend API split for stock candles, data-health, paper, and live readiness"
"$PYTHON_BIN" -m unittest \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_sql_uses_canonical_tables \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_paper_trading_preview_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_trading_readiness_response_matches_frontend_contract_shape

echo "Checking migration and UI references"
if command -v rg >/dev/null 2>&1; then
  SEARCH_BIN=(rg -q)
else
  SEARCH_BIN=(grep -Eq)
fi
"${SEARCH_BIN[@]}" "market\\.tossinvest_daily_candle_snapshot" db/migrations/0034_tossinvest_market_data_agent_context.sql
"${SEARCH_BIN[@]}" "market\\.tossinvest_provider_comparison_snapshot" db/migrations/0034_tossinvest_market_data_agent_context.sql
"${SEARCH_BIN[@]}" "provider text not null default 'unknown'" db/migrations/0034_tossinvest_market_data_agent_context.sql
"${SEARCH_BIN[@]}" "CandlestickChart" apps/web/src/app/stocks/\[symbol\]/page.tsx
"${SEARCH_BIN[@]}" "tossinvest_market_data" apps/web/src/app/data-health/page.tsx

echo "TossInvest market data agent context verification passed"
