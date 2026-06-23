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
  tests.test_tossinvest_readonly_sync \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_trading_readiness_response_matches_frontend_contract_shape \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_trading_readiness_sql_reads_safety_tables_without_exposing_secrets \
  tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_data_health_sql_uses_operations_cadence_registry

echo "tossinvest remaining readonly endpoints verification passed"
